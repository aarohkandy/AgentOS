// Command Plan Widget for Cosmic OS
// Shows the AI's planned actions with approve/deny buttons

import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: root
    
    property var plan: ({})
    property string description: plan.description || "Command Plan"
    property var actions: plan.plan || []
    property int estimatedTime: plan.estimated_time || 0
    
    signal approved(var plan)
    signal denied()
    
    color: "#1E1E1E"
    border.color: "#3D3D3D"
    border.width: 1
    radius: 8
    
    height: content.height + 24
    
    ColumnLayout {
        id: content
        anchors.fill: parent
        anchors.margins: 12
        spacing: 8
        
        // Header
        Text {
            text: "📋 Command Plan"
            font.pixelSize: 14
            font.bold: true
            color: "#E0E0E0"
        }
        
        // Description
        Text {
            text: description
            font.pixelSize: 12
            color: "#A0A0A0"
            wrapMode: Text.Wrap
            Layout.fillWidth: true
        }
        
        // Actions list
        Rectangle {
            Layout.fillWidth: true
            color: "#252525"
            radius: 6
            height: actionsList.height + 16
            
            Column {
                id: actionsList
                anchors.fill: parent
                anchors.margins: 8
                spacing: 4
                
                Repeater {
                    model: Math.min(actions.length, 5)
                    
                    Text {
                        text: (index + 1) + ". " + formatAction(actions[index])
                        font.pixelSize: 11
                        font.family: "monospace"
                        color: "#C0C0C0"
                    }
                }
                
                Text {
                    visible: actions.length > 5
                    text: "... and " + (actions.length - 5) + " more actions"
                    font.pixelSize: 11
                    font.italic: true
                    color: "#808080"
                }
            }
        }
        
        // Estimated time
        Text {
            visible: estimatedTime > 0
            text: "⏱️ Estimated time: " + estimatedTime + "s"
            font.pixelSize: 11
            color: "#808080"
        }
        
        // Buttons
        RowLayout {
            Layout.fillWidth: true
            spacing: 8
            
            Button {
                text: "✕ Deny"
                
                contentItem: Text {
                    text: parent.text
                    color: "white"
                    font.pixelSize: 12
                    font.bold: true
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                
                background: Rectangle {
                    color: parent.pressed ? "#C62828" : (parent.hovered ? "#E53935" : "#D32F2F")
                    radius: 6
                }
                
                padding: 8
                
                onClicked: {
                    root.denied()
                    root.destroy()
                }
            }
            
            Item { Layout.fillWidth: true }
            
            Button {
                text: "✓ Approve"
                
                contentItem: Text {
                    text: parent.text
                    color: "white"
                    font.pixelSize: 12
                    font.bold: true
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                
                background: Rectangle {
                    color: parent.pressed ? "#2E7D32" : (parent.hovered ? "#43A047" : "#388E3C")
                    radius: 6
                }
                
                padding: 8
                
                onClicked: {
                    root.approved(plan)
                    root.destroy()
                }
            }
        }
    }
    
    function formatAction(action) {
        if (!action) return "unknown"
        
        var type = action.action || "unknown"
        
        switch(type) {
            case "click":
                var loc = action.location || [0, 0]
                var target = action.target || ""
                return "click " + target + " @ (" + loc[0] + ", " + loc[1] + ")"
            case "type":
                var text = (action.text || "").substring(0, 30)
                return 'type "' + text + '"'
            case "key":
                return "press " + (action.key || "")
            case "wait":
                return "wait " + (action.seconds || 0) + "s"
            case "drag":
                return "drag operation"
            default:
                return JSON.stringify(action)
        }
    }
}
