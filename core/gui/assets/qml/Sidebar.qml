// Cosmic OS Sidebar QML
// Alternative QML implementation for KDE Plasma integration

import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Window 2.15
import QtGraphicalEffects 1.15

Window {
    id: sidebar
    
    property bool sidebarVisible: false
    property int sidebarWidth: 420
    
    width: sidebarWidth
    height: Screen.height
    x: sidebarVisible ? Screen.width - sidebarWidth : Screen.width
    y: 0
    
    flags: Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
    color: "transparent"
    visible: true
    
    Behavior on x {
        NumberAnimation {
            duration: 200
            easing.type: Easing.OutCubic
        }
    }
    
    // Background
    Rectangle {
        id: background
        anchors.fill: parent
        color: "#1E1E1E"
        opacity: 0.95
        
        Rectangle {
            width: 1
            height: parent.height
            color: "#3D3D3D"
            anchors.left: parent.left
        }
    }
    
    // Content
    ColumnLayout {
        anchors.fill: parent
        spacing: 0
        
        // Header
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 56
            color: "#252525"
            
            Rectangle {
                width: parent.width
                height: 1
                anchors.bottom: parent.bottom
                color: "#3D3D3D"
            }
            
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 16
                anchors.rightMargin: 16
                
                Text {
                    text: "✨ Cosmic AI"
                    font.pixelSize: 16
                    font.bold: true
                    color: "#E0E0E0"
                }
                
                Item { Layout.fillWidth: true }
                
                Button {
                    text: "⚙"
                    flat: true
                    font.pixelSize: 18
                    contentItem: Text {
                        text: parent.text
                        color: parent.hovered ? "#E0E0E0" : "#A0A0A0"
                        font: parent.font
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    background: Rectangle { color: "transparent" }
                }
                
                Button {
                    text: "✕"
                    flat: true
                    font.pixelSize: 16
                    contentItem: Text {
                        text: parent.text
                        color: parent.hovered ? "#FF5252" : "#A0A0A0"
                        font: parent.font
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    background: Rectangle { color: "transparent" }
                    onClicked: sidebar.sidebarVisible = false
                }
            }
        }
        
        // Chat area
        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            
            ListView {
                id: messageList
                anchors.fill: parent
                anchors.margins: 16
                spacing: 12
                
                model: ListModel {
                    id: messageModel
                }
                
                delegate: MessageBubble {
                    text: model.text
                    isUser: model.isUser
                    width: messageList.width
                }
            }
        }
        
        // Input area
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 64
            color: "#252525"
            
            Rectangle {
                width: parent.width
                height: 1
                color: "#3D3D3D"
            }
            
            RowLayout {
                anchors.fill: parent
                anchors.margins: 12
                spacing: 12
                
                TextField {
                    id: inputField
                    Layout.fillWidth: true
                    placeholderText: "Ask Cosmic AI..."
                    font.pixelSize: 14
                    color: "#E0E0E0"
                    
                    background: Rectangle {
                        color: "#3D3D3D"
                        radius: 20
                        border.color: inputField.focus ? "#0078D4" : "#4D4D4D"
                        border.width: 1
                    }
                    
                    leftPadding: 16
                    rightPadding: 16
                    topPadding: 10
                    bottomPadding: 10
                    
                    Keys.onReturnPressed: sendMessage()
                }
                
                Button {
                    Layout.preferredWidth: 40
                    Layout.preferredHeight: 40
                    text: "➤"
                    font.pixelSize: 16
                    
                    contentItem: Text {
                        text: parent.text
                        color: "white"
                        font: parent.font
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    
                    background: Rectangle {
                        color: parent.pressed ? "#006CBD" : (parent.hovered ? "#1084D8" : "#0078D4")
                        radius: 20
                    }
                    
                    onClicked: sendMessage()
                }
            }
        }
    }
    
    function sendMessage() {
        var text = inputField.text.trim()
        if (text.length === 0) return
        
        messageModel.append({
            "text": text,
            "isUser": true
        })
        
        inputField.text = ""
        
        // TODO: Send to AI backend
        // For now, echo response
        Qt.callLater(function() {
            messageModel.append({
                "text": "Processing: " + text,
                "isUser": false
            })
        })
    }
    
    function toggle() {
        sidebarVisible = !sidebarVisible
    }
    
    // Global shortcut handler (needs to be connected from C++ or Python)
    Shortcut {
        sequence: "Ctrl+Space"
        onActivated: toggle()
    }
}
