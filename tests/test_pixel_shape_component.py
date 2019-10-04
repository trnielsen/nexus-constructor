from nexus_constructor.component.pixel_shape_component import PixelShapeComponent
from nexus_constructor.nexus import nexus_wrapper as nx
import numpy as np


def test_GIVEN_a_PixelShapeComponent_WHEN_calling_get_shape_THEN_shape_and_transformations_are_returned():
    wrapper = nx.NexusWrapper("file_with_detector")
    detector_group = wrapper.create_nx_group(
        "detector", "NXdetector", wrapper.instrument
    )
    shape_group = wrapper.create_nx_group(
        "pixel_shape", "NXoff_geometry", detector_group
    )

    # Populate shape group
    vertices = [
        [-0.05, -0.05, 0.0],
        [0.05, -0.05, 0.0],
        [0.05, 0.05, 0.0],
        [-0.05, 0.05, 0.0],
    ]
    faces = [0]
    winding_order = [0, 1, 2, 3]

    wrapper.set_field_value(shape_group, "vertices", vertices)
    wrapper.set_field_value(shape_group, "winding_order", winding_order)
    wrapper.set_field_value(shape_group, "faces", faces)

    # Add pixel offsets to detector group
    x_offsets = np.array([[-0.05, 0.05], [-0.05, 0.05]])
    y_offsets = np.array([[-0.05, -0.05], [0.05, 0.05]])

    wrapper.set_field_value(detector_group, "x_pixel_offset", x_offsets)
    wrapper.set_field_value(detector_group, "x_pixel_offset", y_offsets)

    pixel_component = PixelShapeComponent(wrapper, detector_group)
    assert isinstance(pixel_component, PixelShapeComponent)
    shape, transformations = pixel_component.get_shape()

    assert np.array_equal(shape.vertices, vertices)
    assert np.array_equal(shape.faces, faces)

    assert (
        len(transformations) == x_offsets.size()
    ), "Expected one transformation per pixel offset"
