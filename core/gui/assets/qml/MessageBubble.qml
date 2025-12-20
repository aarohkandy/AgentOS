// Message Bubble Component for Cosmic OS Sidebar

import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Item {
    id: root
    
    property string text: ""
    property bool isUser: true
    
    height: bubble.height
    
    Rectangle {
        id: bubble
        
        width: Math.min(implicitWidth, parent.width * 0.8)
        height: contentText.height + 20
        
        anchors.right: isUser ? parent.right : undefined
        anchors.left: isUser ? undefined : parent.left
        anchors.rightMargin: isUser ? 0 : 40
        anchors.leftMargin: isUser ? 40 : 0
        
        color: isUser ? "#0078D4" : "#2D2D2D"
        radius: 12
        
        property real implicitWidth: contentText.implicitWidth + 24
        
        Text {
            id: contentText
            text: root.text
            color: isUser ? "white" : "#E0E0E0"
            font.pixelSize: 14
            wrapMode: Text.Wrap
            width: Math.min(implicitWidth, parent.parent.width * 0.8 - 24)
            
            anchors.centerIn: parent
            anchors.margins: 12
        }
    }
}
