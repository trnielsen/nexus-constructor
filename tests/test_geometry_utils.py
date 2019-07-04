from nexus_constructor.geometry.utils import (
    get_an_orthogonal_unit_vector,
    validate_nonzero_qvector,
)
from PySide2.QtGui import QVector3D
from pytest import raises, fail


def test_zero_qvector_raises_error_when_validated():
    test_vector = QVector3D(0, 0, 0)
    with raises(ValueError):
        validate_nonzero_qvector(test_vector)


def test_non_zero_qvector_does_not_raise_error_when_validated():
    test_vector = QVector3D(1, 0, 0)
    try:
        validate_nonzero_qvector(test_vector)
    except ValueError:
        fail("Expected non-zero vector to pass validation")
