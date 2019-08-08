import os

import PySide2
import pytest
import pytestqt
from PySide2.QtCore import Qt
from PySide2.QtGui import QVector3D
from PySide2.QtWidgets import QDialog
from PySide2.QtWidgets import QRadioButton, QMainWindow
from mock import patch, mock_open, call, Mock
from pytestqt.qtbot import QtBot

from nexus_constructor import component_type
from nexus_constructor.add_component_window import AddComponentDialog
from nexus_constructor.component_tree_model import ComponentTreeModel
from nexus_constructor.geometry import OFFGeometryNoNexus
from nexus_constructor.instrument import Instrument
from nexus_constructor.main_window import MainWindow
from nexus_constructor.nexus.nexus_wrapper import NexusWrapper
from nexus_constructor.pixel_options import PixelOptions
from nexus_constructor.validators import FieldType, PixelValidator
from tests.ui_tests.ui_test_utils import (
    systematic_button_press,
    show_and_close_window,
    RED_LINE_EDIT_STYLE_SHEET,
    WHITE_LINE_EDIT_STYLE_SHEET,
    show_window_and_wait_for_interaction,
    VALID_CUBE_OFF_FILE,
    VALID_OCTA_OFF_FILE,
)

MISMATCHING_PIXEL_GRID_VALUES = [("0", "5.3"), ("1", "")]

WRONG_EXTENSION_FILE_PATH = os.path.join(os.getcwd(), "requirements.txt")
NONEXISTENT_FILE_PATH = "doesntexist.off"
VALID_CUBE_MESH_FILE_PATH = os.path.join(os.getcwd(), "tests", "cube.off")
VALID_OCTA_MESH_FILE_PATH = os.path.join(os.getcwd(), "tests", "octa.off")

nexus_wrapper_count = 0

UNIQUE_COMPONENT_NAME = "AUniqueName"
NONUNIQUE_COMPONENT_NAME = "sample"
VALID_UNITS = "km"
INVALID_UNITS = "abc"


instrument = Instrument(NexusWrapper("pixels"))
component = ComponentTreeModel(instrument)
add_component_dialog = AddComponentDialog(instrument, component)
ALL_COMPONENT_TYPES = [
    (comp_type, i)
    for i, comp_type in enumerate(
        list(add_component_dialog.nx_component_classes.keys())
    )
][::-1]
PIXEL_OPTIONS = [
    comp_with_index
    for comp_with_index in ALL_COMPONENT_TYPES
    if comp_with_index[0] in component_type.PIXEL_COMPONENT_TYPES
]
NO_PIXEL_OPTIONS = [
    comp_with_index
    for comp_with_index in ALL_COMPONENT_TYPES
    if comp_with_index[0] not in component_type.PIXEL_COMPONENT_TYPES
]
SHAPE_TYPE_BUTTONS = ["No Shape", "Mesh", "Cylinder"]


@pytest.fixture(scope="function")
def template(qtbot):
    template = QDialog()
    return template


@pytest.fixture(scope="function")
def mock_pixel_options(dialog):

    pixel_options = Mock(spec=PixelOptions)

    def change_mapping_filename(filename):
        pixel_options.get_current_mapping_filename = Mock(return_value=filename)

    pixel_options.populate_pixel_mapping_list_with_mesh = Mock(
        side_effect=change_mapping_filename
    )

    change_mapping_filename(None)

    dialog.pixel_options = pixel_options
    return pixel_options


@pytest.fixture(scope="function")
def dialog(qtbot, template):

    dialog = create_add_component_dialog()
    template.ui = dialog
    template.ui.setupUi(template)
    qtbot.addWidget(template)

    return dialog


@pytest.fixture(scope="function")
def mock_pixel_validator(dialog, mock_pixel_options):
    pixel_validator = Mock(spec=PixelValidator)
    pixel_validator.unacceptable_pixel_states = Mock(return_value=[])

    dialog.ok_validator.pixel_validator = pixel_validator
    mock_pixel_options.pixel_validator = pixel_validator
    mock_pixel_options.get_validator = Mock(return_value=pixel_validator)

    return pixel_validator


def create_add_component_template(qtbot: pytestqt.qtbot.QtBot):
    """
    Creates a template Add Component Dialog and sets this up for testing.
    :param qtbot: The qtbot testing tool.
    :return: The AddComponentDialog object and the template that contains it.
    """
    template = QDialog()
    dialog = create_add_component_dialog()
    template.ui = dialog
    template.ui.setupUi(template)
    qtbot.addWidget(template)
    return dialog, template


def create_add_component_dialog():
    """
    Creates an AddComponentDialog object for use in a testing template.
    :return: An instance of an AddComponentDialog object.
    """
    global nexus_wrapper_count
    nexus_name = "test" + str(nexus_wrapper_count)
    instrument = Instrument(NexusWrapper(nexus_name))
    component = ComponentTreeModel(instrument)
    nexus_wrapper_count += 1
    return AddComponentDialog(instrument, component)


@pytest.mark.skip(reason="This test causes seg faults at the moment.")
def test_UI_GIVEN_nothing_WHEN_clicking_add_component_button_THEN_add_component_window_is_shown(
    qtbot
):

    template = QMainWindow()
    window = MainWindow(Instrument(NexusWrapper("test")))
    template.ui = window
    template.ui.setupUi(template)

    qtbot.addWidget(template)

    show_and_close_window(qtbot, template)

    qtbot.mouseClick(
        window.component_tool_bar.widgetForAction(window.new_component_action),
        Qt.LeftButton,
    )

    assert window.add_component_window.isVisible()

    window.add_component_window.close()


def test_UI_GIVEN_no_shape_WHEN_selecting_shape_type_THEN_shape_options_are_hidden(
    qtbot, template, dialog
):
    systematic_button_press(qtbot, template, dialog.noShapeRadioButton)
    assert not dialog.shapeOptionsBox.isVisible()


@pytest.mark.parametrize("shape_button_name", SHAPE_TYPE_BUTTONS)
def test_UI_GIVEN_nothing_WHEN_changing_component_shape_type_THEN_add_component_button_is_always_disabled(
    qtbot, template, dialog, shape_button_name
):
    systematic_button_press(
        qtbot, template, get_shape_type_button(dialog, shape_button_name)
    )

    show_window_and_wait_for_interaction(qtbot, template)

    assert not dialog.buttonBox.isEnabled()


