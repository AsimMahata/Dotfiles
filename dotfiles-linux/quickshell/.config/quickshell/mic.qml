import QtQuick
import Quickshell
import Quickshell.Widgets

PopupWindow {
    id: micPopup
    visible: false
    width: 260
    height: 90
    layer: Layer.Top

    function toggle() {
        visible = !visible
    }

    Rectangle {
        anchors.fill: parent
        radius: 12
        color: "#1e1e2e"

        Row {
            anchors.centerIn: parent
            spacing: 12

            Text {
                text: ""
                font.pixelSize: 24
                color: "white"
            }

            Slider {
                width: 160
                from: 0
                to: 100

                onMoved: {
                    Quickshell.exec(
                        "pactl set-source-volume @DEFAULT_SOURCE@ " +
                        Math.round(value) + "%"
                    )
                }
            }
        }
    }
}
