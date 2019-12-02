from collections import OrderedDict
from enum import Enum

import h5py
from PySide2.QtGui import QVector3D
from PySide2.QtCore import QUrl, Signal, QObject
from PySide2.QtWidgets import QListWidgetItem

from nexus_constructor.component.component_factory import create_component
from nexus_constructor.geometry import (
    OFFGeometry,
    OFFGeometryNoNexus,
    NoShapeGeometry,
    CylindricalGeometry,
    OFFGeometryNexus,
)
from nexus_constructor.component_fields import FieldWidget, add_fields_to_component
from nexus_constructor.invalid_field_names import INVALID_FIELD_NAMES
from nexus_constructor.geometry.disk_chopper.disk_chopper_checker import (
    UserDefinedChopperChecker,
)
from nexus_constructor.geometry.disk_chopper.disk_chopper_geometry_creator import (
    DiskChopperGeometryCreator,
)
from ui.add_component import Ui_AddComponentDialog
from nexus_constructor.component.component_type import (
    make_dictionary_of_class_definitions,
    PIXEL_COMPONENT_TYPES,
    CHOPPER_CLASS_NAME,
)
from nexus_constructor.nexus.nexus_wrapper import get_name_of_node
from nexus_constructor.validators import (
    UnitValidator,
    NameValidator,
    GeometryFileValidator,
    GEOMETRY_FILE_TYPES,
    OkValidator,
    FieldType,
)
from nexus_constructor.instrument import Instrument
from nexus_constructor.ui_utils import file_dialog, validate_line_edit
from nexus_constructor.component_tree_model import ComponentTreeModel
from functools import partial
from nexus_constructor.ui_utils import generate_unique_name
from nexus_constructor.component.component import Component
from nexus_constructor.geometry.geometry_loader import load_geometry
from nexus_constructor.pixel_data import PixelData, PixelMapping, PixelGrid
from nexus_constructor.pixel_options import PixelOptions


class GeometryType(Enum):
    NONE = 1
    CYLINDER = 2
    MESH = 3


def update_existing_link_field(field: h5py.SoftLink, new_ui_field: FieldWidget):
    """
    Fill in a UI link field for an existing link in the component
    :param field: The link field in the component group
    :param new_ui_field: The new UI field to fill in with existing data
    """
    new_ui_field.field_type = FieldType.link.value
    new_ui_field.value = field.parent.get(field.name, getlink=True).path


def update_existing_array_field(field: h5py.Dataset, new_ui_field: FieldWidget):
    """
    Fill in a UI array field for an existing array field in the component group
    :param value: The array dataset's value to copy to the UI fields list model
    :param new_ui_field: The new UI field to fill in with existing data
    """
    new_ui_field.dtype = field.dtype
    new_ui_field.field_type = FieldType.array_dataset.value
    new_ui_field.value = field[()]


def update_existing_scalar_field(field: h5py.Dataset, new_ui_field: FieldWidget):
    """
    Fill in a UI scalar field for an existing scalar field in the component group
    :param field: The dataset to copy into the value line edit
    :param new_ui_field: The new UI field to fill in with existing data
    """
    dtype = field.dtype
    if "S" in str(dtype):
        dtype = h5py.special_dtype(vlen=str)
        new_ui_field.value = field[()]
    else:
        new_ui_field.value = field[()]
    new_ui_field.dtype = dtype
    new_ui_field.field_type = FieldType.scalar_dataset.value


def update_existing_stream_field(field: h5py.Dataset, new_ui_field: FieldWidget):
    """
    Fill in a UI stream field for an existing stream field in the component group
    :param field: The dataset to copy into the value line edit
    :param new_ui_field: The new UI field to fill in with existing data
    """
    new_ui_field.name = get_name_of_node(field)
    new_ui_field.field_type = FieldType.kafka_stream.value
    new_ui_field.streams_widget.update_existing_stream_info(field)