def test_UI_GIVEN_nothong_WHEN_selecting_cylinder_type_THEN_relevant_fields_are_shown(
    qtbot, template, dialog
):
    # Click on the cylinder shape button
    systematic_button_press(qtbot, template, dialog.CylinderRadioButton)

    # Check that this has caused the relevant fields to become visible
    assert dialog.shapeOptionsBox.isVisible()
    assert dialog.cylinderOptionsBox.isVisible()
    assert dialog.unitsbox.isVisible()

    # Check that the file input isn't visible as this is only available for the mesh
    assert not dialog.geometryFileBox.isVisible()
    # Check that the pixel grid options aren't visible as this is only available for certain NXclasses
    assert not dialog.pixelOptionsWidget.isVisible()


def test_UI_GIVEN_nothing_WHEN_selecting_mesh_shape_THEN_relevant_fields_are_shown(
    qtbot, template, dialog
):
    # Click on the mesh shape button
    systematic_button_press(qtbot, template, dialog.meshRadioButton)

    # Check that this has caused the relevant fields to become visible
    assert dialog.shapeOptionsBox.isVisible()
    assert dialog.unitsbox.isVisible()
    assert dialog.geometryFileBox.isVisible()

    # Check that the cylinder options aren't visible
    assert not dialog.cylinderOptionsBox.isVisible()
    # Check that the pixel grid options aren't visible as this is only available for certain NXclasses
    assert not dialog.pixelOptionsWidget.isVisible()


@pytest.mark.parametrize("shape_with_units", SHAPE_TYPE_BUTTONS[1:])
def test_UI_GIVEN_nothing_WHEN_selecting_shape_with_units_THEN_default_units_are_metres(
    qtbot, template, dialog, shape_with_units
):
    # Click on the button of a shape type with units
    systematic_button_press(
        qtbot, template, get_shape_type_button(dialog, shape_with_units)
    )

    # Check that the units line edit is visible and has metres by default
    assert dialog.unitsLineEdit.isVisible()
    assert dialog.unitsLineEdit.text() == "m"


@pytest.mark.parametrize("pixel_class, pixel_index", PIXEL_OPTIONS)
@pytest.mark.parametrize("any_component_type", ALL_COMPONENT_TYPES)
@pytest.mark.parametrize("pixel_shape_name", SHAPE_TYPE_BUTTONS[1:])
def test_UI_GIVEN_class_and_shape_with_pixel_fields_WHEN_adding_component_THEN_pixel_options_go_from_invisible_to_visible(
    qtbot,
    template,
    dialog,
    pixel_class,
    pixel_index,
    any_component_type,
    pixel_shape_name,
):
    # Change the pixel options to visible by selecting a cylinder/mesh shape and a NXclass with pixel fields
    make_pixel_options_appear(
        qtbot,
        get_shape_type_button(dialog, pixel_shape_name),
        dialog,
        template,
        pixel_index,
    )
    # Check that this has caused the pixel options to become visible
    assert dialog.pixelOptionsWidget.isVisible()


@pytest.mark.parametrize("any_component_type", ALL_COMPONENT_TYPES)
def test_UI_GIVEN_any_nxclass_WHEN_adding_component_with_no_shape_THEN_pixel_options_go_from_visible_to_invisible(
    qtbot, template, dialog, any_component_type
):
    make_pixel_options_visible(dialog, qtbot, template, dialog.meshRadioButton)

    # Change the pixel options to invisible
    make_pixel_options_disappear(qtbot, dialog, template, any_component_type[1])
    assert not dialog.pixelOptionsWidget.isVisible()


@pytest.mark.parametrize("no_pixel_options", NO_PIXEL_OPTIONS)
@pytest.mark.parametrize("pixel_options", PIXEL_OPTIONS)
@pytest.mark.parametrize("shape_name", SHAPE_TYPE_BUTTONS[1:])
def test_UI_GIVEN_class_without_pixel_fields_WHEN_selecting_nxclass_for_component_with_mesh_or_cylinder_shape_THEN_pixel_options_becomes_invisible(
    qtbot, template, dialog, no_pixel_options, pixel_options, shape_name
):
    # Make the pixel options become visible
    make_pixel_options_appear(
        qtbot,
        get_shape_type_button(dialog, shape_name),
        dialog,
        template,
        pixel_options[1],
    )
    assert dialog.pixelOptionsWidget.isVisible()

    # Change nxclass to one without pixel fields and check that the pixel options have become invisible again
    dialog.componentTypeComboBox.setCurrentIndex(no_pixel_options[1])
    assert not dialog.pixelOptionsWidget.isVisible()


def test_UI_GIVEN_cylinder_shape_WHEN_user_chooses_pixel_mapping_THEN_pixel_mapping_list_is_generated(
    qtbot, template, dialog, mock_pixel_options
):

    make_pixel_options_visible(dialog, qtbot, template, dialog.CylinderRadioButton)

    enter_file_path(
        qtbot, dialog, template, VALID_CUBE_MESH_FILE_PATH, VALID_CUBE_OFF_FILE
    )

    mock_pixel_options.populate_pixel_mapping_list_with_cylinder_number.assert_called_once_with(
        1
    )


def test_UI_GIVEN_increasing_cylinder_count_WHEN_user_chooses_pixel_mapping_THEN_pixel_mapping_list_is_generated(
    qtbot, template, dialog, mock_pixel_options
):

    make_pixel_options_visible(dialog, qtbot, template, dialog.CylinderRadioButton)

    cylinder_count = 4
    calls = []

    for i in range(2, cylinder_count):
        qtbot.keyClick(dialog.cylinderCountSpinBox, Qt.Key_Up)
        calls.append(call(i))

    mock_pixel_options.populate_pixel_mapping_list_with_cylinder_number.assert_has_calls(
        calls
    )


def test_UI_GIVEN_same_mesh_file_twice_WHEN_user_selects_file_THEN_mapping_list_remains_the_same(
    qtbot, template, dialog, mock_pixel_options
):

    make_pixel_options_visible(dialog, qtbot, template, dialog.meshRadioButton)

    enter_file_path(
        qtbot, dialog, template, VALID_CUBE_MESH_FILE_PATH, VALID_CUBE_OFF_FILE
    )

    # Provide the same file as before
    enter_file_path(
        qtbot, dialog, template, VALID_CUBE_MESH_FILE_PATH, VALID_CUBE_OFF_FILE
    )

    # Check that the method for populating the pixel mapping was only called once even though a file was selected twice
    mock_pixel_options.populate_pixel_mapping_list_with_mesh.assert_called_once_with(
        VALID_CUBE_MESH_FILE_PATH
    )


