from nexus_constructor.component_tree_model import ComponentTreeModel, ComponentInfo
from nexus_constructor.component import Component
from nexus_constructor.transformations import Translation
import pytest
from PySide2.QtCore import QModelIndex

def get_component():
    return Component(nx_class="NXsomething",
            name="None",
            description="")

def test_number_of_components_0():
    data_under_test = []
    under_test = ComponentTreeModel(data_under_test)
    test_index = QModelIndex()
    assert under_test.rowCount(test_index) == 0

def test_number_of_components_1():
    data_under_test = [get_component(), ]
    under_test = ComponentTreeModel(data_under_test)

    test_index = QModelIndex()

    assert under_test.rowCount(test_index) == 1

def test_number_of_components_2():
    data_under_test = [get_component(), get_component()]
    under_test = ComponentTreeModel(data_under_test)

    test_index = QModelIndex()

    assert under_test.rowCount(test_index) == 2


def test_component_has_3_rows():
    data_under_test = [get_component(),]
    under_test = ComponentTreeModel(data_under_test)

    test_index = under_test.createIndex(0, 0, data_under_test[0])

    assert under_test.rowCount(test_index) == 2

def test_transformation_list_has_0_rows():
    data_under_test = [get_component(),]
    under_test = ComponentTreeModel(data_under_test)

    test_index = under_test.createIndex(0, 0, data_under_test[0].transforms)

    assert under_test.rowCount(test_index) == 0

def test_transformation_list_has_1_rows():
    data_under_test = [get_component(),]
    data_under_test[0].transforms.append(Translation(parent=data_under_test[0], name = "Some name"))
    under_test = ComponentTreeModel(data_under_test)

    test_index = under_test.createIndex(0, 0, data_under_test[0].transforms)

    assert under_test.rowCount(test_index) == 1

def test_transformation_has_0_rows():
    data_under_test = [get_component(),]
    data_under_test[0].transforms.append(Translation(parent=data_under_test[0], name = "Some name"))
    under_test = ComponentTreeModel(data_under_test)

    test_index = under_test.createIndex(0, 0, data_under_test[0].transforms[0])

    assert under_test.rowCount(test_index) == 0

def test_rowCount_gets_unknown_type():
    data_under_test = []
    under_test = ComponentTreeModel(data_under_test)

    test_index = under_test.createIndex(0, 0, {})

    with pytest.raises(RuntimeError):
        under_test.rowCount(test_index)

def test_get_default_parent():
    data_under_test = []
    under_test = ComponentTreeModel(data_under_test)

    test_index = QModelIndex()

    assert under_test.parent(test_index) == QModelIndex()

def test_get_component_parent():
    data_under_test = [get_component(),]
    under_test = ComponentTreeModel(data_under_test)

    test_index = under_test.createIndex(0, 0, data_under_test[0])

    assert under_test.parent(test_index) == QModelIndex()

def test_get_transform_list_parent():
    data_under_test = [get_component(),]
    under_test = ComponentTreeModel(data_under_test)

    test_index = under_test.createIndex(0, 0, data_under_test[0].transforms)

    temp_parent = under_test.parent(test_index)

    assert temp_parent.internalPointer() is data_under_test[0]
    assert temp_parent.row() == 0

def test_get_transform_list_parent_v2():
    data_under_test = [get_component(), get_component()]
    data_under_test[1].name = "Some other name"
    under_test = ComponentTreeModel(data_under_test)

    test_index = under_test.createIndex(0, 0, data_under_test[1].transforms)

    temp_parent = under_test.parent(test_index)

    assert temp_parent.internalPointer() is data_under_test[1]
    assert temp_parent.row() == 1

def test_get_component_info_parent():
    data_under_test = [get_component(),]
    under_test = ComponentTreeModel(data_under_test)

    # Creating ComponentInfo in-line causes a segmentation error
    temp_component_info = ComponentInfo(parent = data_under_test[0])
    test_index = under_test.createIndex(0, 0, temp_component_info)

    assert under_test.parent(test_index).internalPointer() is data_under_test[0]

def test_get_transformation_parent():
    data_under_test = [get_component(),]
    under_test = ComponentTreeModel(data_under_test)
    test_translation = Translation(parent=data_under_test[0].transforms, name="Some name")
    data_under_test[0].transforms.append(test_translation)

    test_index = under_test.createIndex(0, 0, test_translation)

    found_parent = under_test.parent(test_index)
    assert found_parent.internalPointer() == data_under_test[0].transforms
    assert found_parent.row() == 1

def test_get_invalid_index():
    data_under_test = [get_component(), ]
    under_test = ComponentTreeModel(data_under_test)

    test_index = QModelIndex()

    assert under_test.index(2, 0, test_index) ==  QModelIndex()

# def test_get_component_index():
#     data_under_test = [get_component(), ]
#     under_test = ComponentTreeModel(data_under_test)
#
#     temp_index = under_test.createIndex(0, 0, data_under_test)
#
#     assert under_test.index(0, 0, temp_index).internalPointer() is data_under_test[0]
