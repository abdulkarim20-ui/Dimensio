"""Sidebar-specific input components."""

from PySide6.QtWidgets import QLineEdit, QApplication
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIntValidator

class EditableLabel(QLineEdit):
    """A label that becomes editable when clicked or focused."""
    value_changed = Signal(int)
    
    def __init__(self, text="0", parent=None):
        super().__init__(text, parent)
        self.setValidator(QIntValidator(0, 10000))
        self.setFixedWidth(50)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("""
            QLineEdit {
                background: transparent;
                border: none;
                color: #ffffff;
                font-family: 'Segoe UI';
                font-size: 18px;
                font-weight: 800;
                padding: 0px;
            }
            QLineEdit:hover {
                background: rgba(255, 255, 255, 10);
                border-radius: 2px;
            }
            QLineEdit:focus {
                background: #000000;
                border: 1px solid #ffffff;
                border-radius: 2px;
            }
        """)
        self.returnPressed.connect(self._on_return)
        self.editingFinished.connect(self._on_return)

    def _on_return(self):
        try:
            val = int(self.text())
            self.value_changed.emit(val)
        except:
            pass
        self.clearFocus()

    def wheelEvent(self, event):
        delta = 1 if event.angleDelta().y() > 0 else -1
        if QApplication.keyboardModifiers() & Qt.ShiftModifier:
            delta *= 10
            
        try:
            val = int(self.text()) + delta
            final_val = max(0, val)
            self.setText(str(final_val))
            self.value_changed.emit(final_val)
        except:
            pass
        event.accept()

class FigmaInput(QLineEdit):
    """Figma-style numeric input field."""
    value_changed = Signal(int)
    
    def __init__(self, text="0", parent=None):
        super().__init__(text, parent)
        self.setValidator(QIntValidator(0, 500))
        self.setFixedWidth(42)
        self.setFixedHeight(24)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("""
            QLineEdit {
                background: #111;
                border: 1px solid #2a2a2a;
                border-radius: 3px;
                color: #aaa;
                font-family: 'Segoe UI', system-ui;
                font-size: 10px;
                font-weight: 700;
            }
            QLineEdit:hover {
                border-color: #444;
                color: #fff;
            }
            QLineEdit:focus {
                border-color: #2ecc71;
                background: #000;
                color: #fff;
            }
        """)
        self.returnPressed.connect(self._on_return)
        self.editingFinished.connect(self._on_return)

    def _on_return(self):
        try:
            val = int(self.text())
            self.value_changed.emit(val)
        except:
            pass
        self.clearFocus()

    def wheelEvent(self, event):
        delta = 1 if event.angleDelta().y() > 0 else -1
        if QApplication.keyboardModifiers() & Qt.ShiftModifier:
            delta *= 10
            
        try:
            val = int(self.text()) + delta
            final_val = max(0, min(500, val))
            self.setText(str(final_val))
            self.value_changed.emit(final_val)
        except:
            pass
        event.accept()
