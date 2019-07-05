import h5py

from PySide2.QtCore import Signal, QObject
from typing import Any, TypeVar
import numpy as np

h5Node = TypeVar("h5Node", h5py.Group, h5py.Dataset)


def set_up_in_memory_nexus_file(filename: str):
    """
    Creates an in-memory nexus-file to store the model data in.
    :return: The file object.
    """
    return h5py.File(filename, mode="x", driver="core", backing_store=False)


def append_nxs_extension(file_name: str):
    extension = ".nxs"
    if file_name.endswith(extension):
        return file_name
    else:
        return file_name + extension


def get_name_of_node(node: h5Node):
    return node.name.split("/")[-1]


class NexusWrapper(QObject):
    """
    Contains the NeXus file and functions to add and edit components in the NeXus file structure.
    All changes to the NeXus file should happen via this class. Emits Qt signal whenever anything in the file changes.
    """

    # Signal that indicates the nexus file has been changed in some way
    file_changed = Signal("QVariant")
    component_added = Signal(str, "QVariant")
    show_entries_dialog = Signal("QVariant", "QVariant")

    def __init__(self, filename="NeXus File"):
        super().__init__()
        self.nexus_file = set_up_in_memory_nexus_file(filename)
        self.entry = self.create_nx_group("entry", "NXentry", self.nexus_file)

        self.create_nx_group("sample", "NXsample", self.entry)
        self.instrument = self.create_nx_group("instrument", "NXinstrument", self.entry)

        self._emit_file()

    def _emit_file(self):
        """
        Calls the file_changed signal with the updated file object when the structure is changed.
        :return: None
        """
        self.file_changed.emit(self.nexus_file)

    def save_file(self, filename):
        """
        Saves the in-memory NeXus file to a physical file if the filename is valid.
        :param filename: Absolute file path to the file to save.
        :return: None
        """
        if filename:
            print(filename)
            file = h5py.File(append_nxs_extension(filename), mode="x")
            try:
                file.copy(source=self.nexus_file["/entry/"], dest="/entry/")
                print("Saved to NeXus file")
            except ValueError as e:
                print(f"File writing failed: {e}")

    def open_file(self, filename):
        """
        Opens a physical file into memory and sets the model to use it.
        :param filename: Absolute file path to the file to open.
        :return:
        """
        if filename:
            nexus_file = h5py.File(
                filename, mode="r", backing_store=False, driver="core"
            )

            self.find_entries_in_file(nexus_file)

    def find_entries_in_file(self, nexus_file: h5py.File):
        """
        Find the entry group in the specified nexus file. If there are multiple, emit the signal required to show the multiple entry selection dialog in the UI.
        :param nexus_file: A reference to the nexus file to check for the entry group.
        """
        entries_in_root = dict()

        def append_nx_entries_to_list(name, node):
            if isinstance(node, h5py.Group):
                if "NX_class" in node.attrs.keys():
                    if (
                        node.attrs["NX_class"] == b"NXentry"
                        or node.attrs["NX_class"] == "NXentry"
                    ):
                        entries_in_root[name] = node

        nexus_file["/"].visititems(append_nx_entries_to_list)
        if len(entries_in_root.keys()) > 1:
            self.show_entries_dialog.emit(entries_in_root, nexus_file)
        else:
            self.load_file(list(entries_in_root.values())[0], nexus_file)

    def load_file(self, entry: h5py.Group, nexus_file: h5py.File):
        """
        Sets the entry group, instrument group and reference to the nexus file.
        :param entry: The entry group.
        :param nexus_file: The nexus file reference.
        """
        self.entry = entry
        self.instrument = self.get_instrument_group_from_entry(self.entry)
        self.nexus_file = nexus_file

        print("NeXus file loaded")
        self._emit_file()

    def rename_node(self, node: h5Node, new_name: str):
        self.nexus_file.move(node.name, f"{node.parent.name}/{new_name}")
        self._emit_file()

    def delete_node(self, node: h5Node):
        del self.nexus_file[node.name]
        self._emit_file()

    def create_nx_group(self, name, nx_class, parent):
        """
        Given a name, an nx class and a parent group, create a group under the parent
        :param name: The name of the group to be created.
        :param nx_class: The NX_class attribute to be set.
        :param parent: The parent HDF group to add the created group to.
        :return: A reference to the created group in the in-memory NeXus file.
        """
        group = parent.create_group(name)
        group.attrs["NX_class"] = nx_class
        self._emit_file()
        return group

    @staticmethod
    def get_nx_class(group: h5py.Group):
        if "NX_class" not in group.attrs.keys():
            return None
        return group.attrs["NX_class"]

    def set_nx_class(self, group: h5py.Group, nx_class: str):
        group.attrs["NX_class"] = nx_class
        self._emit_file()

    @staticmethod
    def get_field_value(group: h5py.Group, name: str):
        if name not in group:
            return None
        value = group[name][...]
        if value.dtype.type is np.string_:
            value = str(value, "utf8")
        return value

    def set_field_value(self, group: h5py.Group, name: str, value: Any, dtype=None):
        """
        Create or update the value of a field (dataset in hdf terminology)
        :param group: Parent group of the field
        :param name: Name of the field
        :param value: Value fo the field
        :param dtype: Type of the value (Use numpy types)
        :return: The dataset
        """
        if dtype is str:
            dtype = f"|S{len(value)}"
            value = np.array(value).astype(dtype)

        if name in group:
            if dtype is None or group[name].dtype == dtype:
                group[name][...] = value
            else:
                del group[name]
                group.create_dataset(name, data=value, dtype=dtype)
        else:
            group.create_dataset(name, data=value, dtype=dtype)
        self._emit_file()
        return group[name]

    @staticmethod
    def get_attribute_value(node: h5Node, name: str):
        if name in node.attrs.keys():
            return node.attrs[name]

    def set_attribute_value(self, node: h5Node, name: str, value: Any):
        # Deal with arrays of strings
        if isinstance(value, np.ndarray):
            if value.dtype.type is np.str_ and value.size == 1:
                value = str(value[0])
            elif value.dtype.type is np.str_ and value.size > 1:
                node.attrs.create(
                    name, value, (len(value),), h5py.special_dtype(vlen=str)
                )
                for index, item in enumerate(value):
                    node.attrs[name][index] = item.encode("utf-8")
                self._emit_file()
                return

        node.attrs[name] = value
        self._emit_file()

    def delete_attribute(self, node: h5Node, name: str):
        if name in node.attrs.keys():
            del node.attrs[name]
        self._emit_file()

    def create_transformations_group_if_does_not_exist(self, parent_group: h5Node):
        for child in parent_group:
            if "NX_class" in parent_group[child].attrs.keys():
                if parent_group[child].attrs["NX_class"] == "NXtransformations":
                    return parent_group[child]
        return self.create_nx_group(
            "transformations", "NXtransformations", parent_group
        )

    @staticmethod
    def get_instrument_group_from_entry(entry: h5py.Group) -> h5py.Group:
        """
        Get the first NXinstrument object from an entry group.
        :param entry: The entry group object to search for the instrument group in.
        :return: the instrument group object.
        """
        for node in entry.values():
            if isinstance(node, h5py.Group):
                if "NX_class" in node.attrs.keys():
                    if node.attrs["NX_class"] == "NXinstrument":
                        return node