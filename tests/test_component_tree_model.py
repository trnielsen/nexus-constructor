from nexus_constructor.component_tree_model import (
    ComponentTreeModel,
    ComponentInfo,
    LinkTransformation
)
from nexus_constructor.component import ComponentModel
import pytest
from PySide2.QtCore import QModelIndex
from nexus_constructor.nexus.nexus_wrapper import NexusWrapper
from typing import Any
from uuid import uuid1
from PySide2.QtGui import QVector3D


def _add_component_to_file(
    nexus_wrapper: NexusWrapper,
    field_name: str,
    field_value: Any,
    component_name: str = "test_component",
):
    component_group = nexus_wrapper.nexus_file.create_group(component_name)
    component_group.create_dataset(field_name, data=field_value)
    return component_group


class FakeInstrument(list):
    def __init__(self, component_list=[]):
        super().__init__()
        for current in component_list:
            self.append(current)

    def get_component_list(self):
        return self


def get_component():
    nexus_wrapper = NexusWrapper(str(uuid1()))
    component_group = _add_component_to_file(
        nexus_wrapper, "some_field", 42, "component_name"
    )
    return ComponentModel(nexus_wrapper, component_group)


def test_number_of_components_0():
    data_under_test = FakeInstrument()
    under_test = ComponentTreeModel(data_under_test)
    test_index = QModelIndex()
    assert under_test.rowCount(test_index) == 0


def test_number_of_components_1():
    data_under_test = FakeInstrument([get_component()])
    under_test = ComponentTreeModel(data_under_test)

    test_index = QModelIndex()

    assert under_test.rowCount(test_index) == 1


def test_number_of_components_2():
    data_under_test = FakeInstrument([get_component(), get_component()])
    under_test = ComponentTreeModel(data_under_test)

    test_index = QModelIndex()

    assert under_test.rowCount(test_index) == 2


def test_component_has_2_rows():
    data_under_test = FakeInstrument([get_component()])
    under_test = ComponentTreeModel(data_under_test)

    test_index = under_test.createIndex(0, 0, data_under_test[0])

    assert under_test.rowCount(test_index) == 2


def test_transformation_list_has_0_rows():
    data_under_test = FakeInstrument([get_component()])
    under_test = ComponentTreeModel(data_under_test)

    data_under_test[0].stored_transforms = data_under_test[0].transforms

    test_index = under_test.createIndex(0, 0, data_under_test[0].stored_transforms)

    assert under_test.rowCount(test_index) == 0


def test_transformation_list_has_1_rows():
    component = get_component()
    translation = component.add_translation(QVector3D(1.0, 0.0, 0.0))
    component.depends_on = translation
    data_under_test = FakeInstrument([component])
    component.stored_transforms = component.transforms
    under_test = ComponentTreeModel(data_under_test)

    test_index = under_test.createIndex(0, 0, component.stored_transforms)

    assert under_test.rowCount(test_index) == 1


def test_transformation_has_0_rows():
    component = get_component()
    translation = component.add_translation(QVector3D(1.0, 0.0, 0.0))
    component.depends_on = translation
    data_under_test = FakeInstrument([component])
    component.stored_transforms = component.transforms
    under_test = ComponentTreeModel(data_under_test)

    test_index = under_test.createIndex(0, 0, component.stored_transforms[0])

    assert under_test.rowCount(test_index) == 0

def test_transformation_link_has_0_rows():
    component = get_component()
    translation = component.add_translation(QVector3D(1.0, 0.0, 0.0))
    component.depends_on = translation
    data_under_test = FakeInstrument([component])
    component.stored_transforms = component.transforms
    under_test = ComponentTreeModel(data_under_test)

    test_index = under_test.createIndex(0, 0, component.stored_transforms[0])

    assert under_test.rowCount(test_index) == 0


def test_rowCount_gets_unknown_type():
    data_under_test = FakeInstrument()
    under_test = ComponentTreeModel(data_under_test)

    test_index = under_test.createIndex(0, 0, {})

    with pytest.raises(RuntimeError):
        under_test.rowCount(test_index)


def test_get_default_parent():
    data_under_test = FakeInstrument()
    under_test = ComponentTreeModel(data_under_test)

    test_index = QModelIndex()

    assert under_test.parent(test_index) == QModelIndex()

def test_get_component_parent():
    data_under_test = FakeInstrument([get_component()])
    under_test = ComponentTreeModel(data_under_test)

    test_index = under_test.createIndex(0, 0, data_under_test[0])

    assert under_test.parent(test_index) == QModelIndex()


def test_get_transform_list_parent():
    data_under_test = FakeInstrument([get_component()])
    under_test = ComponentTreeModel(data_under_test)

    data_under_test[0].stored_transforms = data_under_test[0].transforms

    test_index = under_test.createIndex(0, 0, data_under_test[0].stored_transforms)

    temp_parent = under_test.parent(test_index)

    assert temp_parent.internalPointer() is data_under_test[0]
    assert temp_parent.row() == 0


def test_get_transform_list_parent_v2():
    data_under_test = FakeInstrument([get_component(), get_component()])
    data_under_test[0].stored_transforms = data_under_test[0].transforms
    data_under_test[1].stored_transforms = data_under_test[1].transforms
    data_under_test[1].name = "Some other name"
    under_test = ComponentTreeModel(data_under_test)

    test_index = under_test.createIndex(0, 0, data_under_test[1].stored_transforms)

    temp_parent = under_test.parent(test_index)

    assert temp_parent.internalPointer() is data_under_test[1]
    assert temp_parent.row() == 1


def test_get_component_info_parent():
    data_under_test = FakeInstrument([get_component()])
    under_test = ComponentTreeModel(data_under_test)

    # Creating ComponentInfo in-line causes a segmentation error
    temp_component_info = ComponentInfo(parent=data_under_test[0])
    test_index = under_test.createIndex(0, 0, temp_component_info)

    assert under_test.parent(test_index).internalPointer() is data_under_test[0]


def test_get_transformation_parent():
    component = get_component()
    translation = component.add_translation(QVector3D(1.0, 0.0, 0.0))
    component.depends_on = translation
    data_under_test = FakeInstrument([component])
    component.stored_transforms = component.transforms
    translation.parent = component.stored_transforms

    under_test = ComponentTreeModel(data_under_test)

    test_index = under_test.createIndex(0, 0, translation)

    found_parent = under_test.parent(test_index)
    assert found_parent.internalPointer() == data_under_test[0].stored_transforms
    assert found_parent.row() == 1

def test_get_transformation_link_parent():
    component = get_component()
    data_under_test = FakeInstrument([component])
    component.stored_transforms = component.transforms
    transform_link = LinkTransformation(component.stored_transforms)
    component.stored_transforms.link = transform_link
    component.stored_transforms.has_link = True

    under_test = ComponentTreeModel(data_under_test)

    test_index = under_test.createIndex(0, 0, transform_link)

    found_parent = under_test.parent(test_index)
    assert found_parent.internalPointer() == data_under_test[0].stored_transforms
    assert found_parent.row() == 1


def test_get_invalid_index():
    data_under_test = FakeInstrument([get_component()])
    under_test = ComponentTreeModel(data_under_test)

    test_index = QModelIndex()

    assert under_test.index(2, 0, test_index) == QModelIndex()
