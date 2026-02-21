"""File menu and toggle components."""

import os
from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QFrame, QPushButton
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, Property, QEasingCurve, QSize
from PySide6.QtGui import QPainter, QPainterPath, QColor, QIcon
from ..config import Config


class ToggleSwitch(QWidget):
    """A premium looking toggle switch."""
    toggled = Signal(bool)

    def __init__(self, parent=None, active_color="#2ecc71"):
        super().__init__(parent)
        self.setFixedSize(34, 18)
        self._active = False
        self._active_color = active_color
        self._circle_pos = 2
        
        self._anim = QPropertyAnimation(self, b"circle_pos")
        self._anim.setDuration(200)
        self._anim.setEasingCurve(QEasingCurve.InOutQuad)

    @Property(float)
    def circle_pos(self):
        return self._circle_pos

    @circle_pos.setter
    def circle_pos(self, pos):
        self._circle_pos = pos
        self.update()

    def set_active(self, active):
        if self._active == active:
            return
        self._active = active
        self._anim.setEndValue(18 if active else 2)
        self._anim.start()
        self.toggled.emit(active)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.set_active(not self._active)
            event.accept()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw background
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), self.height()/2, self.height()/2)
        
        bg_color = QColor(self._active_color) if self._active else QColor("#333333")
        painter.fillPath(path, bg_color)
        
        # Draw circle
        painter.setBrush(QColor("white"))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(self._circle_pos, 2, 14, 14)


class FileMenu(QFrame):
    """Custom dropdown menu for file operations (Save/Import)."""
    
    new_requested = Signal()
    save_requested = Signal()
    import_requested = Signal()

    def __init__(self, parent=None, theme_color="#ffffff"):
        super().__init__(parent)
        self.theme_color = theme_color
        
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self._init_ui()

    def _init_ui(self):
        self.container = QFrame(self)
        self.container.setObjectName("MenuContainer")
        self.container.setStyleSheet(f"""
            QFrame#MenuContainer {{
                background-color: #1a1a1a;
                border: 1px solid #454545;
                border-radius: 4px;
            }}
            QPushButton {{
                background: transparent;
                border: none;
                color: white;
                text-align: left;
                padding: 6px 12px;
                font-family: 'Segoe UI';
                font-size: 11px;
                border-radius: 2px;
            }}
            QPushButton:hover {{
                background: rgba(255, 255, 255, 0.1);
            }}
        """)
        
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        # New Option
        self.btn_new = QPushButton()
        self.btn_new.setFixedHeight(28)
        new_layout = QHBoxLayout(self.btn_new)
        new_layout.setContentsMargins(12, 0, 8, 0)
        
        lbl_new_text = QLabel("New Design")
        lbl_new_text.setStyleSheet("color: white; font-size: 11px; background: transparent;")
        lbl_new_shortcut = QLabel("Ctrl+Shift+N")
        lbl_new_shortcut.setStyleSheet("color: #666; font-size: 10px; background: transparent;")
        
        new_layout.addWidget(lbl_new_text)
        new_layout.addStretch()
        new_layout.addWidget(lbl_new_shortcut)
        
        layout.addWidget(self.btn_new)
        self.btn_new.clicked.connect(self._on_new_clicked)

        # Save Option
        self.btn_save = QPushButton()
        self.btn_save.setFixedHeight(28)
        save_layout = QHBoxLayout(self.btn_save)
        save_layout.setContentsMargins(12, 0, 8, 0)
        
        lbl_save_text = QLabel("Save Design")
        lbl_save_text.setStyleSheet("color: white; font-size: 11px; background: transparent;")
        lbl_save_shortcut = QLabel("Ctrl+S")
        lbl_save_shortcut.setStyleSheet("color: #666; font-size: 10px; background: transparent;")
        
        save_layout.addWidget(lbl_save_text)
        save_layout.addStretch()
        save_layout.addWidget(lbl_save_shortcut)
        
        layout.addWidget(self.btn_save)
        self.btn_save.clicked.connect(self._on_save_clicked)

        # Import Option (Renamed to Open)
        self.btn_import = QPushButton()
        self.btn_import.setFixedHeight(28)
        import_layout = QHBoxLayout(self.btn_import)
        import_layout.setContentsMargins(12, 0, 8, 0)
        
        lbl_import_text = QLabel("Open Design")
        lbl_import_text.setStyleSheet("color: white; font-size: 11px; background: transparent;")
        lbl_import_shortcut = QLabel("Ctrl+O")
        lbl_import_shortcut.setStyleSheet("color: #666; font-size: 10px; background: transparent;")
        
        import_layout.addWidget(lbl_import_text)
        import_layout.addStretch()
        import_layout.addWidget(lbl_import_shortcut)
        
        layout.addWidget(self.btn_import)
        self.btn_import.clicked.connect(self._on_import_clicked)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.container)
        self.setFixedSize(160, 96)

    def _on_new_clicked(self):
        self.new_requested.emit()
        self.hide()

    def _on_save_clicked(self):
        self.save_requested.emit()
        self.hide()

    def _on_import_clicked(self):
        self.import_requested.emit()
        self.hide()
