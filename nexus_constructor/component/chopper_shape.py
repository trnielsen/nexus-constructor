import logging

from nexus_constructor.component.component_shape import ComponentShape
from nexus_constructor.geometry.cylindrical_geometry import CylindricalGeometry
from nexus_constructor.geometry import OFFGeometry, NoShapeGeometry
from nexus_constructor.geometry.disk_chopper.disk_chopper_checker import (
    NexusDefinedChopperChecker,
)
from nexus_constructor.geometry.disk_chopper.disk_chopper_geometry_creator import (
    DiskChopperGeometryCreator,
)
from typing import Optional, Union, List, Tuple
from PySide2.QtGui import QVector3D


class ChopperShape(ComponentShape):
    def get_shape(
        self,
    ) -> Tuple[
        Optional[Union[OFFGeometry, CylindricalGeometry, NoShapeGeometry]],
        Optional[List[QVector3D]],
    ]:
        # If there is a shape group then use that
        shape, _ = super().get_shape()
        if not isinstance(shape, NoShapeGeometry):
            return shape, None

        # Otherwise see if we can generate shape from the details we have
        chopper_checker = NexusDefinedChopperChecker(self.component_group)
        if chopper_checker.validate_chopper():
            return (
                DiskChopperGeometryCreator(
                    chopper_checker.chopper_details
                ).create_disk_chopper_geometry(),
                None,
            )
        else:
            logging.warning("Validation failed. Unable to create disk chopper mesh.")
        return NoShapeGeometry(), None
