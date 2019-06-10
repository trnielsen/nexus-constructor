from PySide2.QtWidgets import QDialog
from nexus_constructor.nexus_wrapper import NexusWrapper
from nexus_constructor.addcomponentwindow import AddComponentDialog
from nexus_constructor.utils import file_dialog
from ui.mainwindow import Ui_MainWindow
import silx.gui.hdf5
from nexus_constructor.component_tree_view import ComponentEditorDelegate
from nexus_constructor.component_tree_model import ComponentTreeModel


from nexus_constructor.nexus_filewriter_json import writer

NEXUS_FILE_TYPES = {"NeXus Files": ["nxs", "nex", "nx5"]}
JSON_FILE_TYPES = {"JSON Files": ["json", "JSON"]}


class MainWindow(Ui_MainWindow):
    def __init__(self, nexus_wrapper: NexusWrapper):
        super().__init__()
        self.nexus_wrapper = nexus_wrapper

    def setupUi(self, main_window):
        super().setupUi(main_window)

        self.addComponentButton.clicked.connect(self.show_add_component_window)
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
        self.treemodel.insertH5pyObject(self.nexus_wrapper.nexus_file)
        self.nexus_wrapper.file_changed.connect(self.update_nexus_file_structure_view)
        self.verticalLayout.addWidget(self.widget)
        #self.listView.setModel(self.nexus_wrapper.get_component_list())

        self.widget.setVisible(True)

        import nexus_constructor.test_components as Cp
        Sample = Cp.Component("Sample")
        Detector = Cp.Cylinder(Name="Detector1")
        Monitor = Cp.Cylinder(Name="Monitor1")
        Detector.Transformations.append(Cp.Translation("DetMovement", Detector))
        Detector.Transformations.append(Cp.Rotation("DetRotation", Detector))
        MonTrans = Cp.Translation("MonMovement", Monitor)
        MonTrans.X = 0.5
        MonTrans.Y = -10
        MonTrans.Z = 5
        Monitor.Transformations.append(MonTrans)
        Components = [Sample, Detector, Monitor]

        self.component_model = ComponentTreeModel(Components)

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


    def update_nexus_file_structure_view(self, nexus_file):
        self.treemodel.clear()
        self.treemodel.insertH5pyObject(nexus_file)

    def save_to_nexus_file(self):
        filename = file_dialog(True, "Save Nexus File", NEXUS_FILE_TYPES)
        self.nexus_wrapper.save_file(filename)

    def save_to_filewriter_json(self):
        filename = file_dialog(True, "Save JSON File", JSON_FILE_TYPES)
        self.nexus_wrapper.save_file(filename)
        if filename:
            with open(filename, "w") as file:
                file.write(
                    writer.generate_json(self.nexus_wrapper.get_component_list())
                )

    def open_nexus_file(self):
        filename = file_dialog(False, "Open Nexus File", NEXUS_FILE_TYPES)
        self.nexus_wrapper.open_file(filename)

    def show_add_component_window(self):
        add_window = QDialog()
        add_window.ui = AddComponentDialog(self.nexus_wrapper)
        add_window.ui.setupUi(add_window)
        add_window.exec()
