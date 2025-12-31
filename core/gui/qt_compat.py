"""
Qt Compatibility Layer
Supports both PyQt6 and PySide6 for maximum compatibility.
"""

import sys

# Try PyQt6 first (preferred)
try:
    from PyQt6.QtWidgets import (
        QApplication, QWidget, QVBoxLayout, QHBoxLayout,
        QTextEdit, QLineEdit, QPushButton, QLabel,
        QScrollArea, QFrame, QSizePolicy, QGraphicsOpacityEffect
    )
    from PyQt6.QtCore import (
        Qt, QPropertyAnimation, QEasingCurve, QThread, 
        pyqtSignal, QTimer, QPoint, QRect
    )
    from PyQt6.QtGui import (
        QFont, QColor, QPalette, QKeySequence, QShortcut,
        QScreen, QPainter, QBrush, QPen
    )
    QT_BINDING = "PyQt6"
    Signal = pyqtSignal
except ImportError:
    # Fallback to PySide6
    try:
        from PySide6.QtWidgets import (
            QApplication, QWidget, QVBoxLayout, QHBoxLayout,
            QTextEdit, QLineEdit, QPushButton, QLabel,
            QScrollArea, QFrame, QSizePolicy, QGraphicsOpacityEffect
        )
        from PySide6.QtCore import (
            Qt, QPropertyAnimation, QEasingCurve, QThread, 
            Signal, QTimer, QPoint, QRect
        )
        from PySide6.QtGui import (
            QFont, QColor, QPalette, QKeySequence, QShortcut,
            QScreen, QPainter, QBrush, QPen
        )
        QT_BINDING = "PySide6"
    except ImportError:
        raise ImportError(
            "Neither PyQt6 nor PySide6 is installed. "
            "Please install one: pip install PyQt6 or pip install PySide6"
        )

__all__ = [
    'QApplication', 'QWidget', 'QVBoxLayout', 'QHBoxLayout',
    'QTextEdit', 'QLineEdit', 'QPushButton', 'QLabel',
    'QScrollArea', 'QFrame', 'QSizePolicy', 'QGraphicsOpacityEffect',
    'Qt', 'QPropertyAnimation', 'QEasingCurve', 'QThread',
    'Signal', 'QTimer', 'QPoint', 'QRect',
    'QFont', 'QColor', 'QPalette', 'QKeySequence', 'QShortcut',
    'QScreen', 'QPainter', 'QBrush', 'QPen',
    'QT_BINDING'
]




