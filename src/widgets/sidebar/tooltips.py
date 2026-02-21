"""Premium toolkit components for Sidebar and Overlays."""

from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QApplication
from PySide6.QtCore import Qt, QEvent, QTimer, QPoint, QObject, QPropertyAnimation
from PySide6.QtGui import QColor, QFontMetrics

class PremiumToolTip(QWidget):
    """Animated, premium-looking tooltip with shadow room in margins."""
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.margin = 15
        layout = QVBoxLayout(self)
        layout.setContentsMargins(self.margin, self.margin, self.margin, self.margin)
        
        self.label = QLabel(text)
        self.label.setStyleSheet("""
            QLabel {
                background-color: #121212;
                color: #ffffff;
                border: 1px solid #333333;
                border-radius: 6px;
                padding: 8px 14px;
                font-family: 'Segoe UI', system-ui;
                font-size: 11px;
                font-weight: 600;
            }
        """)
        layout.addWidget(self.label)
        
        from PySide6.QtWidgets import QGraphicsDropShadowEffect
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(12)
        self.shadow.setColor(QColor(0, 0, 0, 180))
        self.shadow.setOffset(0, 4)
        self.label.setGraphicsEffect(self.shadow)
        
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(150)
        
    def setText(self, text):
        self.label.setText(text)

    def show_at(self, pos):
        self.move(pos.x() - self.margin, pos.y() - self.margin)
        self.setWindowOpacity(0.0)
        self.show()
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.start()

class ToolTipManager:
    """Singleton manager for the premium tooltip to ensure universal behavior."""
    _instance = None
    _tooltip = None

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = ToolTipManager()
        return cls._instance

    def show(self, text, obj):
        if not self._tooltip:
            self._tooltip = PremiumToolTip(text)
        else:
            self._tooltip.setText(text)
            
        self._tooltip.adjustSize()
        self._tooltip.label.adjustSize()
        
        # Target position calculation
        global_pos = obj.mapToGlobal(QPoint(0, 0))
        screen = QApplication.screenAt(global_pos) or QApplication.primaryScreen()
        s_rect = screen.availableGeometry()
        
        # Center horizontally relative to object
        x = global_pos.x() + (obj.width() - self._tooltip.label.width()) // 2
        y = global_pos.y() + obj.height() + 8 # Padding below
        
        # Keep within screen bounds
        tooltip_w = self._tooltip.label.width()
        tooltip_h = self._tooltip.label.height()
        
        x = max(s_rect.left() + 10, min(s_rect.right() - tooltip_w - 10, x))
        
        # Flip to top if it clips the bottom
        if y + tooltip_h > s_rect.bottom() - 10:
            y = global_pos.y() - tooltip_h - 12
            
        self._tooltip.show_at(QPoint(x, y))

    def hide(self):
        if self._tooltip:
            # We don't use the animation for hiding to feel more responsive/standard
            self._tooltip.hide()

class ToolTipFilter(QObject):
    """Event filter that delegates to the Universal ToolTipManager."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.manager = ToolTipManager.instance()
        self._active_obj = None

    def eventFilter(self, watched, event):
        if not watched:
            return False
            
        # Intercept the standard ToolTip event
        if event.type() == QEvent.ToolTip:
            text = watched.toolTip()
            if text:
                self._active_obj = watched
                self.manager.show(text, watched)
                return True # Stop standard Qt tooltip
            return False

        # Hide when moving mouse, leaving, or clicking
        if event.type() in (QEvent.Leave, QEvent.MouseButtonPress, QEvent.Wheel):
            if self._active_obj == watched:
                self.manager.hide()
                self._active_obj = None
                
        return super().eventFilter(watched, event)
