from PySide2.QtWidgets import QDialog, QLabel, QGridLayout, QAction, QToolBar
from PySide2.QtGui import QIcon
from nexus_constructor.instrument import Instrument
from nexus_constructor.add_component_window import AddComponentDialog
from nexus_constructor.ui_utils import file_dialog
from ui.main_window import Ui_MainWindow
import silx.gui.hdf5
import os

from functools import partial
import h5py

from nexus_constructor.component import ComponentModel
from nexus_constructor.transformations import TransformationModel, TransformationsList
from nexus_constructor.component_tree_model import ComponentTreeModel
from nexus_constructor.component_tree_view import ComponentEditorDelegate
from nexus_constructor.nexus_filewriter_json import writer

NEXUS_FILE_TYPES = {"NeXus Files": ["nxs", "nex", "nx5"]}
JSON_FILE_TYPES = {"JSON Files": ["json", "JSON"]}


class MainWindow(Ui_MainWindow):
    def __init__(self, instrument: Instrument):
        super().__init__()
        self.instrument = instrument

    def setupUi(self, main_window):
        super().setupUi(main_window)

        self.actionExport_to_NeXus_file.triggered.connect(self.save_to_nexus_file)
        self.actionOpen_NeXus_file.triggered.connect(self.open_nexus_file)
        self.actionExport_to_Filewriter_JSON.triggered.connect(
            self.save_to_filewriter_json
        )

        self.widget = silx.gui.hdf5.Hdf5TreeView()
        self.widget.setAcceptDrops(True)
        self.widget.setDragEnabled(True)
        self.treemodel = self.widget.findHdf5TreeModel()
        self.treemodel.setDatasetDragEnabled(True)
        self.treemodel.setFileDropEnabled(True)
        self.treemodel.setFileMoveEnabled(True)
        self.treemodel.insertH5pyObject(self.instrument.nexus.nexus_file)
        self.instrument.nexus.file_changed.connect(
            self.update_nexus_file_structure_view
        )
        self.verticalLayout.addWidget(self.widget)
        self.instrument.nexus.show_entries_dialog.connect(self.show_entries_dialog)

        self.instrument.nexus.component_added.connect(self.sceneWidget.add_component)
        self.instrument.nexus.file_changed.connect(self.update_nexus_file_structure_view)

        self.set_up_warning_window()

        self.widget.setVisible(True)

        self.component_model = ComponentTreeModel(self.instrument)

        self.componentTreeView.setDragEnabled(True)
        self.componentTreeView.setAcceptDrops(True)
        self.componentTreeView.setDropIndicatorShown(True)
        self.componentTreeView.header().hide()
        self.component_delegate = ComponentEditorDelegate(self.componentTreeView)
        self.componentTreeView.setItemDelegate(self.component_delegate)
        self.componentTreeView.setModel(self.component_model)
        self.componentTreeView.updateEditorGeometries()
        self.componentTreeView.updateGeometries()
        self.componentTreeView.updateGeometry()
        self.componentTreeView.clicked.connect(self.on_clicked)

        self.component_tool_bar = QToolBar("Actions", self.tab_2)
        self.new_component_action = QAction(QIcon("ui/new_component.png"), "New component", self.tab_2)
        self.new_component_action.triggered.connect(self.show_add_component_window)
        self.component_tool_bar.addAction(self.new_component_action)
        self.new_translation_action = QAction(QIcon("ui/new_translation.png"), "New translation", self.tab_2)
        self.new_translation_action.triggered.connect(self.on_add_translation)
        self.new_translation_action.setEnabled(False)
        self.component_tool_bar.addAction(self.new_translation_action)
        self.new_rotation_action = QAction(QIcon("ui/new_rotation.png"), "New rotation", self.tab_2)
        self.new_rotation_action.triggered.connect(self.on_add_rotation)
        self.new_rotation_action.setEnabled(False)
        self.component_tool_bar.addAction(self.new_rotation_action)
        self.duplicate_action = QAction(QIcon("ui/duplicate.png"), "Duplicate", self.tab_2)
        self.component_tool_bar.addAction(self.duplicate_action)
        self.duplicate_action.triggered.connect(self.on_duplicate_node)
        self.duplicate_action.setEnabled(False)
        self.delete_action = QAction(QIcon("ui/delete.png"), "Delete", self.tab_2)
        self.delete_action.triggered.connect(self.on_delete_item)
        self.delete_action.setEnabled(False)
        self.component_tool_bar.addAction(self.delete_action)
        self.componentsTabLayout.insertWidget(0, self.component_tool_bar)

    def show_entries_dialog(self, map_of_entries: dict, nexus_file: h5py.File):
        """
        Shows the entries dialog when loading a nexus file if there are multiple entries.
        :param map_of_entries: A map of the entry groups, with the key being the name of the group and value being the actual h5py group object.
        :param nexus_file: A reference to the nexus file.
        """
        self.entries_dialog = QDialog()
        self.entries_dialog.setMinimumWidth(400)
        self.entries_dialog.setWindowTitle(
            "Multiple Entries found. Please choose the entry name from the list."
        )
        combo = QComboBox()

        # Populate the combo box with the names of the entry groups.
        [combo.addItem(x) for x in map_of_entries.keys()]

        ok_button = QPushButton()

        ok_button.setText("OK")
        ok_button.clicked.connect(self.entries_dialog.close)

        # Connect the clicked signal of the ok_button to instrument.load_file and pass the file and entry group object.
        ok_button.clicked.connect(
            partial(
                self.instrument.nexus.load_file,
                map_of_entries[combo.currentText()],
                nexus_file,
            )
        )

        self.entries_dialog.setLayout(QGridLayout())

        self.entries_dialog.layout().addWidget(QLabel("Entry:"))
        self.entries_dialog.layout().addWidget(combo)
        self.entries_dialog.layout().addWidget(ok_button)
        self.entries_dialog.show()

    def set_button_state(self):
        indices = self.componentTreeView.selectedIndexes()
        if len(indices) == 0 or len(indices) != 1:
            self.delete_action.setEnabled(False)
            self.duplicate_action.setEnabled(False)
            self.new_rotation_action.setEnabled(False)
            self.new_translation_action.setEnabled(False)
        else:
            selected_object = indices[0].internalPointer()
            if isinstance(selected_object, ComponentModel) or isinstance(selected_object, TransformationModel):
                self.delete_action.setEnabled(True)
                self.duplicate_action.setEnabled(True)
            else:
                self.delete_action.setEnabled(False)
                self.duplicate_action.setEnabled(False)
            self.new_rotation_action.setEnabled(True)
            self.new_translation_action.setEnabled(True)

    def on_clicked(self, index):
        self.set_button_state()

    def on_duplicate_node(self):
        selected = self.componentTreeView.selectedIndexes()
        if len(selected) > 0:
            self.component_model.duplicate_node(selected[0])

    def on_add_translation(self):
        selected = self.componentTreeView.selectedIndexes()
        if len(selected) > 0:
            current_index = selected[0]
            self.component_model.add_translation(current_index)
            current_pointer = current_index.internalPointer()
            if not self.componentTreeView.isExpanded(current_index) and (isinstance(current_pointer, TransformationsList) or isinstance(current_pointer,ComponentModel)):
                self.componentTreeView.expand(current_index)
                if isinstance(current_pointer,ComponentModel):
                    trans_list_index = self.component_model.index(1, 0, current_index)
                    self.componentTreeView.expand(trans_list_index)


    def on_add_rotation(self):
        selected = self.componentTreeView.selectedIndexes()
        if len(selected) > 0:
            self.component_model.add_rotation(selected[0])

    def set_up_warning_window(self):
        """
        Sets up the warning dialog that is shown when the definitions submodule has not been cloned.
        :return:
        """
        definitions_dir = os.path.join(os.curdir, "definitions")

        # Will contain .git even if missing so check that it does not contain just that file.
        if not os.path.exists(definitions_dir) or len(os.listdir(definitions_dir)) <= 1:
            self.warning_window = QDialog()
            self.warning_window.setWindowTitle("NeXus definitions missing")
            self.warning_window.setLayout(QGridLayout())
            self.warning_window.layout().addWidget(
                QLabel(
                    "Warning: NeXus definitions are missing. Did you forget to clone the submodules?\n run git submodule update --init "
                )
            )
            # Set add component button to disabled, as it wouldn't work without the definitions.
            self.pushButton.setEnabled(False)
            self.warning_window.show()

    def update_nexus_file_structure_view(self, nexus_file):
        self.treemodel.clear()
        self.treemodel.insertH5pyObject(nexus_file)

    def save_to_nexus_file(self):
        filename = file_dialog(True, "Save Nexus File", NEXUS_FILE_TYPES)
        self.instrument.nexus.save_file(filename)

    def save_to_filewriter_json(self):
        filename = file_dialog(True, "Save JSON File", JSON_FILE_TYPES)
        self.instrument.nexus.save_file(filename)
        if filename:
            with open(filename, "w") as file:
                file.write(writer.generate_json(self.instrument.get_component_list()))

    def open_nexus_file(self):
        filename = file_dialog(False, "Open Nexus File", NEXUS_FILE_TYPES)
        self.instrument.nexus.open_file(filename)

    def show_add_component_window(self):
        self.add_component_window = QDialog()
        self.add_component_window.ui = AddComponentDialog(self.instrument, self.component_model)
        self.add_component_window.ui.setupUi(self.add_component_window)
        self.add_component_window.show()

    def on_delete_item(self):
        selected = self.componentTreeView.selectedIndexes()
        for item in selected:
            self.component_model.remove_node(item)
        self.set_button_state()