def test_UI_GIVEN_pixel_options_are_not_visible_WHEN_giving_mesh_file_THEN_mapping_list_is_not_generated(
    qtbot, template, dialog, mock_pixel_options
):

    systematic_button_press(qtbot, template, dialog.meshRadioButton)

    enter_file_path(
        qtbot, dialog, template, VALID_CUBE_MESH_FILE_PATH, VALID_CUBE_OFF_FILE
    )

    mock_pixel_options.populate_pixel_mapping_list_with_mesh.assert_not_called()


def test_UI_GIVEN_pixel_options_are_not_visible_WHEN_changing_cylinder_count_THEN_mapping_list_is_not_generated(
    qtbot, template, dialog, mock_pixel_options
):

    systematic_button_press(qtbot, template, dialog.CylinderRadioButton)

    qtbot.keyClick(dialog.cylinderCountSpinBox, Qt.Key_Up)

    mock_pixel_options.populate_pixel_mapping_list_with_cylinder_number.assert_not_called()


def test_UI_GIVEN_invalid_file_WHEN_giving_mesh_file_THEN_mapping_list_is_not_generated(
    qtbot, template, dialog, mock_pixel_options
):

    make_pixel_options_visible(dialog, qtbot, template, dialog.meshRadioButton)

    enter_file_path(qtbot, dialog, template, VALID_CUBE_OFF_FILE, "OFF")

    mock_pixel_options.populate_pixel_mapping_list_with_mesh.assert_not_called()


def make_pixel_options_visible(dialog, qtbot, template, button):
    systematic_button_press(qtbot, template, button)
    dialog.componentTypeComboBox.setCurrentIndex(PIXEL_OPTIONS[0][1])


def test_UI_GIVEN_different_mesh_file_WHEN_user_selects_face_mapped_mesh_THEN_mapping_list_changes(
    qtbot, template, dialog, mock_pixel_options
):
    make_pixel_options_visible(dialog, qtbot, template, dialog.meshRadioButton)

    # Provide a path and file for a cube mesh
    enter_file_path(
        qtbot, dialog, template, VALID_CUBE_MESH_FILE_PATH, VALID_CUBE_OFF_FILE
    )

    # Provide a path and file for an octahedron mesh
    enter_file_path(
        qtbot, dialog, template, VALID_OCTA_MESH_FILE_PATH, VALID_OCTA_OFF_FILE
    )

    # Check that two different files being given means the method was called twice
    mock_pixel_options.populate_pixel_mapping_list_with_mesh.assert_has_calls(
        [call(VALID_CUBE_MESH_FILE_PATH), call(VALID_OCTA_MESH_FILE_PATH)]
    )


def test_UI_GIVEN_valid_name_WHEN_choosing_component_name_THEN_background_becomes_white(
    qtbot, template, dialog
):
    # Check that the background color of the ext field starts as red
    assert dialog.nameLineEdit.styleSheet() == RED_LINE_EDIT_STYLE_SHEET

    # Mimic the user entering a name in the text field
    enter_component_name(qtbot, template, dialog, UNIQUE_COMPONENT_NAME)

    # Check that the background color of the test field has changed to white
    assert dialog.nameLineEdit.styleSheet() == WHITE_LINE_EDIT_STYLE_SHEET


def test_UI_GIVEN_repeated_name_WHEN_choosing_component_name_THEN_background_remains_red(
    qtbot, template, dialog
):

    # Check that the background color of the text field starts as red
    assert dialog.nameLineEdit.styleSheet() == RED_LINE_EDIT_STYLE_SHEET

    # Mimic the user entering a non-unique name in the text field
    enter_component_name(qtbot, template, dialog, NONUNIQUE_COMPONENT_NAME)

    # Check that the background color of the test field has remained red
    assert dialog.nameLineEdit.styleSheet() == RED_LINE_EDIT_STYLE_SHEET


def test_UI_GIVEN_invalid_input_WHEN_adding_component_with_no_shape_THEN_add_component_window_remains_open(
    qtbot, template, dialog
):

    # Mimic the user entering a non-unique name in the text field
    enter_component_name(qtbot, template, dialog, NONUNIQUE_COMPONENT_NAME)

    # Mimic the user pressing the Add Component button
    qtbot.mouseClick(dialog.buttonBox, Qt.LeftButton)

    # The window won't close because the button is disabled
    assert template.isVisible()


def test_UI_GIVEN_valid_input_WHEN_adding_component_with_no_shape_THEN_add_component_window_closes(
    qtbot, template, dialog
):

    # Mimic the user entering a unique name in the text field
    enter_component_name(qtbot, template, dialog, UNIQUE_COMPONENT_NAME)

    # Mimic the user pressing the Add Component button
    qtbot.mouseClick(dialog.buttonBox, Qt.LeftButton)

    # The window will close because the input is valid and the button is enabled
    assert not template.isVisible()


def test_UI_GIVEN_valid_input_WHEN_adding_component_with_mesh_shape_THEN_add_component_window_closes(
    qtbot, template, dialog
):

    # Mimic the user selecting a mesh shape
    systematic_button_press(qtbot, template, dialog.meshRadioButton)

    # Mimic the user entering a unique name in the text field
    enter_component_name(qtbot, template, dialog, UNIQUE_COMPONENT_NAME)

    # Mimic the user entering a valid file name
    enter_file_path(
        qtbot, dialog, template, VALID_CUBE_MESH_FILE_PATH, VALID_CUBE_OFF_FILE
    )

    # Mimic the user entering valid units
    enter_units(qtbot, dialog, VALID_UNITS)

    # Mimic the user pressing the Add Component button
    qtbot.mouseClick(dialog.buttonBox, Qt.LeftButton)

    # The window will close because the input is valid and the button is enabled
    assert not template.isVisible()


