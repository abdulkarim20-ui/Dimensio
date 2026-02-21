"""VS Code inspired context menu for layer items."""

from PySide6.QtWidgets import QMenu, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QColor, QIcon, QAction

class PremiumContextMenu(QMenu):
    """A VS Code styled context menu with standard keyboard support."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # VS Code Colors
        # Background: #252526
        # Border: #454545
        # Hover: #094771
        # Text: #cccccc
        # Shortcut: #8b8b8b
        
        self.setStyleSheet("""
            QMenu {
                background-color: #252526;
                border: 1px solid #454545;
                padding: 4px 0px;
                color: #cccccc;
                font-family: 'Segoe UI', system-ui;
                font-size: 11px;
            }
            QMenu::item {
                padding: 4px 28px 4px 22px;
                background-color: transparent;
                margin: 0px;
            }
            QMenu::item:selected {
                background-color: #094771;
                color: #ffffff;
            }
            QMenu::item:disabled {
                color: #555555;
            }
            QMenu::icon {
                padding-left: 6px;
            }
            QMenu::separator {
                height: 1px;
                background: #454545;
                margin: 4px 0px;
            }
            /* Shortcut text styling */
            QMenu::right-arrow {
                padding-right: 5px;
            }
        """)
        
        # Smooth fade animation
        self._fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self._fade_anim.setDuration(100)
        self._fade_anim.setEasingCurve(QEasingCurve.OutQuad)

    def showEvent(self, event):
        self.setWindowOpacity(0.0)
        self._fade_anim.setStartValue(0.0)
        self._fade_anim.setEndValue(1.0)
        self._fade_anim.start()
        super().showEvent(event)

    def exec_(self, pos):
        return super().exec_(pos)
