"""
ListModel implementations for accessing and manipulating Geometry models in QML

See http://doc.qt.io/qt-5/qabstractlistmodel.html#subclassing for guidance on how to develop these classes, including
what signals need to be emitted when changes to the data are made.
"""

from geometry_constructor.data_model import Vector, CylindricalGeometry, OFFGeometry
from nexusutils.readwriteoff import parse_off_file
from PySide2.QtCore import Qt, QAbstractListModel, QModelIndex, QUrl, Slot

from geometry_constructor.instrument_model import InstrumentModel


class CylinderModel(QAbstractListModel):
    """
    A single item list model that allows properties of a Cylindrical geometry to be read and manipulated in QML
    """

    AxisXRole = Qt.UserRole + 100
    AxisYRole = Qt.UserRole + 101
    AxisZRole = Qt.UserRole + 102
    HeightRole = Qt.UserRole + 103
    RadiusRole = Qt.UserRole + 104

    def __init__(self):
        super().__init__()
        self.cylinder = CylindricalGeometry()

    def rowCount(self, parent=QModelIndex()):
        return 1

    def data(self, index, role=Qt.DisplayRole):
        if role == CylinderModel.AxisXRole:
            return self.cylinder.axis_direction.x
        if role == CylinderModel.AxisYRole:
            return self.cylinder.axis_direction.y
        if role == CylinderModel.AxisZRole:
            return self.cylinder.axis_direction.z
        if role == CylinderModel.HeightRole:
            return self.cylinder.height
        if role == CylinderModel.RadiusRole:
            return self.cylinder.radius

    def setData(self, index, value, role):
        changed = False
        if role == CylinderModel.AxisXRole:
            changed = self.cylinder.axis_direction.x != value
            self.cylinder.axis_direction.x = value
        if role == CylinderModel.AxisYRole:
            changed = self.cylinder.axis_direction.y != value
            self.cylinder.axis_direction.y = value
        if role == CylinderModel.AxisZRole:
            changed = self.cylinder.axis_direction.z != value
            self.cylinder.axis_direction.z = value
        if role == CylinderModel.HeightRole:
            changed = self.cylinder.height != value
            self.cylinder.height = value
        if role == CylinderModel.RadiusRole:
            changed = self.cylinder.radius != value
            self.cylinder.radius = value
        if changed:
            self.dataChanged.emit(index, index, role)
        return changed

    def flags(self, index):
        return super().flags(index) | Qt.ItemIsEditable

    def roleNames(self):
        return {
            CylinderModel.AxisXRole: b'axis_x',
            CylinderModel.AxisYRole: b'axis_y',
            CylinderModel.AxisZRole: b'axis_z',
            CylinderModel.HeightRole: b'cylinder_height',
            CylinderModel.RadiusRole: b'cylinder_radius'
        }

    def get_geometry(self):
        return self.cylinder

    @Slot(int, 'QVariant')
    def set_geometry(self, index, instrument: InstrumentModel):
        self.cylinder = instrument.components[index].geometry


class OFFModel(QAbstractListModel):
    """
    A single item list model that allows properties of an OFF geometry to be read and manipulated in QML
    """

    FileNameRole = Qt.UserRole + 200
    VerticesRole = Qt.UserRole + 201
    FacesRole = Qt.UserRole + 202

    def __init__(self):
        super().__init__()
        self.geometry = OFFGeometry()
        self.file_url = QUrl('')

    def rowCount(self, parent=QModelIndex()):
        return 1

    def data(self, index, role=Qt.DisplayRole):
        if role == OFFModel.FileNameRole:
            return self.file_url
        if role == OFFModel.VerticesRole:
            return self.geometry.vertices
        if role == OFFModel.FacesRole:
            return self.geometry.faces

    def setData(self, index, value, role):
        changed = False
        if role == OFFModel.FileNameRole:
            changed = self.file_url != value
            self.file_url = value
            if changed:
                self.load_data()
                self.dataChanged.emit(index, index, [OFFModel.VerticesRole,
                                                     OFFModel.FacesRole])
        if role == OFFModel.VerticesRole:
            changed = self.geometry.vertices != value
            self.geometry.vertices = value
        if role == OFFModel.FacesRole:
            changed = self.geometry.faces != value
            self.geometry.faces = value
        if changed:
            self.dataChanged.emit(index, index, role)
        return changed

    def flags(self, index):
        return super().flags(index) | Qt.ItemIsEditable

    def roleNames(self):
        return {
            OFFModel.FileNameRole: b'file_url',
            OFFModel.VerticesRole: b'vertices',
            OFFModel.FacesRole: b'faces'
        }

    # Read the OFF file into self.geometry
    def load_data(self):
        filename = self.file_url.toString(options=QUrl.PreferLocalFile)
        with open(filename) as file:
            vertices, faces = parse_off_file(file)

        print(vertices)
        print(faces)

        self.geometry.vertices = [Vector(x, y, z) for x, y, z in (vertex for vertex in vertices)]
        self.geometry.faces = [face.tolist()[1:] for face in faces]

    def get_geometry(self):
        return self.geometry

    @Slot(int, 'QVariant')
    def set_geometry(self, index, instrument: InstrumentModel):
        self.geometry = instrument.components[index].geometry