def test_UI_GIVEN_valid_input_WHEN_adding_component_with_cylinder_shape_THEN_add_component_window_closes(
    qtbot, template, dialog
):
    # Mimic the user selecting a mesh shape
    systematic_button_press(qtbot, template, dialog.CylinderRadioButton)

    # Mimic the user entering a unique name in the text field
    enter_component_name(qtbot, template, dialog, UNIQUE_COMPONENT_NAME)

    # Mimic the user entering valid units
    enter_units(qtbot, dialog, VALID_UNITS)

    # Mimic the user pressing the Add Component button
    qtbot.mouseClick(dialog.buttonBox, Qt.LeftButton)

    # The window will close because the input is valid and the button is enabled
    assert not template.isVisible()


def test_UI_GIVEN_invalid_input_WHEN_adding_component_with_no_shape_THEN_add_component_button_is_disabled(
    qtbot, template, dialog
):

    # Mimic the user selecting a no shape
    systematic_button_press(qtbot, template, dialog.noShapeRadioButton)

    # Mimic the user entering a non-unique name in the text field
    enter_component_name(qtbot, template, dialog, NONUNIQUE_COMPONENT_NAME)

    show_window_and_wait_for_interaction(qtbot, template)

    # The Add Component button is disabled
    assert not dialog.buttonBox.isEnabled()


def test_UI_GIVEN_no_input_WHEN_adding_component_with_no_shape_THEN_add_component_button_is_disabled(
    qtbot, template, dialog
):

    # The Add Component button is disabled because no input was given
    assert not dialog.buttonBox.isEnabled()


def test_UI_GIVEN_valid_input_WHEN_adding_component_with_no_shape_THEN_add_component_button_is_enabled(
    qtbot, template, dialog
):

    # Mimic the user entering a unique name in the text field
    enter_component_name(qtbot, template, dialog, UNIQUE_COMPONENT_NAME)

    # The Add Component button is enabled because all the information required to create a no shape component is
    # there
    assert dialog.buttonBox.isEnabled()


def test_UI_GIVEN_no_file_path_WHEN_adding_component_with_mesh_shape_THEN_file_path_box_has_red_background(
    qtbot, template, dialog
):
    # Mimic the user selecting a mesh shape
    systematic_button_press(qtbot, template, dialog.meshRadioButton)

    # No file name was given so we expect the file input box background to be red
    assert dialog.fileLineEdit.styleSheet() == RED_LINE_EDIT_STYLE_SHEET


def test_UI_GIVEN_file_that_doesnt_exist_WHEN_adding_component_with_mesh_shape_THEN_file_path_box_has_red_background(
    qtbot, template, dialog
):
    # Mimic the user selecting a mesh shape
    systematic_button_press(qtbot, template, dialog.meshRadioButton)

    # Mimic the user entering a bad file path
    enter_file_path(qtbot, dialog, template, NONEXISTENT_FILE_PATH, "OFF")

    assert dialog.fileLineEdit.styleSheet() == RED_LINE_EDIT_STYLE_SHEET


def test_UI_GIVEN_file_with_wrong_extension_WHEN_adding_component_with_mesh_shape_THEN_file_path_box_has_red_background(
    qtbot, template, dialog
):

    # Mimic the user selecting a mesh shape
    systematic_button_press(qtbot, template, dialog.meshRadioButton)

    # Mimic the user giving the path for a file that exists but has the wrong extension
    enter_file_path(qtbot, dialog, template, WRONG_EXTENSION_FILE_PATH, "OFF")

    assert dialog.fileLineEdit.styleSheet() == RED_LINE_EDIT_STYLE_SHEET


def test_UI_GIVEN_valid_file_path_WHEN_adding_component_with_mesh_shape_THEN_file_path_box_has_white_background(
    qtbot, template, dialog
):
    # Mimic the user selecting a mesh shape
    systematic_button_press(qtbot, template, dialog.meshRadioButton)

    # Mimic the user entering a valid file name
    enter_file_path(
        qtbot, dialog, template, VALID_CUBE_MESH_FILE_PATH, VALID_CUBE_OFF_FILE
    )

    # The file input box should now have a white background
    assert dialog.fileLineEdit.styleSheet() == WHITE_LINE_EDIT_STYLE_SHEET


def test_UI_GIVEN_valid_file_path_WHEN_adding_component_with_mesh_shape_THEN_add_component_button_is_enabled(
    qtbot, template, dialog
):

    # Mimic the user selecting a mesh shape
    systematic_button_press(qtbot, template, dialog.meshRadioButton)

    # Mimic the user giving a valid component name
    enter_component_name(qtbot, template, dialog, UNIQUE_COMPONENT_NAME)

    # Mimic the user entering a valid file name
    enter_file_path(
        qtbot, dialog, template, VALID_CUBE_MESH_FILE_PATH, VALID_CUBE_OFF_FILE
    )

    assert dialog.buttonBox.isEnabled()


def test_UI_GIVEN_no_file_path_WHEN_adding_component_with_mesh_shape_THEN_add_component_button_is_disabled(
    qtbot, template, dialog
):
    # Mimic the user selecting a mesh shape
    systematic_button_press(qtbot, template, dialog.meshRadioButton)

    # Mimic the user entering a unique name in the text field
    enter_component_name(qtbot, template, dialog, UNIQUE_COMPONENT_NAME)

    # Although the component name is valid, no file path has been given so the button should be disabled
    assert not dialog.buttonBox.isEnabled()


def test_UI_GIVEN_nonexistent_file_path_WHEN_adding_component_with_mesh_shape_THEN_add_component_button_is_disabled(
    qtbot, template, dialog
):

    # Mimic the user selecting a mesh shape
    systematic_button_press(qtbot, template, dialog.meshRadioButton)

    # Mimic the user giving a valid component name
    enter_component_name(qtbot, template, dialog, UNIQUE_COMPONENT_NAME)

    # Mimic the user entering a nonexistent file path
    enter_file_path(qtbot, dialog, template, NONEXISTENT_FILE_PATH, VALID_CUBE_OFF_FILE)

    assert not dialog.buttonBox.isEnabled()


def test_UI_GIVEN_file_with_wrong_extension_WHEN_adding_component_with_mesh_shape_THEN_add_component_button_is_disabled(
    qtbot, template, dialog
):

    # Mimic the user selecting a mesh shape
    systematic_button_press(qtbot, template, dialog.meshRadioButton)

    # Mimic the user giving a valid component name
    enter_component_name(qtbot, template, dialog, UNIQUE_COMPONENT_NAME)

    # Mimic the user entering a path for a file that exists but has the wrong extension
    enter_file_path(
        qtbot, dialog, template, WRONG_EXTENSION_FILE_PATH, VALID_CUBE_OFF_FILE
    )

    assert not dialog.buttonBox.isEnabled()


