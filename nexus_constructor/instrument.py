import os
from typing import List, Dict, Any, Tuple

import h5py
from nexus_constructor.component_type import make_dictionary_of_class_definitions
from nexus_constructor.nexus import nexus_wrapper as nx
from nexus_constructor.component import Component
from nexus_constructor.nexus.nexus_wrapper import get_nx_class
from nexus_constructor.transformations import Transformation
from nexus_constructor.component_factory import create_component

COMPONENTS_IN_ENTRY = ["NXmonitor", "NXsample"]


def _convert_name_with_spaces(component_name):
    return component_name.replace(" ", "_")


def _separate_dot_field_group_hierarchy(
    item_dict: Dict[Any, Any],
    dots_in_field_name: List[str],
    item: Tuple[str, h5py.Group],
):
    previous_group = item_dict
    for subgroup in dots_in_field_name:
        # do not overwrite a group unless it doesn't yet exist
        if subgroup not in previous_group:
            previous_group[subgroup] = dict()
        if subgroup == dots_in_field_name[-1]:
            # set the value of the field to the last item in the list
            previous_group[subgroup] = _handle_stream_dataset(item[1][...])
        previous_group = previous_group[subgroup]


def _handle_stream_dataset(stream_dataset: h5py.Dataset):
    if stream_dataset.dtype == h5py.special_dtype(vlen=str):
        return str(stream_dataset)
    if stream_dataset.dtype == bool:
        return bool(stream_dataset)
    if stream_dataset.dtype == int:
        return int(stream_dataset)


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
                            transform = Transformation(
                                self.nexus, node[transformation_name]
                            )
                            transform.depends_on = transform.depends_on

        self.nexus.nexus_file.visititems(refresh_depends_on)

    def create_component(self, name: str, nx_class: str, description: str) -> Component:
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
        component = Component(self.nexus, component_group)
        component.description = description
        return component

    def remove_component(self, component: Component):
        """
        Removes a component group from the NeXus file and instrument view
        :param component: The component to be removed
        """
        self.nexus.component_removed.emit(component.name)
        self.nexus.delete_node(component.group)

    def get_component_list(self) -> List[Component]:
        component_list = []

        def find_components(_, node):
            if isinstance(node, h5py.Group):
                if "NX_class" in node.attrs.keys():
                    nx_class = get_nx_class(node)
                    if nx_class and nx_class in self.nx_component_classes:
                        component_list.append(create_component(self.nexus, node))

        self.nexus.entry.visititems(find_components)
        return component_list

    def get_streams(self) -> Dict[str, Dict[str, str]]:
        """
        Find all streams and return them in the expected format for JSON serialisiation.
        :return: A dictionary of stream groups, with their respective field names and values.
        """
        streams_dict = dict()

        def find_streams(_, node):
            if isinstance(node, h5py.Group):
                if "NX_class" in node.attrs:
                    if node.attrs["NX_class"] == "NCstream":
                        item_dict = dict()
                        for item in node.items():
                            dots_in_field_name = item[0].split(".")
                            if len(dots_in_field_name) > 1:
                                _separate_dot_field_group_hierarchy(
                                    item_dict, dots_in_field_name, item
                                )
                            else:
                                item_dict[item[0]] = _handle_stream_dataset(
                                    item[1][...]
                                )
                        streams_dict[node.name] = item_dict

        self.nexus.entry.visititems(find_streams)
        return streams_dict

    def get_links(self) -> Dict[str, h5py.Group]:
        links_dict = dict()

        def find_links(_, node):
            if isinstance(node, h5py.Group):
                # visititems does not visit softlinks so we need to do this manually
                for item in node:
                    if isinstance(node.get(item, getlink=True), h5py.SoftLink):
                        links_dict[node[item].name] = node[item]

        self.nexus.entry.visititems(find_links)
        return links_dict
