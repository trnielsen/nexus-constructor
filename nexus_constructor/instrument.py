import os
import h5py
from nexus_constructor.component_type import make_dictionary_of_class_definitions
from nexus_constructor.nexus import nexus_wrapper as nx
from nexus_constructor.component import ComponentModel
from nexus_constructor.transformations import TransformationModel

COMPONENTS_IN_ENTRY = ["NXmonitor", "NXsample"]


def _convert_name_with_spaces(component_name):
    return component_name.replace(" ", "_")


class Instrument:
    """
    This is the high level container for all application data,
    as much as possible lives in the in memory NeXus file which this class holds (via NexusWrapper)

    Existance of this class, rather than putting all this functionality in NexusWrapper avoids circular dependencies,
    for example between component and NexusWrapper
    """

    def __init__(self, nexus_file: nx.NexusWrapper):
        self.nexus = nexus_file
        _, self.nx_component_classes = make_dictionary_of_class_definitions(
            os.path.abspath(
                os.path.join(
                    os.path.realpath(__file__), os.pardir, os.pardir, "definitions"
                )
            )
        )
        self._generate_transform_dependency_lists()

    def _generate_transform_dependency_lists(self):
        """
        We keep track of what transformations a transformation is a dependency of
        so that we can avoid deleting transformations if anything else still depends on them.
        There is no attribute for this in the NeXus standard, so we cannot rely on it being in the file we have loaded.
        This method allows us to generate the attributes.
        """

        def refresh_depends_on(_, node):
            """
            Refresh the depends_on attribute of each transformation, which also results in registering dependents
            """
            if isinstance(node, h5py.Group):
                if "NX_class" in node.attrs.keys():
                    if node.attrs["NX_class"] == "NXtransformations":
                        for transformation_name in node:
                            transform = TransformationModel(
                                self.nexus, node[transformation_name]
                            )
                            transform.depends_on = transform.depends_on

        self.nexus.nexus_file.visititems(refresh_depends_on)

    def add_component(self, name: str, nx_class: str, description: str):
        """
        Creates a component group in a NeXus file
        :param name: Name of the component group to create
        :param nx_class: NX_class of the component group to create
        :param description: Description of the component
        :return Wrapper for added component
        """
        name = _convert_name_with_spaces(name)
        parent_group = self.nexus.instrument
        if nx_class in COMPONENTS_IN_ENTRY:
            parent_group = self.nexus.entry
        component_group = self.nexus.create_nx_group(name, nx_class, parent_group)
        component = ComponentModel(self.nexus, component_group)
        component.description = description
        return component

    def remove_component(self, component: ComponentModel):
        """
        Removes a component group from the NeXus file
        :param component: The component to be removed
        """
        self.nexus.delete_node(component.group)

    def get_component_list(self):
        component_list = []

        def find_components(_, node):
            if isinstance(node, h5py.Group):
                if "NX_class" in node.attrs.keys():
                    if node.attrs["NX_class"] in self.nx_component_classes:
                        component_list.append(ComponentModel(self.nexus, node))

        self.nexus.nexus_file.visititems(find_components)
        return component_list