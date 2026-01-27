import QtQuick
import Quickshell

Quickshell {
    MicPopup { id: mic }

    Command {
        name: "mic"
        onTriggered: mic.visible = !mic.visible
    }
}
