from nexus_constructor.geometry import NoShapeGeometry, CylindricalGeometry, OFFGeometry
from nexus_constructor.geometry.no_shape_geometry import OFFCube
from PySide2.QtGui import QVector3D, QMatrix4x4
from math import acos, degrees


def test_GIVEN_nothing_WHEN_constructing_NoShapeGeometry_THEN_off_geometry_returns_offcube():
    geom = NoShapeGeometry()
    assert geom.off_geometry == OFFCube


def test_GIVEN_nothing_WHEN_constructing_NoShapeGeometry_THEN_geometry_str_is_none():
    geom = NoShapeGeometry()
    assert geom.geometry_str == "None"


def test_GIVEN_nothing_WHEN_constructing_CylindricalGeometry_THEN_geometry_str_is_correct():
    geom = CylindricalGeometry()
    assert geom.geometry_str == "Cylinder"


def test_GIVEN_nothing_WHEN_constructing_OFFGeometry_THEN_geometry_str_is_correct():
    geom = OFFGeometry()
    assert geom.geometry_str == "OFF"


UNIT = "m"
AXIS_DIRECTION = QVector3D(1, 2, 3)
HEIGHT = 2.0
RADIUS = 1.0


def test_GIVEN_cylinder_WHEN_constructing_CylindricalGeometry_THEN_off_geometry_returns_correct_off():
    geom = CylindricalGeometry(UNIT, AXIS_DIRECTION, HEIGHT, RADIUS)

    assert geom.radius == RADIUS
    assert geom.height == HEIGHT
    assert geom.axis_direction.toTuple() == AXIS_DIRECTION.toTuple()
    assert geom.units == UNIT


def test_GIVEN_nothing_WHEN_constructing_CylindricalGeometry_THEN_rotation_matrix_is_correct():
    geom = CylindricalGeometry(UNIT, AXIS_DIRECTION, HEIGHT, RADIUS)

    default_axis = QVector3D(0, 0, 1)
    cross_product = QVector3D.crossProduct(AXIS_DIRECTION.normalized(), default_axis)
    rotate_radians = acos(
        QVector3D.dotProduct(AXIS_DIRECTION.normalized(), default_axis)
    )
    matrix = QMatrix4x4()
    matrix.rotate(degrees(rotate_radians), cross_product)
    assert geom.rotation_matrix == matrix


def test_GIVEN_faces_WHEN_calling_winding_order_on_OFF_THEN_order_is_correct():
    vertices = [
        QVector3D(0, 0, 1),
        QVector3D(0, 1, 0),
        QVector3D(0, 0, 0),
        QVector3D(0, 1, 1),
    ]

    faces = [[0, 1, 2, 3]]

    geom = OFFGeometry(vertices, faces)
    expected = [point for face in faces for point in face]

    assert expected == geom.winding_order


def test_GIVEN_faces_WHEN_calling_winding_order_indices_on_OFF_THEN_order_is_correct():
    vertices = [
        QVector3D(0, 0, 1),
        QVector3D(0, 1, 0),
        QVector3D(0, 0, 0),
        QVector3D(0, 1, 1),
    ]

    faces = [[0, 1, 2, 3]]

    geom = OFFGeometry(vertices, faces)

    expected = [0]  # only one face

    assert expected == geom.winding_order_indices


def test_GIVEN_nothing_WHEN_calling_off_geometry_on_noshapegeometry_THEN_OFFCube_is_returned():
    geom = NoShapeGeometry()
    assert geom.off_geometry == OFFCube


def test_GIVEN_off_gemetry_WHEN_calling_off_geometry_on_offGeometry_THEN_original_geometry_is_returned():
    vertices = [
        QVector3D(0, 0, 1),
        QVector3D(0, 1, 0),
        QVector3D(0, 0, 0),
        QVector3D(0, 1, 1),
    ]

    faces = [[0, 1, 2, 3]]
    geom = OFFGeometry(vertices, faces)

    assert geom.faces == faces
    assert geom.vertices == vertices
    assert geom.off_geometry == geom


def test_GIVEN_nothing_WHEN_creating_cylindricalGeometry_THEN_base_center_point_is_origin():
    geom = CylindricalGeometry(UNIT, AXIS_DIRECTION, HEIGHT, RADIUS)

    assert geom.base_center_point == QVector3D(0, 0, 0)


def test_GIVEN_nothing_WHEN_creating_cylindricalGeometry_THEN_top_center_point_is_correct():
    geom = CylindricalGeometry(UNIT, AXIS_DIRECTION, HEIGHT, RADIUS)

    assert geom.top_center_point == (AXIS_DIRECTION.normalized() * HEIGHT)


def test_GIVEN_nothing_WHEN_creating_cylindricalGeometry_THEN_base_edge_point_is_correct():
    geom = CylindricalGeometry(UNIT, AXIS_DIRECTION, HEIGHT, RADIUS)

    assert geom.base_edge_point == (QVector3D(RADIUS, 0, 0) * geom.rotation_matrix)