def test_UI_GIVEN_no_units_WHEN_adding_component_with_mesh_shape_THEN_units_box_has_red_background(
    qtbot, template, dialog
):

    # Mimic the user selecting a mesh shape
    systematic_button_press(qtbot, template, dialog.meshRadioButton)

    # Mimic the user clearing the unit input box
    enter_units(qtbot, dialog, "")

    assert dialog.unitsLineEdit.styleSheet() == RED_LINE_EDIT_STYLE_SHEET


def test_UI_GIVEN_invalid_units_WHEN_adding_component_with_mesh_shape_THEN_units_box_has_red_background(
    qtbot, template, dialog
):

    # Mimic the user selecting a mesh shape
    systematic_button_press(qtbot, template, dialog.meshRadioButton)

    # Mimic the user giving invalid units input
    enter_units(qtbot, dialog, INVALID_UNITS)

    assert dialog.unitsLineEdit.styleSheet() == RED_LINE_EDIT_STYLE_SHEET


def test_UI_GIVEN_valid_units_WHEN_adding_component_with_mesh_shape_THEN_units_box_has_white_background(
    qtbot, template, dialog
):

    # Mimic the user selecting a mesh shape
    systematic_button_press(qtbot, template, dialog.meshRadioButton)

    # Mimic the replacing the default value with "km"
    enter_units(qtbot, dialog, VALID_UNITS)

    assert dialog.unitsLineEdit.styleSheet() == WHITE_LINE_EDIT_STYLE_SHEET


def test_UI_GIVEN_valid_units_WHEN_adding_component_with_mesh_shape_THEN_add_component_button_is_enabled(
    qtbot, template, dialog
):

    # Mimic the user selecting a mesh shape
    systematic_button_press(qtbot, template, dialog.meshRadioButton)

    # Mimic the user giving a valid component name
    enter_component_name(qtbot, template, dialog, UNIQUE_COMPONENT_NAME)

    # Mimic the user entering a valid file name
    enter_file_path(
        qtbot, dialog, template, VALID_CUBE_MESH_FILE_PATH, VALID_CUBE_OFF_FILE
    )

    # Mimic the user giving valid units
    enter_units(qtbot, dialog, VALID_UNITS)

    assert dialog.buttonBox.isEnabled()


def test_UI_GIVEN_no_units_WHEN_adding_component_with_mesh_shape_THEN_add_component_button_is_disabled(
    qtbot, template, dialog
):

    # Mimic the user selecting a mesh shape
    systematic_button_press(qtbot, template, dialog.meshRadioButton)

    # Mimic the user giving a valid component name
    enter_component_name(qtbot, template, dialog, UNIQUE_COMPONENT_NAME)

    # Mimic the user entering a valid file name
    enter_file_path(
        qtbot, dialog, template, VALID_CUBE_MESH_FILE_PATH, VALID_CUBE_OFF_FILE
    )

    # Mimic the user clearing the units box
    enter_units(qtbot, dialog, "")

    assert not dialog.buttonBox.isEnabled()


def test_UI_GIVEN_invalid_units_WHEN_adding_component_with_mesh_shape_THEN_add_component_button_is_disabled(
    qtbot, template, dialog
):

    # Mimic the user selecting a mesh shape
    systematic_button_press(qtbot, template, dialog.meshRadioButton)

    # Mimic the user giving a valid component name
    enter_component_name(qtbot, template, dialog, UNIQUE_COMPONENT_NAME)

    # Mimic the user entering a valid file name
    enter_file_path(
        qtbot, dialog, template, VALID_CUBE_MESH_FILE_PATH, VALID_CUBE_OFF_FILE
    )

    # Mimic the user giving invalid units input
    enter_units(qtbot, dialog, INVALID_UNITS)

    assert not dialog.buttonBox.isEnabled()


def test_UI_GIVEN_nonunique_name_WHEN_adding_component_with_mesh_shape_THEN_add_component_button_is_disabled(
    qtbot, template, dialog
):

    # Mimic the user selecting a mesh shape
    systematic_button_press(qtbot, template, dialog.meshRadioButton)

    # Mimic the user giving an invalid component name
    enter_component_name(qtbot, template, dialog, NONUNIQUE_COMPONENT_NAME)

    # Mimic the user entering a valid file name
    enter_file_path(
        qtbot, dialog, template, VALID_CUBE_MESH_FILE_PATH, VALID_CUBE_OFF_FILE
    )

    assert not dialog.buttonBox.isEnabled()


def test_UI_GIVEN_invalid_units_WHEN_adding_component_with_cylinder_shape_THEN_add_component_button_is_disabled(
    qtbot, template, dialog
):

    # Mimic the user selecting a mesh shape
    systematic_button_press(qtbot, template, dialog.CylinderRadioButton)

    # Mimic the user giving valid component name
    enter_component_name(qtbot, template, dialog, UNIQUE_COMPONENT_NAME)

    # Mimic the user giving invalid units input
    enter_units(qtbot, dialog, INVALID_UNITS)

    assert not dialog.buttonBox.isEnabled()


def test_UI_GIVEN_invalid_name_WHEN_adding_component_with_cylinder_shape_THEN_add_component_button_is_disabled(
    qtbot, template, dialog
):

    # Mimic the user selecting a mesh shape
    systematic_button_press(qtbot, template, dialog.CylinderRadioButton)

    # Mimic the user giving valid units input
    enter_units(qtbot, dialog, VALID_UNITS)

    # Mimic the user giving valid component name
    enter_component_name(qtbot, template, dialog, NONUNIQUE_COMPONENT_NAME)

    assert not dialog.buttonBox.isEnabled()


def test_UI_GIVEN_mesh_shape_selected_THEN_relevant_fields_are_visible(
    qtbot, template, dialog
):

    # Mimic the user selecting a mesh shape
    systematic_button_press(qtbot, template, dialog.meshRadioButton)

    assert dialog.shapeOptionsBox.isVisible()
    assert dialog.unitsbox.isVisible()
    assert dialog.geometryFileBox.isVisible()

    assert not dialog.cylinderOptionsBox.isVisible()


