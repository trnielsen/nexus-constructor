import attr
import h5py
from typing import Any, List
from PySide2.QtGui import QVector3D
from nexus_constructor.pixel_data import PixelData
from nexus_constructor.geometry_types import Geometry
from nexus_constructor.nexus import nexus_wrapper as nx
from nexus_constructor.transformations import (
    Transformation,
    TransformationModel,
    TransformationsList,
)
from nexus_constructor.ui_utils import qvector3d_to_numpy_array


class DependencyError(Exception):
    """
    Raised when trying to carry out an operation which would invalidate the depends_on chain
    """

    pass


def _normalise(input_vector: QVector3D):
    """
    Normalise to unit vector

    :param input_vector: Input vector
    :return: Unit vector, magnitude
    """
    magnitude = input_vector.length()
    if magnitude == 0:
        return QVector3D(0.0, 0.0, 0.0), 0.0

    return input_vector.normalized(), magnitude


def _generate_incremental_name(base_name, group: h5py.Group):
    number = 1
    while f"{base_name}_{number}" in group:
        number += 1
    return f"{base_name}_{number}"


def _transforms_are_equivalent(
    transform_1: TransformationModel, transform_2: TransformationModel
):
    return transform_1.absolute_path == transform_2.absolute_path


class ComponentModel:
    """
    Provides an interface to an existing component group in a NeXus file
    """

    def __init__(self, nexus_file: nx.NexusWrapper, group: h5py.Group):
        self.file = nexus_file
        self.group = group

    @property
    def name(self):
        return nx.get_name_of_node(self.group)

    @name.setter
    def name(self, new_name: str):
        self.file.rename_node(self.group, new_name)

    @property
    def absolute_path(self):
        """
        Get absolute path of the component group in the NeXus file,
        this is guaranteed to be unique so it can be used as an ID for this Component
        :return: absolute path of the transform dataset in the NeXus file,
        """
        return self.group.name

    def get_field(self, name: str):
        return self.file.get_field_value(self.group, name)

    def set_field(self, name: str, value: Any, dtype=None):
        self.file.set_field_value(self.group, name, value, dtype)

    @property
    def nx_class(self):
        return self.file.get_nx_class(self.group)

    @nx_class.setter
    def nx_class(self, nx_class: str):
        self.file.set_nx_class(self.group, nx_class)

    @property
    def description(self):
        return self.file.get_field_value(self.group, "description")

    @description.setter
    def description(self, description: str):
        if description:
            self.file.set_field_value(self.group, "description", description, str)

    @property
    def transforms_full_chain(self) -> TransformationsList:
        """
        Gets all transforms in the depends_on chain for this component
        :return: List of transforms
        """
        transforms = TransformationsList(self)
        depends_on = self.get_field("depends_on")
        self._get_transform(depends_on, transforms)
        return transforms

    def _get_transform(
        self,
        depends_on: str,
        transforms: List[TransformationModel],
        local_only: bool = False,
    ):
        """
        Recursive function, appends each transform in depends_on chain to transforms list
        :param depends_on: The next depends_on string to find the next transformation in the chain
        :param transforms: The list to populate with transformations
        :param local_only: If True then only add transformations which are stored within this component
        """
        if depends_on is not None and depends_on != ".":
            transform_dataset = self.file.nexus_file[depends_on]
            if local_only and transform_dataset.parent.parent.name != self.absolute_path:
                # We're done, the next transformation is not stored in this component
                return
            transforms.append(TransformationModel(self.file, transform_dataset))
            if "depends_on" in transform_dataset.attrs.keys():
                self._get_transform(transform_dataset.attrs["depends_on"], transforms)

    @property
    def transforms(self) -> TransformationsList:
        """
        Gets transforms in the depends_on chain but only those which are local to
        this component's group in the NeXus file
        :return:
        """
        transforms = TransformationsList(self)
        depends_on = self.get_field("depends_on")
        self._get_transform(depends_on, transforms, local_only=True)
        return transforms

    def add_translation(
        self,
        vector: QVector3D,
        name: str = None,
        depends_on: TransformationModel = None,
    ) -> TransformationModel:
        """
        Note, currently assumes translation is in metres
        :param vector: direction and magnitude of translation as a 3D vector
        :param name: name of the translation group (Optional)
        :param depends_on: existing transformation which the new one depends on (otherwise relative to origin)
        """
        transforms_group = self.file.create_transformations_group_if_does_not_exist(
            self.group
        )
        if name is None:
            name = _generate_incremental_name("translation", transforms_group)
        unit_vector, magnitude = _normalise(vector)
        field = self.file.set_field_value(transforms_group, name, magnitude, float)
        self.file.set_attribute_value(field, "units", "m")
        self.file.set_attribute_value(
            field, "vector", qvector3d_to_numpy_array(unit_vector)
        )
        self.file.set_attribute_value(field, "transformation_type", "Translation")

        translation_transform = TransformationModel(self.file, field)
        translation_transform.depends_on = depends_on
        return translation_transform

    def add_rotation(
        self,
        axis: QVector3D,
        angle: float,
        name: str = None,
        depends_on: TransformationModel = None,
    ) -> TransformationModel:
        """
        Note, currently assumes angle is in degrees
        :param axis: axis
        :param angle:
        :param name: Name of the rotation group (Optional)
        :param depends_on: existing transformation which the new one depends on (otherwise relative to origin)
        """
        transforms_group = self.file.create_transformations_group_if_does_not_exist(
            self.group
        )
        if name is None:
            name = _generate_incremental_name("rotation", transforms_group)
        field = self.file.set_field_value(transforms_group, name, angle, float)
        self.file.set_attribute_value(field, "units", "degrees")
        self.file.set_attribute_value(field, "vector", qvector3d_to_numpy_array(axis))
        self.file.set_attribute_value(field, "transformation_type", "Rotation")
        rotation_transform = TransformationModel(self.file, field)
        rotation_transform.depends_on = depends_on
        return rotation_transform

    def _transform_is_in_this_component(self, transform: TransformationModel) -> bool:
        return transform.dataset.parent.parent.name == self.absolute_path

    def remove_transformation(self, transform: TransformationModel):
        if not self._transform_is_in_this_component(transform):
            raise PermissionError(
                "Transform is not in this component, do not have permission to delete"
            )

        dependents = transform.get_dependents()
        if dependents:
            raise DependencyError(f"Cannot delete transformation, it is a dependency of {dependents}")

        # Remove whole transformations group if this is the only transformation in it
        if len(transform.dataset.parent.keys()) == 1:
            self.file.delete_node(transform.dataset.parent)
        # Otherwise just remove the transformation from the group
        else:
            self.file.delete_node(transform.dataset)

    @property
    def depends_on(self):
        depends_on_path = self.file.get_field_value(self.group, "depends_on")
        if depends_on_path is None:
            return None
        return TransformationModel(self.file, self.file.nexus_file[depends_on_path])

    @depends_on.setter
    def depends_on(self, transformation: TransformationModel):
        existing_depends_on = self.file.get_attribute_value(self.group, "depends_on")
        if existing_depends_on is not None:
            TransformationModel(self.file, self.file[existing_depends_on]).deregister_dependent(self)

        if transformation is None:
            self.file.set_field_value(
                self.group, "depends_on", ".", str
            )
        else:
            self.file.set_field_value(
                self.group, "depends_on", transformation.absolute_path, str
            )
            transformation.register_dependent(self)


@attr.s
class Component:
    """DEPRECATED: Switching to use ComponentModel everywhere"""

    nx_class = attr.ib(str)
    name = attr.ib(str)
    description = attr.ib(default="", type=str)
    transform_parent = attr.ib(default=None, type=object)
    dependent_transform = attr.ib(default=None, type=Transformation)
    transforms = attr.ib(factory=list, type=List[Transformation])
    geometry = attr.ib(default=None, type=Geometry)
    pixel_data = attr.ib(default=None, type=PixelData)
