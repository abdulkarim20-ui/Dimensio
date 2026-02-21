"""Positioning controls for frames."""

import os
from PySide6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QPushButton, QFrame
from PySide6.QtCore import Qt, Signal, QSize, QTimer
from PySide6.QtGui import QIcon
from ...config import Config

class PositionControl(QWidget):
    """Directional pad for moving frames with hold-to-repeat support."""
    move_requested = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(180)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        
        grid = QGridLayout()
        grid.setSpacing(8)
        
        self.btn_up = self._create_btn("arrow-up.svg", "up")
        self.btn_down = self._create_btn("arrow-down.svg", "down")
        self.btn_left = self._create_btn("arrow-left.svg", "left")
        self.btn_right = self._create_btn("arrow-right.svg", "right")
        
        grid.addWidget(self.btn_up, 0, 1)
        grid.addWidget(self.btn_left, 1, 0)
        grid.addWidget(self.btn_right, 1, 2)
        grid.addWidget(self.btn_down, 2, 1)
        
        dot = QFrame()
        dot.setFixedSize(6, 6)
        dot.setStyleSheet("background: #094771; border-radius: 3px; opacity: 0.8;")
        grid.addWidget(dot, 1, 1, Qt.AlignCenter)
        
        layout.addLayout(grid)
        
        self.move_timer = QTimer()
        self.move_timer.timeout.connect(self._on_move_timer)
        self.current_direction = None
        
    def _create_btn(self, icon_name, direction):
        btn = QPushButton()
        btn.setFixedSize(38, 38)
        path = os.path.join(Config.ICONS_DIR, icon_name)
        if os.path.exists(path):
            btn.setIcon(QIcon(path))
            btn.setIconSize(QSize(20, 20))
        
        btn.setStyleSheet("""
            QPushButton { 
                background: #252526; 
                border: 1px solid #454545; 
                border-radius: 4px; 
            } 
            QPushButton:hover { 
                background: #333333; 
                border-color: #094771; 
            } 
            QPushButton:pressed { 
                background: #094771; 
            }
        """)
        btn.setFocusPolicy(Qt.NoFocus)
        
        btn.pressed.connect(lambda d=direction: self._on_pressed(d))
        btn.released.connect(self._on_released)
        return btn
        
    def _on_pressed(self, direction):
        self.current_direction = direction
        self.move_requested.emit(direction)
        self.move_timer.start(50)
        
    def _on_released(self):
        self.move_timer.stop()
        self.current_direction = None
        
    def _on_move_timer(self):
        if self.current_direction:
            self.move_requested.emit(self.current_direction)