def test_UI_GIVEN_cylinder_shape_selected_THEN_relevant_fields_are_visible(
    qtbot, template, dialog
):

    # Mimic the user selecting a cylinder shape
    systematic_button_press(qtbot, template, dialog.CylinderRadioButton)

    assert dialog.shapeOptionsBox.isVisible()
    assert dialog.unitsbox.isVisible()
    assert dialog.cylinderOptionsBox.isVisible()

    assert not dialog.geometryFileBox.isVisible()


@pytest.mark.parametrize("comp_type_without_pixels", NO_PIXEL_OPTIONS)
def test_UI_GIVEN_file_chosen_WHEN_pixel_mapping_options_not_visible_THEN_pixel_mapping_list_remains_empty(
    qtbot, template, dialog, comp_type_without_pixels, mock_pixel_options
):

    # Mimic the user selecting a mesh shape
    systematic_button_press(qtbot, template, dialog.meshRadioButton)

    # Mimic the user selecting a component type that doesn't have pixel fields
    dialog.componentTypeComboBox.setCurrentIndex(comp_type_without_pixels[1])

    # Mimic the user giving a valid mesh file
    enter_file_path(
        qtbot, dialog, template, VALID_CUBE_MESH_FILE_PATH, VALID_CUBE_OFF_FILE
    )

    # Check that the pixel mapping list is still empty
    mock_pixel_options.populate_pixel_mapping_list_with_mesh.assert_not_called()


def test_UI_GIVEN_invalid_off_file_WHEN_creating_pixel_mapping_THEN_pixel_mapping_widget_isnt_populated(
    qtbot, template, dialog, mock_pixel_options
):

    make_pixel_options_visible(dialog, qtbot, template, dialog.meshRadioButton)

    # Give an invalid file
    enter_file_path(qtbot, dialog, template, VALID_CUBE_MESH_FILE_PATH, "hfhuihfiuhf")

    mock_pixel_options.populate_pixel_mapping_list_with_mesh.assert_not_called()


def test_UI_GIVEN_cylinder_shape_selected_WHEN_adding_component_THEN_default_values_are_correct(
    qtbot, template, dialog
):

    # Mimic the user selecting a cylinder shape
    systematic_button_press(qtbot, template, dialog.CylinderRadioButton)

    assert dialog.cylinderOptionsBox.isVisible()
    assert dialog.cylinderHeightLineEdit.value() == 1.0
    assert dialog.cylinderRadiusLineEdit.value() == 1.0
    assert dialog.cylinderXLineEdit.value() == 0.0
    assert dialog.cylinderYLineEdit.value() == 0.0
    assert dialog.cylinderZLineEdit.value() == 1.0


def test_UI_GIVEN_array_field_selected_and_edit_button_pressed_THEN_edit_dialog_is_shown(
    qtbot, template, dialog
):
    qtbot.mouseClick(dialog.addFieldPushButton, Qt.LeftButton)
    field = dialog.fieldsListWidget.itemWidget(dialog.fieldsListWidget.item(0))
    field.field_type_combo.setCurrentIndex(2)
    qtbot.addWidget(field)
    qtbot.mouseClick(field.edit_button, Qt.LeftButton)
    assert field.edit_dialog.isEnabled()


def test_UI_GIVEN_array_field_selected_and_edit_button_pressed_THEN_edit_dialog_table_is_shown(
    qtbot, template, dialog
):
    qtbot.mouseClick(dialog.addFieldPushButton, Qt.LeftButton)
    field = dialog.fieldsListWidget.itemWidget(dialog.fieldsListWidget.item(0))
    field.field_type_combo.setCurrentIndex(2)
    qtbot.addWidget(field)
    qtbot.mouseClick(field.edit_button, Qt.LeftButton)
    assert field.table_view.isEnabled()


def test_UI_GIVEN_user_provides_valid_pixel_configuration_THEN_add_component_button_is_enabled(
    qtbot, template, dialog, mock_pixel_validator
):

    make_pixel_options_visible(dialog, qtbot, template, dialog.meshRadioButton)

    mock_pixel_validator.unacceptable_pixel_states = Mock(return_value=[False, False])

    # Enter a valid name
    enter_component_name(qtbot, template, dialog, UNIQUE_COMPONENT_NAME)

    # Enter a valid file path
    enter_file_path(
        qtbot, dialog, template, VALID_CUBE_MESH_FILE_PATH, VALID_CUBE_OFF_FILE
    )

    # Check that the add component button is enabled
    assert dialog.buttonBox.isEnabled()


def test_UI_GIVEN_user_provides_invalid_pixel_grid_THEN_add_component_button_is_disabled(
    qtbot, template, dialog, mock_pixel_validator
):

    make_pixel_options_visible(dialog, qtbot, template, dialog.meshRadioButton)

    mock_pixel_validator.unacceptable_pixel_states = Mock(return_value=[True, False])

    # Enter a valid name
    enter_component_name(qtbot, template, dialog, UNIQUE_COMPONENT_NAME)

    # Enter a valid file path
    enter_file_path(
        qtbot, dialog, template, VALID_CUBE_MESH_FILE_PATH, VALID_CUBE_OFF_FILE
    )

    # Check that the add component button is disabled
    assert not dialog.buttonBox.isEnabled()


def test_UI_GIVEN_user_provides_invalid_pixel_mapping_THEN_add_component_button_is_disabled(
    qtbot, template, dialog, mock_pixel_validator
):

    make_pixel_options_visible(dialog, qtbot, template, dialog.meshRadioButton)

    mock_pixel_validator.unacceptable_pixel_states = Mock(return_value=[False, True])

    # Enter a valid name
    enter_component_name(qtbot, template, dialog, UNIQUE_COMPONENT_NAME)

    # Enter a valid file path
    enter_file_path(
        qtbot, dialog, template, VALID_CUBE_MESH_FILE_PATH, VALID_CUBE_OFF_FILE
    )

    # Check that the add component button is disabled
    assert not dialog.buttonBox.isEnabled()


