from ui.transformation import Ui_Transformation
from ui.link import Ui_Link
from PySide2.QtWidgets import QGroupBox, QFrame, QWidget
from PySide2.QtGui import QVector3D
from nexus_constructor.transformations import Transformation
from nexus_constructor.instrument import Instrument
from nexus_constructor.component_tree_model import LinkTransformation


class EditTransformation(QGroupBox):
    def __init__(self, parent: QWidget, transformation: Transformation):
        super().__init__(parent)
        self.transformation_frame = Ui_Transformation()
        self.transformation_frame.setupUi(self)
        self.transformation = transformation
        current_vector = self.transformation.vector
        self.transformation_frame.xSpinBox.setValue(current_vector.x())
        self.transformation_frame.ySpinBox.setValue(current_vector.y())
        self.transformation_frame.zSpinBox.setValue(current_vector.z())
        self.transformation_frame.nameLineEdit.setText(self.transformation.name)
        self.transformation_frame.valueSpinBox.setValue(self.transformation.value)
        self.disable()

    def disable(self):
        self.transformation_frame.xSpinBox.setEnabled(False)
        self.transformation_frame.ySpinBox.setEnabled(False)
        self.transformation_frame.zSpinBox.setEnabled(False)
        self.transformation_frame.valueSpinBox.setEnabled(False)
        self.transformation_frame.nameLineEdit.setEnabled(False)
        self.transformation_frame.editButton.setText("Edit")

    def enable(self):
        self.transformation_frame.xSpinBox.setEnabled(True)
        self.transformation_frame.ySpinBox.setEnabled(True)
        self.transformation_frame.zSpinBox.setEnabled(True)
        self.transformation_frame.valueSpinBox.setEnabled(True)
        self.transformation_frame.nameLineEdit.setEnabled(True)
        self.transformation_frame.editButton.setText("Done")

    def saveChanges(self):
        self.transformation.name = self.transformation_frame.nameLineEdit.text()
        self.transformation.vector = QVector3D(
            self.transformation_frame.xSpinBox.value(),
            self.transformation_frame.ySpinBox.value(),
            self.transformation_frame.zSpinBox.value(),
        )
        self.transformation.value = self.transformation_frame.valueSpinBox.value()


class EditTranslation(EditTransformation):
    def __init__(self, parent: QWidget, transformation: Transformation):
        super().__init__(parent, transformation)
        self.transformation_frame.valueLabel.setText("Position (m)")
        self.setTitle("Translation")


class EditRotation(EditTransformation):
    def __init__(self, parent: QWidget, transformation: Transformation):
        super().__init__(parent, transformation)
        self.transformation_frame.valueLabel.setText("Rotation (°)")
        self.setTitle("Rotation")


class EditTransformationLink(QFrame):
    def __init__(
        self, parent: QWidget, link: LinkTransformation, instrument: Instrument
    ):
        super().__init__(parent)
        self.link = link
        self.instrument = instrument
        self.link_frame = Ui_Link()
        self.link_frame.setupUi(self)
        components = self.instrument.get_component_list()
        for current_component in components:
            transformations = current_component.transforms
            for transform in transformations:
                self.link_frame.TransformationsComboBox.addItem(transform.name)

    def enable(self):
        print("EditTransformationLink.enable not implemented.")

    def disable(self):
        print("EditTransformationLink.disable not implemented.")

    def saveChanges(self):
        print("EditTransformationLink.saveChanges not implemented.")