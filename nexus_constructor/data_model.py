import attr
from enum import Enum, unique
from math import sin, cos, pi, acos, degrees
from typing import List
from PySide2.QtGui import QVector3D, QMatrix4x4
from nexus_constructor.unit_converter import calculate_unit_conversion_factor
from numpy import array, allclose
from numpy.linalg import norm
from abc import ABC, abstractmethod


def validate_nonzero_vector(instance, attribute, value):
    if value.x == 0 and value.y == 0 and value.z == 0:
        raise ValueError("Vector is zero length")


# Temporary method here until the one above is no longer needed
def validate_nonzero_qvector(instance, attribute, value):
    if value.x() == 0 and value.y() == 0 and value.z() == 0:
        raise ValueError("Vector is zero length")


class Vector:
    """A vector in 3D space, defined by x, y and z coordinates"""

    def __init__(self, x, y, z):
        """

        :param x: The x coordinate.
        :param y: The y coordinate.
        :param z: The z coordinate.
        """
        self.vector = array([x, y, z], dtype=float)

    @property
    def x(self):
        return self.vector[0].item()

    @x.setter
    def x(self, value):
        self.vector[0] = value

    @property
    def y(self):
        return self.vector[1].item()

    @y.setter
    def y(self, value):
        self.vector[1] = value

    @property
    def z(self):
        return self.vector[2].item()

    @z.setter
    def z(self, value):
        self.vector[2] = value

    @property
    def magnitude(self):
        return norm(self.vector)

    @property
    def unit_list(self):
        return self.vector / self.magnitude

    def __eq__(self, other):
        ...
        return self.__class__ == other.__class__ and allclose(self.vector, other.vector)

@attr.s
class Geometry(ABC):
    """Base class for geometry a component can take"""
    geometry_str = None  # A string describing the geometry type to the user

    @property
    @abstractmethod
    def off_geometry(self):
        pass

@attr.s
class CylindricalGeometry(Geometry):
    """
    Describes the shape of a cylinder in 3D space

    The cylinder is assumed to have the center of its base located at the origin of the local coordinate system, and is
    described by the direction of its axis, its height, and radius.
    """
    geometry_str = "Cylinder"
    units = attr.ib(default="m", type=str)
    axis_direction = attr.ib(
        factory=lambda: QVector3D(1, 0, 0),
        type=QVector3D,
        validator=validate_nonzero_qvector,
    )
    height = attr.ib(default=1, type=float)
    radius = attr.ib(default=1, type=float)

    @property
    def base_center_point(self):
        return QVector3D(0, 0, 0)

    @property
    def base_edge_point(self):
        # rotate a point on the edge of a Z axis aligned cylinder by the rotation matrix
        return (
            QVector3D(self.radius * calculate_unit_conversion_factor(self.units), 0, 0)
            * self.rotation_matrix
        )

    @property
    def top_center_point(self):
        return (
            self.axis_direction.normalized()
            * self.height
            * calculate_unit_conversion_factor(self.units)
        )

    @property
    def off_geometry(self, steps=20):

        unit_conversion_factor = calculate_unit_conversion_factor(self.units)

        # A list of vertices describing the circle at the bottom of the cylinder
        bottom_circle = [QVector3D(sin(2 * pi * i / steps), cos(2 * pi * i / steps), 0) * self.radius
                         for i in range(steps)]

        # The top of the cylinder is the bottom shifted upwards
        top_circle = [vector + QVector3D(0, 0, self.height) for vector in bottom_circle]

        # The true cylinder are all vertices from the unit cylinder multiplied by the conversion factor
        vertices = [vector * unit_conversion_factor for vector in bottom_circle + top_circle]

        # rotate each vertex to produce the desired cylinder mesh
        rotate_matrix = self.rotation_matrix
        vertices = [vector * rotate_matrix for vector in vertices]

        def vertex_above(vertex):
            """
            Returns the index of the vertex above this one in the cylinder.
            """
            return vertex + steps

        def next_vertex(vertex):
            """
            Returns the next vertex around in the top or bottom circle of the cylinder.
            """
            return (vertex + 1) % steps

        # Rectangular faces joining the top and bottom
        rectangle_faces = [[i, vertex_above(i), vertex_above(next_vertex(i)), next_vertex(i)] for i in range(steps)]

        # Step sided shapes describing the top and bottom
        # The bottom uses steps of -1 to preserve winding order
        top_bottom_faces = [[i for i in range(steps)], [i for i in range((2 * steps) - 1, steps - 1, -1)], ]

        return OFFGeometry(
            vertices=vertices,
            faces=rectangle_faces + top_bottom_faces
        )

    @property
    def rotation_matrix(self):
        """
        :return: A QMatrix4x4 describing the rotation from the Z axis to the cylinder's axis
        """
        default_axis = QVector3D(0, 0, 1)
        desired_axis = self.axis_direction.normalized()
        rotate_axis = QVector3D.crossProduct(desired_axis, default_axis)
        rotate_radians = acos(QVector3D.dotProduct(desired_axis, default_axis))
        rotate_matrix = QMatrix4x4()
        rotate_matrix.rotate(degrees(rotate_radians), rotate_axis)
        return rotate_matrix


