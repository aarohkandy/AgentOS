"""
iOS-Quality Animation Utilities
Perfect timing, smooth easing, instant feel
"""

from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QParallelAnimationGroup, QSequentialAnimationGroup
from PyQt6.QtWidgets import QGraphicsOpacityEffect, QGraphicsDropShadowEffect
from PyQt6.QtGui import QColor

def create_slide_animation(widget, start_pos, end_pos, duration=280):
    """Create perfect iOS-style slide animation."""
    anim = QPropertyAnimation(widget, b"pos")
    anim.setDuration(duration)
    anim.setStartValue(start_pos)
    anim.setEndValue(end_pos)
    anim.setEasingCurve(QEasingCurve.Type.OutCubic)  # Perfect iOS easing
    return anim

def create_fade_animation(effect, start_opacity, end_opacity, duration=280):
    """Create perfect iOS-style fade animation."""
    anim = QPropertyAnimation(effect, b"opacity")
    anim.setDuration(duration)
    anim.setStartValue(start_opacity)
    anim.setEndValue(end_opacity)
    anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
    return anim

def create_message_appear_animation(widget, duration=200):
    """Create smooth message appearance animation."""
    effect = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(effect)
    effect.setOpacity(0.0)
    
    anim = QPropertyAnimation(effect, b"opacity")
    anim.setDuration(duration)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(QEasingCurve.Type.OutCubic)
    
    return anim, effect

def create_shadow_effect(blur_radius=8, color=QColor(0, 0, 0, 100), offset=(0, 2)):
    """Create perfect iOS-style shadow."""
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(blur_radius)
    shadow.setColor(color)
    shadow.setOffset(offset[0], offset[1])
    return shadow

def create_button_shadow():
    """Create perfect button shadow."""
    return create_shadow_effect(
        blur_radius=8,
        color=QColor(0, 122, 255, 80),
        offset=(0, 2)
    )

def create_message_shadow(is_user=True):
    """Create perfect message bubble shadow."""
    if is_user:
        return create_shadow_effect(
            blur_radius=8,
            color=QColor(0, 122, 255, 60),
            offset=(0, 2)
        )
    else:
        return create_shadow_effect(
            blur_radius=6,
            color=QColor(0, 0, 0, 40),
            offset=(0, 1)
        )