def test_UI_GIVEN_user_presses_cylinder_button_WHEN_mesh_pixel_mapping_list_has_been_generated_THEN_new_pixel_mapping_list_is_generated(
    qtbot, template, dialog, mock_pixel_options
):

    make_pixel_options_visible(dialog, qtbot, template, dialog.meshRadioButton)

    mock_pixel_options.reset_mock()

    enter_file_path(
        qtbot, dialog, template, VALID_CUBE_MESH_FILE_PATH, VALID_CUBE_OFF_FILE
    )

    make_pixel_options_visible(dialog, qtbot, template, dialog.CylinderRadioButton)

    mock_pixel_options.reset_pixel_mapping_list.assert_called_once()
    mock_pixel_options.populate_pixel_mapping_list_with_cylinder_number.assert_called_once_with(
        1
    )


def test_UI_GIVEN_user_presses_mesh_button_WHEN_cylinder_pixel_mapping_list_has_been_generated_WHEN_new_pixel_mapping_list_is_generated(
    qtbot, template, dialog, mock_pixel_options
):

    make_pixel_options_visible(dialog, qtbot, template, dialog.CylinderRadioButton)

    mock_pixel_options.reset_mock()

    make_pixel_options_visible(dialog, qtbot, template, dialog.meshRadioButton)

    enter_file_path(
        qtbot, dialog, template, VALID_CUBE_MESH_FILE_PATH, VALID_CUBE_OFF_FILE
    )

    mock_pixel_options.reset_pixel_mapping_list.assert_called_once()
    mock_pixel_options.populate_pixel_mapping_list_with_mesh.assert_called_once_with(
        VALID_CUBE_MESH_FILE_PATH
    )


def test_UI_GIVEN_component_name_and_description_WHEN_editing_component_THEN_correct_values_are_loaded_into_UI(
    qtbot
):
    instrument = Instrument(NexusWrapper("test_component_editing_name"))

    component_model = ComponentTreeModel(instrument)

    name = "test"
    nx_class = "NXmonitor"
    desc = "description"

    component = instrument.create_component(
        name=name, nx_class=nx_class, description=desc
    )

    with patch("nexus_constructor.validators.PixelValidator") as mock_pixel_validator:
        mock_pixel_validator.unacceptable_pixel_states = Mock(return_value=[])
        with patch(
            "nexus_constructor.add_component_window.PixelOptions"
        ) as mock_pixel_options:
            mock_pixel_options.pixel_validator = mock_pixel_validator
            dialog = AddComponentDialog(
                instrument, component_model, component_to_edit=component, parent=None
            )
            template = QDialog()
            template.ui = dialog
            template.ui.setupUi(template)

            qtbot.addWidget(template)

            assert dialog.nameLineEdit.text() == name
            assert dialog.descriptionPlainTextEdit.text() == desc
            assert dialog.componentTypeComboBox.currentText() == nx_class


def test_UI_GIVEN_component_with_no_shape_WHEN_editing_component_THEN_no_shape_radio_is_checked(
    qtbot
):
    instrument = Instrument(NexusWrapper("test_component_editing_no_shape"))
    component_model = ComponentTreeModel(instrument)

    component = instrument.create_component("test", "NXpinhole", "")

    with patch("nexus_constructor.validators.PixelValidator") as mock_pixel_validator:
        mock_pixel_validator.unacceptable_pixel_states = Mock(return_value=[])
        with patch(
            "nexus_constructor.add_component_window.PixelOptions"
        ) as mock_pixel_options:
            mock_pixel_options.pixel_validator = mock_pixel_validator
            dialog = AddComponentDialog(
                instrument, component_model, component_to_edit=component, parent=None
            )
            template = QDialog()
            template.ui = dialog
            template.ui.setupUi(template)
            qtbot.addWidget(template)

            assert dialog.noShapeRadioButton.isChecked()


def test_UI_GIVEN_component_with_cylinder_shape_WHEN_editing_component_THEN_cylinder_shape_radio_is_checked(
    qtbot
):
    instrument = Instrument(NexusWrapper("test_component_editing_cylinder"))
    component_model = ComponentTreeModel(instrument)

    component_name = "test"
    component = instrument.create_component(component_name, "NXpinhole", "")
    component.set_cylinder_shape(QVector3D(1, 1, 1), height=3, radius=4)

    with patch("nexus_constructor.validators.PixelValidator") as mock_pixel_validator:
        mock_pixel_validator.unacceptable_pixel_states = Mock(return_value=[])
        with patch(
            "nexus_constructor.add_component_window.PixelOptions"
        ) as mock_pixel_options:
            mock_pixel_options.pixel_validator = mock_pixel_validator
            dialog = AddComponentDialog(
                instrument, component_model, component_to_edit=component
            )
            dialog.pixel_options = Mock(spec=PixelOptions)
            template = QDialog()
            template.ui = dialog
            template.ui.setupUi(template)
            qtbot.addWidget(template)

            assert dialog.CylinderRadioButton.isChecked()
            assert dialog.cylinderOptionsBox.isEnabled()


def test_UI_GIVEN_component_with_off_shape_WHEN_editing_component_THEN_mesh_shape_radio_is_checked(
    qtbot
):
    instrument = Instrument(NexusWrapper("test_component_editing_off"))
    component_model = ComponentTreeModel(instrument)

    component_name = "test"

    component = instrument.create_component(component_name, "NXpinhole", "")
    component.set_off_shape(
        OFFGeometryNoNexus(
            [
                QVector3D(0.0, 0.0, 1.0),
                QVector3D(0.0, 1.0, 0.0),
                QVector3D(0.0, 0.0, 0.0),
            ],
            [[0, 1, 2]],
        ),
        units="m",
        filename=os.path.join(os.path.pardir, "cube.off"),
    )

    dialog = AddComponentDialog(
        instrument, component_model, component_to_edit=component
    )
    dialog.pixel_options = Mock(spec=PixelOptions)
    template = QDialog()
    template.ui = dialog
    template.ui.setupUi(template)
    qtbot.addWidget(template)

    assert dialog.meshRadioButton.isChecked()
    assert dialog.fileLineEdit.isEnabled()
    assert dialog.fileBrowseButton.isEnabled()