@attr.s
class OFFGeometry(Geometry):
    """
    Stores arbitrary 3D geometry as a list of vertices and faces, based on the Object File Format

    vertices:   list of Vector objects used as corners of polygons in the geometry
    faces:  list of integer lists. Each sublist is a winding path around the corners of a polygon. Each sublist item is
            an index into the vertices list to identify a specific point in 3D space
    """
    geometry_str = "OFF"
    vertices = attr.ib(factory=list, type=List[QVector3D])
    faces = attr.ib(factory=list, type=List[List[int]])

    @property
    def winding_order(self):
        return [point for face in self.faces for point in face]

    @property
    def winding_order_indices(self):
        face_sizes = [len(face) for face in self.faces]
        return [sum(face_sizes[0:i]) for i in range(len(face_sizes))]

    @property
    def off_geometry(self):
        return self


@attr.s
class NoShapeGeometry(Geometry):
    """
    Dummy object for components with no geometry.
    """
    geometry_str = "None"

    @property
    def off_geometry(self):
        return OFFCube


OFFCube = OFFGeometry(
            vertices=[
                QVector3D(-0.5, -0.5, 0.5),
                QVector3D(0.5, -0.5, 0.5),
                QVector3D(-0.5, 0.5, 0.5),
                QVector3D(0.5, 0.5, 0.5),
                QVector3D(-0.5, 0.5, -0.5),
                QVector3D(0.5, 0.5, -0.5),
                QVector3D(-0.5, -0.5, -0.5),
                QVector3D(0.5, -0.5, -0.5),
            ],
            faces=[
                [0, 1, 3, 2],
                [2, 3, 5, 4],
                [4, 5, 7, 6],
                [6, 7, 1, 0],
                [1, 7, 5, 3],
                [6, 0, 2, 4],
            ],
        )


@attr.s
class PixelData:
    """Base class for a detector's pixel description"""

    pass


class CountDirection(Enum):
    ROW = 1
    COLUMN = 2


class Corner(Enum):
    TOP_LEFT = 1
    TOP_RIGHT = 2
    BOTTOM_LEFT = 3
    BOTTOM_RIGHT = 4


@attr.s
class PixelGrid(PixelData):
    """
    Represents a grid of pixels arranged at regular intervals on a 2D plane

    Rows and columns increase along the X and Y axis positive directions, with the origin in the bottom left corner,
    the X axis increasing to the left, and the Y axis increasing upwards.

    The center of the detector is located at the origin of the pixel grid.

    ^ y
    |
    |    x
    +---->

    Detector numbers will be assigned from a starting value in the attribute 'first_id'
    This count will increase by 1 for each instance of the pixel in the grid.
    The corner that counting starts in, and whether counting should first happen along rows or columns can be set with
    the 'count_direction' and 'initial_count_corner' attributes, which respectively take 'CountDirection' and 'Corner'
    Enum values.
    """

    rows = attr.ib(default=1, type=int)
    columns = attr.ib(default=1, type=int)
    row_height = attr.ib(default=1, type=float)
    col_width = attr.ib(default=1, type=float)
    first_id = attr.ib(default=0, type=int)
    count_direction = attr.ib(default=CountDirection.ROW, type=CountDirection)
    initial_count_corner = attr.ib(default=Corner.BOTTOM_LEFT, type=Corner)


@attr.s
class PixelMapping(PixelData):
    """
    Maps faces in a 3D geometry to the detector id's

    To be used in conjunction with an OFFGeometry instance. This classes pixel_ids attribute should be the same length
    as the geometry's faces list. The value of this list at any given index should be the detector id number that the
    face is part of, or None if it isn't part of any detecting face or volume.

    Used to populate the detector_faces dataset of the NXoff_geometry class.
    See http://download.nexusformat.org/sphinx/classes/base_classes/NXoff_geometry.html
    """

    pixel_ids = attr.ib(list)


@attr.s
class SinglePixelId(PixelData):
    """Pixel data for components that only have a single detector ID"""

    pixel_id = attr.ib(int)


@attr.s
class Transformation:
    name = attr.ib(str)


@attr.s
class Rotation(Transformation):
    axis = attr.ib(
        factory=lambda: Vector(0, 0, 1), type=Vector, validator=validate_nonzero_vector
    )
    angle = attr.ib(default=0)


@attr.s
class Translation(Transformation):
    vector = attr.ib(factory=lambda: Vector(0, 0, 0), type=Vector)


@unique
class ComponentType(Enum):
    SAMPLE = "Sample"
    DETECTOR = "Detector"
    MONITOR = "Monitor"
    SOURCE = "Source"
    SLIT = "Slit"
    MODERATOR = "Moderator"
    DISK_CHOPPER = "Disk Chopper"

    @classmethod
    def values(cls):
        return [item.value for item in cls]


@attr.s
class Component:
    """Components of an instrument"""

    component_type = attr.ib(ComponentType)
    name = attr.ib(str)
    description = attr.ib(default="", type=str)
    transform_parent = attr.ib(default=None, type=object)
    dependent_transform = attr.ib(default=None, type=Transformation)
    transforms = attr.ib(
        factory=list,
        type=List[Transformation]
    )
    geometry = attr.ib(default=None, type=Geometry)
    pixel_data = attr.ib(default=None, type=PixelData)