class AddComponentDialog(Ui_AddComponentDialog, QObject):
    nx_class_changed = Signal("QVariant")

    def __init__(
        self,
        instrument: Instrument,
        component_model: ComponentTreeModel,
        component_to_edit: Component = None,
        definitions_dir: str = "",
        parent=None,
    ):
        super(AddComponentDialog, self).__init__()
        if parent:
            self.setParent(parent)
        self.instrument = instrument
        self.component_model = component_model
        self.geometry_model = None
        _, self.nx_component_classes = make_dictionary_of_class_definitions(
            definitions_dir
        )
        self.nx_component_classes = OrderedDict(
            sorted(self.nx_component_classes.items())
        )

        self.cad_file_name = None
        self.possible_fields = []
        self.component_to_edit = component_to_edit
        self.valid_file_given = False
        self.pixel_options = None

    def setupUi(self, parent_dialog):
        """ Sets up push buttons and validators for the add component window. """
        super().setupUi(parent_dialog)

        # Connect the button calls with functions
        self.buttonBox.clicked.connect(self.on_ok)

        # Disable by default as component name will be missing at the very least.
        self.buttonBox.setEnabled(False)

        # Set default URL to nexus base classes in web view
        # self.webEngineView.setUrl(
        #     QUrl(
        #         "http://download.nexusformat.org/doc/html/classes/base_classes/index.html"
        #     )
        # )

        self.meshRadioButton.clicked.connect(self.show_mesh_fields)
        self.CylinderRadioButton.clicked.connect(self.show_cylinder_fields)
        self.noShapeRadioButton.clicked.connect(self.show_no_geometry_fields)
        self.fileBrowseButton.clicked.connect(self.mesh_file_picker)

        self.fileLineEdit.setValidator(GeometryFileValidator(GEOMETRY_FILE_TYPES))
        self.fileLineEdit.validator().is_valid.connect(
            partial(validate_line_edit, self.fileLineEdit)
        )
        self.fileLineEdit.textChanged.connect(self.populate_pixel_mapping_if_necessary)

        self.componentTypeComboBox.currentIndexChanged.connect(self.on_nx_class_changed)

        # Set default geometry type and show the related fields.
        self.noShapeRadioButton.setChecked(True)
        self.show_no_geometry_fields()

        component_list = self.instrument.get_component_list().copy()

        if self.component_to_edit:
            for item in component_list:
                if item.name == self.component_to_edit.name:
                    component_list.remove(item)

        name_validator = NameValidator(component_list)
        self.nameLineEdit.setValidator(name_validator)
        self.nameLineEdit.validator().is_valid.connect(
            partial(
                validate_line_edit,
                self.nameLineEdit,
                tooltip_on_accept="Component name is valid.",
                tooltip_on_reject=f"Component name is not valid. Suggestion: ",
                suggestion_callable=self.generate_name_suggestion,
            )
        )

        validate_line_edit(self.fileLineEdit, False)

        self.unitsLineEdit.setValidator(UnitValidator())
        self.unitsLineEdit.validator().is_valid.connect(
            partial(
                validate_line_edit,
                self.unitsLineEdit,
                tooltip_on_reject="Units not valid",
                tooltip_on_accept="Units Valid",
            )
        )

        self.componentTypeComboBox.addItems(list(self.nx_component_classes.keys()))
        self.componentTypeComboBox.currentIndexChanged.connect(
            self.change_pixel_options_visibility
        )

        # Set whatever the default nx_class is so the fields autocompleter can use the possible fields in the nx_class
        self.on_nx_class_changed()

        self.fieldsListWidget.itemClicked.connect(self.select_field)

        self.pixel_options = PixelOptions()
        self.pixel_options.setupUi(self.pixelOptionsWidget)
        self.pixelOptionsWidget.ui = self.pixel_options

        if self.component_to_edit:
            parent_dialog.setWindowTitle(
                f"Edit Component: {get_name_of_node(self.component_to_edit.group)}"
            )
            self._fill_existing_entries()
            self.pixel_options.fill_existing_entries()

        self.ok_validator = OkValidator(
            self.noShapeRadioButton,
            self.meshRadioButton,
            self.pixel_options.get_validator(),
        )
        self.ok_validator.is_valid.connect(self.buttonBox.setEnabled)

        self.nameLineEdit.validator().is_valid.connect(self.ok_validator.set_name_valid)

        [
            button.clicked.connect(self.ok_validator.validate_ok)
            for button in [
                self.meshRadioButton,
                self.CylinderRadioButton,
                self.noShapeRadioButton,
            ]
        ]

        self.unitsLineEdit.validator().is_valid.connect(
            self.ok_validator.set_units_valid
        )

        self.fileLineEdit.validator().is_valid.connect(self.ok_validator.set_file_valid)
        self.fileLineEdit.validator().is_valid.connect(self.set_file_valid)

        # Validate the default values set by the UI
        self.unitsLineEdit.validator().validate(self.unitsLineEdit.text(), 0)
        self.nameLineEdit.validator().validate(self.nameLineEdit.text(), 0)
        self.fileLineEdit.validator().validate(self.fileLineEdit.text(), 0)
        self.addFieldPushButton.clicked.connect(self.add_field)
        self.removeFieldPushButton.clicked.connect(self.remove_field)

        # Connect the pixel mapping press signal the populate pixel mapping method
        self.pixel_options.pixel_mapping_button_pressed.connect(
            self.populate_pixel_mapping_if_necessary
        )

        self.cylinderCountSpinBox.valueChanged.connect(
            self.populate_pixel_mapping_if_necessary
        )

        self.meshRadioButton.clicked.connect(self.set_pixel_related_changes)
        self.CylinderRadioButton.clicked.connect(self.set_pixel_related_changes)
        self.noShapeRadioButton.clicked.connect(self.set_pixel_related_changes)

    def set_pixel_related_changes(self):
        """
        Manages the pixel-related changes that are induced by changing the shape type. This entails changing the
        visibility of the pixel options widget, clearing the previous pixel mapping widget list (if necessary),
        generating a new pixel mapping widget list (if necessary), and reassessing the validity of the pixel input.
        """
        self.change_pixel_options_visibility()

        if not self.noShapeRadioButton.isChecked():
            self.clear_previous_mapping_list()
            self.populate_pixel_mapping_if_necessary()

        self.update_pixel_input_validity()

    def clear_previous_mapping_list(self):
        """
        Wipes the previous list of pixel mapping widgets. Required if the file has changed, or if the shape type has
        changed.
        """
        self.pixel_options.reset_pixel_mapping_list()

    def _fill_existing_entries(self):
        """
        Fill in component details in the UI if editing a component
        """
        self.buttonBox.setText("Edit Component")
        self.nameLineEdit.setText(self.component_to_edit.name)
        self.descriptionPlainTextEdit.setText(self.component_to_edit.description)
        self.componentTypeComboBox.setCurrentText(self.component_to_edit.nx_class)
        component_shape, _ = self.component_to_edit.shape
        if not component_shape or isinstance(component_shape, NoShapeGeometry):
            self.noShapeRadioButton.setChecked(True)
            self.noShapeRadioButton.clicked.emit()
        else:
            if isinstance(component_shape, OFFGeometryNexus):
                self.cad_file_name = component_shape.file_path
                self.meshRadioButton.setChecked(True)
                self.meshRadioButton.clicked.emit()
                if component_shape.file_path:
                    self.fileLineEdit.setText(component_shape.file_path)
            elif isinstance(component_shape, CylindricalGeometry):
                self.CylinderRadioButton.clicked.emit()
                self.CylinderRadioButton.setChecked(True)
                self.cylinderHeightLineEdit.setValue(component_shape.height)
                self.cylinderRadiusLineEdit.setValue(component_shape.radius)
                self.cylinderXLineEdit.setValue(component_shape.axis_direction.x())
                self.cylinderYLineEdit.setValue(component_shape.axis_direction.y())
                self.cylinderZLineEdit.setValue(component_shape.axis_direction.z())
                self.unitsLineEdit.setText(component_shape.units)

        scalar_fields, array_fields, stream_fields, link_fields = (
            self.component_to_edit.get_fields()
        )

        update_methods = [
            (scalar_fields, update_existing_scalar_field),
            (array_fields, update_existing_array_field),
            (stream_fields, update_existing_stream_field),
            (link_fields, update_existing_link_field),
        ]

        for fields, update_method in update_methods:
            for field in fields:
                new_ui_field = self.create_new_ui_field(field)
                update_method(field, new_ui_field)
                new_ui_field.attrs = field

    def create_new_ui_field(self, field):
        new_ui_field = self.add_field()
        new_ui_field.name = field.name.split("/")[-1]
        return new_ui_field

    def add_field(self) -> FieldWidget:
        item = QListWidgetItem()
        field = FieldWidget(
            self.possible_fields, self.fieldsListWidget, self.instrument
        )
        field.something_clicked.connect(partial(self.select_field, item))
        self.nx_class_changed.connect(field.field_name_edit.update_possible_fields)
        item.setSizeHint(field.sizeHint())

        self.fieldsListWidget.addItem(item)
        self.fieldsListWidget.setItemWidget(item, field)
        return field

    def select_field(self, widget):
        self.fieldsListWidget.setItemSelected(widget, True)

    def remove_field(self):
        for item in self.fieldsListWidget.selectedItems():
            self.fieldsListWidget.takeItem(self.fieldsListWidget.row(item))

    def generate_name_suggestion(self):
        """
        Generates a component name suggestion for use in the tooltip when a component is invalid.
        :return: The component name suggestion, based on the current nx_class.
        """
        return generate_unique_name(
            self.componentTypeComboBox.currentText().lstrip("NX"),
            self.instrument.get_component_list(),
        )

    def on_nx_class_changed(self):
        # self.webEngineView.setUrl(
        #     QUrl(
        #         f"http://download.nexusformat.org/sphinx/classes/base_classes/{self.componentTypeComboBox.currentText()}.html"
        #     )
        # )
        self.possible_fields = self.nx_component_classes[
            self.componentTypeComboBox.currentText()
        ]
        self.nx_class_changed.emit(self.possible_fields)

    def mesh_file_picker(self):
        """
        Opens the mesh file picker. Sets the file name line edit to the file path.
        :return: None
        """
        filename = file_dialog(False, "Open Mesh", GEOMETRY_FILE_TYPES)
        self.cad_file_name = filename
        self.fileLineEdit.setText(filename)

    def show_cylinder_fields(self):
        self.shapeOptionsBox.setVisible(True)
        self.geometryFileBox.setVisible(False)
        self.cylinderOptionsBox.setVisible(True)

    def show_no_geometry_fields(self):

        self.shapeOptionsBox.setVisible(False)
        if self.nameLineEdit.text():
            self.buttonBox.setEnabled(True)

    def show_mesh_fields(self):
        self.shapeOptionsBox.setVisible(True)
        self.geometryFileBox.setVisible(True)
        self.cylinderOptionsBox.setVisible(False)

    def generate_geometry_model(
        self, component: Component, pixel_data: PixelData = None
    ) -> OFFGeometry:
        """
        Generates a geometry model depending on the type of geometry selected and the current values
        of the line edits that apply to the particular geometry type.
        :return: The generated model.
        """
        if self.CylinderRadioButton.isChecked():

            geometry_model = component.set_cylinder_shape(
                QVector3D(
                    self.cylinderXLineEdit.value(),
                    self.cylinderYLineEdit.value(),
                    self.cylinderZLineEdit.value(),
                ),
                self.cylinderHeightLineEdit.value(),
                self.cylinderRadiusLineEdit.value(),
                self.unitsLineEdit.text(),
                pixel_data=pixel_data,
            )
        elif self.meshRadioButton.isChecked():
            mesh_geometry = OFFGeometryNoNexus()
            geometry_model = load_geometry(
                self.cad_file_name, self.unitsLineEdit.text(), mesh_geometry
            )

            # Units have already been used during loading the file, but we store them and file name
            # so we can repopulate their fields in the edit component window
            geometry_model.units = self.unitsLineEdit.text()
            geometry_model.file_path = self.cad_file_name

            component.set_off_shape(
                geometry_model,
                units=self.unitsLineEdit.text(),
                filename=self.fileLineEdit.text(),
                pixel_data=pixel_data,
            )
        else:
            chopper_checker = UserDefinedChopperChecker(self.fieldsListWidget)
            if (
                component.nx_class == CHOPPER_CLASS_NAME
                and chopper_checker.validate_chopper()
            ):
                geometry_model = DiskChopperGeometryCreator(
                    chopper_checker.chopper_details
                ).create_disk_chopper_geometry()
            else:
                geometry_model = NoShapeGeometry()
                component.remove_shape()

        return geometry_model

    def get_pixel_visibility_condition(self):
        """
        Determines if it is necessary to make the pixel options visible.
        :return: A bool indicating if the current shape and component type allow for pixel-related input.
        """
        return (
            self.componentTypeComboBox.currentText() in PIXEL_COMPONENT_TYPES
            and not self.noShapeRadioButton.isChecked()
        )

    def on_ok(self):
        """
        Retrieves information from the interface in order to create a component. By this point the input should already
        be valid as the validators control whether or not the Add Component button is enabled.
        """
        nx_class = self.componentTypeComboBox.currentText()
        component_name = self.nameLineEdit.text()
        description = self.descriptionPlainTextEdit.text()

        pixel_data = (
            self.pixel_options.generate_pixel_data()
            if nx_class in PIXEL_COMPONENT_TYPES
            else None
        )

        if self.component_to_edit:
            shape, positions = self.edit_existing_component(
                component_name, description, nx_class, pixel_data
            )
        else:
            shape, positions = self.create_new_component(
                component_name, description, nx_class, pixel_data
            )

        self.instrument.nexus.component_added.emit(
            self.nameLineEdit.text(), shape, positions
        )

    def create_new_component(
        self,
        component_name: str,
        description: str,
        nx_class: str,
        pixel_data: PixelData,
    ):
        """
        Creates a new component.
        :param component_name: The name of the component.
        :param description: The component description.
        :param nx_class: The component class.
        :param pixel_data: The PixelData for the component. Will be None if it was not given of if the component type
            doesn't have pixel-related fields.
        :return: The geometry object.
        """
        component = self.instrument.create_component(
            component_name, nx_class, description
        )
        self.generate_geometry_model(component, pixel_data)

        # In the future this should check if the class is NXdetector or NXdetector_module
        if nx_class == "NXdetector":
            if isinstance(pixel_data, PixelMapping):
                component.record_detector_number(pixel_data)
            if isinstance(pixel_data, PixelGrid):
                component.record_pixel_grid(pixel_data)

        add_fields_to_component(component, self.fieldsListWidget)
        self.component_model.add_component(component)

        component_with_geometry = create_component(
            self.instrument.nexus, component.group
        )
        return component_with_geometry.shape

    def edit_existing_component(
        self,
        component_name: str,
        description: str,
        nx_class: str,
        pixel_data: PixelData,
    ):
        """
        Edits an existing component.
        :param component_name: The component name.
        :param description: The component description.
        :param nx_class: The component class.
        :param pixel_data: The component PixelData. Can be None.
        :return: The geometry object.
        """

        # remove previous fields
        for field_group in self.component_to_edit.group.values():
            if field_group.name.split("/")[-1] not in INVALID_FIELD_NAMES:
                del self.instrument.nexus.nexus_file[field_group.name]

        # remove the previous shape from the qt3d view
        if not isinstance(self.component_to_edit.shape[0], NoShapeGeometry):
            self.parent().sceneWidget.delete_component(self.component_to_edit.name)

        self.component_to_edit.name = component_name
        self.component_to_edit.nx_class = nx_class
        self.component_to_edit.description = description

        add_fields_to_component(self.component_to_edit, self.fieldsListWidget)
        self.generate_geometry_model(self.component_to_edit, pixel_data)
        component_with_geometry = create_component(
            self.instrument.nexus, self.component_to_edit.group
        )
        return component_with_geometry.shape

    def change_pixel_options_visibility(self):
        """
        Changes the visibility of the pixel options depending on if the current component/shape type has pixel fields.
        """
        self.pixelOptionsWidget.setVisible(self.get_pixel_visibility_condition())

    def set_file_valid(self, validity):
        """
        Records the current status of the geometry file validity. This is used to determine if a list of pixel mapping
        widgets can be generated.
        :param validity: A bool indicating whether the mesh file was opened successfully.
        """
        self.valid_file_given = validity

    def populate_pixel_mapping_if_necessary(self):
        """
        Tells the pixel options widget to populate the pixel mapping widget provided certain conditions are met. Checks
        that the pixel options are visible then performs further checks depending on if the mesh or cylinder button
        has been selected.
        """

        if not self.pixelOptionsWidget.isVisible():
            return

        if self.meshRadioButton.isChecked():
            self.create_pixel_mapping_list_for_mesh()

        if self.CylinderRadioButton.isChecked():
            self.pixel_options.populate_pixel_mapping_list_with_cylinder_number(
                self.cylinderCountSpinBox.value()
            )

    def create_pixel_mapping_list_for_mesh(self):
        """
        Instructs the PixelOptions to create a list of Pixel Mapping widgets using a mesh file if the user has given a
        valid file and has not selected the same file twice in a row.
        """
        if (
            self.cad_file_name is not None
            and self.valid_file_given
            and self.pixel_options.get_current_mapping_filename() != self.cad_file_name
        ):
            self.pixel_options.populate_pixel_mapping_list_with_mesh(self.cad_file_name)

    def update_pixel_input_validity(self):
        """
        :return:
        """
        self.pixel_options.update_pixel_input_validity()
