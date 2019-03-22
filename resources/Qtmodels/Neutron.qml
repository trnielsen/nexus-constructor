import QtQuick 2.11
import Qt3D.Core 2.0
import Qt3D.Extras 2.0

Entity {
    property real yOffset: 0.0
    property real xOffset: 0.0
    property real timespanOffset: 0.0
    property real zLength: -40.0
    property PhongMaterial material
    property SphereMesh mesh
    components: [ mesh, material, neutronTransform ]

    Transform {
        id: neutronTransform
        property real distance: 0.0
        matrix: {
            var m = Qt.matrix4x4();
            m.translate(Qt.vector3d(xOffset, yOffset, distance));
            m.scale(0.1)
            return m;
        }
    }

    NumberAnimation {
        target: neutronTransform
        property: "distance"
        duration: 500 + timespanOffset
        from: zLength
        to: 0

        loops: Animation.Infinite
        running: true
    }
}