def test_UI_GIVEN_component_with_off_shape_WHEN_editing_component_THEN_mesh_data_is_in_line_edits(
    qtbot
):
    instrument = Instrument(NexusWrapper("test_component_editing_off_filepath"))
    component_model = ComponentTreeModel(instrument)

    component_name = "test"
    units = "m"
    filepath = os.path.join(os.path.pardir, "cube.off")

    component = instrument.create_component(component_name, "NXpinhole", "")
    component.set_off_shape(
        OFFGeometryNoNexus(
            [
                QVector3D(0.0, 0.0, 1.0),
                QVector3D(0.0, 1.0, 0.0),
                QVector3D(0.0, 0.0, 0.0),
            ],
            [[0, 1, 2]],
        ),
        units=units,
        filename=filepath,
    )

    dialog = AddComponentDialog(
        instrument, component_model, component_to_edit=component
    )
    dialog.pixel_options = Mock(spec=PixelOptions)
    template = QDialog()
    template.ui = dialog
    template.ui.setupUi(template)
    qtbot.addWidget(template)

    assert dialog.meshRadioButton.isChecked()
    assert dialog.fileLineEdit.isEnabled()
    assert dialog.unitsLineEdit.isEnabled()
    assert dialog.unitsLineEdit.text() == units

    assert dialog.fileBrowseButton.isEnabled()

    assert dialog.fileLineEdit.isEnabled()
    assert dialog.fileLineEdit.text() == filepath


def test_UI_GIVEN_field_widget_with_string_type_THEN_value_property_is_correct(
    qtbot, dialog, template
):

    qtbot.mouseClick(dialog.addFieldPushButton, Qt.LeftButton)
    field = dialog.fieldsListWidget.itemWidget(dialog.fieldsListWidget.item(0))

    field.field_type_combo.setCurrentText(FieldType.scalar_dataset.value)
    field.field_type_combo.currentTextChanged.emit(field.field_type_combo.currentText())

    field.value_type_combo.setCurrentText("String")
    field.value_type_combo.currentTextChanged.emit(field.value_type_combo.currentText)

    field_name = "testfield"
    field_value = "testvalue"

    field.field_name_edit.setText(field_name)
    field.value_line_edit.setText(field_value)

    import h5py

    assert field.dtype == h5py.special_dtype(vlen=str)

    assert field.name == field_name
    assert field.value[...] == field_value


def enter_file_path(
    qtbot: pytestqt.qtbot.QtBot,
    dialog: AddComponentDialog,
    template: PySide2.QtWidgets.QDialog,
    file_path: str,
    file_contents: str,
):
    """
    Mimics the user entering a file path. Mimics a button click and patches the methods that deal with loading a
    geometry file.
    :param qtbot: The qtbot testing tool.
    :param dialog: An instance of an AddComponentDialog.
    :param template: The window/widget that holds the AddComponentDialog.
    :param file_path: The desired file path.
    :param file_contents: The file contents that are returned by the open mock.
    """
    with patch(
        "nexus_constructor.add_component_window.file_dialog", return_value=file_path
    ):
        with patch("builtins.open", mock_open(read_data=file_contents)):
            systematic_button_press(qtbot, template, dialog.fileBrowseButton)


def enter_component_name(
    qtbot: pytestqt.qtbot.QtBot,
    template: PySide2.QtWidgets.QDialog,
    dialog: AddComponentDialog,
    component_name: str,
):
    """
    Mimics the user entering a component name in the Add Component dialog. Clicks on the text field and enters a given
    name.
    :param qtbot: The qtbot testing tool.
    :param dialog: An instance of an AddComponentDialog.
    :param template: The window/widget that holds the AddComponentDialog.
    :param component_name: The desired component name.
    """
    qtbot.mouseClick(dialog.nameLineEdit, Qt.LeftButton)
    qtbot.keyClicks(dialog.nameLineEdit, component_name)
    show_and_close_window(qtbot, template)


@pytest.fixture(scope="session", autouse=True)
def cleanup(request):
    """
    Creates a QtBot at the end of all the tests and has it wait. This seems to be necessary in order to prevent
    the use of fixtures from causing a segmentation fault.
    """

    def make_another_qtest():
        bot = QtBot(request)
        bot.wait(1)

    request.addfinalizer(make_another_qtest)


def get_shape_type_button(dialog: AddComponentDialog, button_name: str):
    """
    Finds the shape type button that contains the given text.
    :param dialog: An instance of an AddComponentDialog.
    :param button_name: The name of the desired button.
    :return: The QRadioButton for the given shape type.
    """
    for child in dialog.shapeTypeBox.findChildren(PySide2.QtWidgets.QRadioButton):
        if child.text() == button_name:
            return child


def make_pixel_options_disappear(
    qtbot: pytestqt.qtbot.QtBot,
    dialog: AddComponentDialog,
    template: PySide2.QtWidgets.QDialog,
    component_index: int,
):
    """
    Create the conditions to allow the disappearance of the pixel options.
    :param qtbot: The qtbot testing tool.
    :param dialog: An instance of an AddComponentDialog.
    :param template: The window/widget that holds the AddComponentDialog.
    :param component_index: The index of a component type.
    """
    systematic_button_press(qtbot, template, dialog.noShapeRadioButton)
    dialog.componentTypeComboBox.setCurrentIndex(component_index)
    show_and_close_window(qtbot, template)


def make_pixel_options_appear(
    qtbot: pytestqt.qtbot.QtBot,
    button: QRadioButton,
    dialog: AddComponentDialog,
    template: PySide2.QtWidgets.QDialog,
    pixel_options_index: int,
):
    """
    Create the conditions to allow the appearance of the pixel options.
    :param qtbot: The qtbot testing tool.
    :param button: The Mesh or Cylinder radio button.
    :param dialog: An instance of an AddComponentDialog.
    :param template: The window/widget that holds the AddComponentDialog.
    :param pixel_options_index: The index of a component type for the combo box that has pixel fields.
    """
    systematic_button_press(qtbot, template, button)
    dialog.componentTypeComboBox.setCurrentIndex(pixel_options_index)
    show_and_close_window(qtbot, template)


def enter_units(qtbot: pytestqt.qtbot.QtBot, dialog: AddComponentDialog, units: str):
    """
    Mimics the user entering unit information. Clicks on the text field and removes the default value then enters a
    given string.
    :param qtbot: The qtbot testing tool.
    :param dialog: An instance of an AddComponentDialog object.
    :param units: The desired units input.
    """
    word_length = len(dialog.unitsLineEdit.text())
    for _ in range(word_length):
        qtbot.keyClick(dialog.unitsLineEdit, Qt.Key_Backspace)

    if len(units) > 0:
        qtbot.keyClicks(dialog.unitsLineEdit, units)
