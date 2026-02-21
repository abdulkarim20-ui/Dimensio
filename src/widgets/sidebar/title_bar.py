"""Custom title bar for the sidebar."""

import os
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QIcon, QPixmap
from ...config import Config

class TitleBar(QFrame):
    """Custom title bar with logo, title, minimize and close buttons."""
    
    minimize_clicked = Signal()
    close_clicked = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(32)
        self.setStyleSheet("background-color: #000; border-top-left-radius: 4px; border-top-right-radius: 4px;")
        
        self._init_ui()
        
    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 8, 0)
        
        # Logo
        self.lbl_logo = QLabel()
        self.lbl_logo.setFixedSize(20, 20)
        app_logo_path = Config.APP_LOGO
        if os.path.exists(app_logo_path):
            pixmap = QPixmap(app_logo_path)
            self.lbl_logo.setPixmap(pixmap.scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        layout.addWidget(self.lbl_logo)

        # Title Text
        self.lbl_title_text = QLabel("Dimensio")
        self.lbl_title_text.setStyleSheet("color: #fff; font-weight: 900; font-size: 10px; letter-spacing: 1.5px;")
        layout.addWidget(self.lbl_title_text)
        
        layout.addStretch()

        # Minimize Button
        self.btn_minimize = QPushButton()
        self.btn_minimize.setFixedSize(20, 20)
        icon_minimize_path = os.path.join(Config.ICONS_DIR, "minimize.svg")
        if os.path.exists(icon_minimize_path):
            self.btn_minimize.setIcon(QIcon(icon_minimize_path))
            self.btn_minimize.setIconSize(QSize(14, 14))
        self.btn_minimize.setStyleSheet("""
            QPushButton { background: transparent; border: none; } 
            QPushButton:hover { background: rgba(255,255,255,10); }
        """)
        self.btn_minimize.clicked.connect(self.minimize_clicked.emit)
        layout.addWidget(self.btn_minimize)

        # Close Button
        self.btn_close = QPushButton()
        self.btn_close.setFixedSize(20, 20)
        icon_close_path = os.path.join(Config.ICONS_DIR, "close.svg")
        if os.path.exists(icon_close_path):
            self.btn_close.setIcon(QIcon(icon_close_path))
            self.btn_close.setIconSize(QSize(14, 14))
        self.btn_close.setStyleSheet("""
            QPushButton { background: transparent; border: none; } 
            QPushButton:hover { background: #e74c3c; }
        """)
        self.btn_close.clicked.connect(self.close_clicked.emit)
        layout.addWidget(self.btn_close)
