"""Custom status bar for the sidebar."""

import os
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, QSize, Signal, QTimer
from PySide6.QtGui import QIcon
from ...config import Config

class StatusBar(QFrame):
    """Custom status bar with frame counter and action buttons."""
    
    add_frame_requested = Signal()
    delete_frame_requested = Signal()
    
    def __init__(self, tooltip_filter=None, parent=None):
        super().__init__(parent)
        self.tooltip_filter = tooltip_filter
        self.setFixedHeight(32) # Set same height as TitleBar (32px)
        self.setStyleSheet("""
            QFrame { 
                background-color: #0a0a0a; 
                border-bottom-left-radius: 4px; 
                border-bottom-right-radius: 4px; 
            }
        """)

        
        self.copy_timer = QTimer()
        self.copy_timer.setSingleShot(True)
        self.copy_timer.timeout.connect(self.reset_status)
        
        self.frame_count = 0
        self._init_ui()
        
    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 8, 0)
        layout.setSpacing(0) # Minimal tight spacing
        
        # 1. Project Name (Left)
        self.lbl_project = QLabel("project.dio *")
        self.lbl_project.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.lbl_project.setStyleSheet("""
            color: #888; 
            font-weight: 600; 
            font-size: 11px; 
            font-family: 'Segoe UI'; 
            letter-spacing: 0px; 
            padding-bottom: 1px;
        """)
        layout.addWidget(self.lbl_project)
        
        layout.addStretch()

        # 2. Frame Count (Shifted near buttons, Fn format)
        self.lbl_status = QLabel("F0")
        self.lbl_status.setToolTip("Total Frames Currently Active")
        self.lbl_status.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.lbl_status.setStyleSheet("""
            color: #666; 
            font-weight: 700; 
            font-size: 11px; 
            font-family: 'Segoe UI'; 
            letter-spacing: 0.5px; 
            padding-bottom: 1px;
        """)
        if self.tooltip_filter:
            self.lbl_status.installEventFilter(self.tooltip_filter)
        layout.addWidget(self.lbl_status)
        
        layout.addSpacing(6) # Spacing between text and buttons

        # 3. Action Buttons (Tight grouping)
        self.btn_add_layer = QPushButton()
        self._set_mini_button_style(
            self.btn_add_layer, 
            os.path.join(Config.ICONS_DIR, "add_frame.svg"), 
            "Create New Frame (Ctrl+N)"
        )
        self.btn_add_layer.clicked.connect(self.add_frame_requested.emit)
        layout.addWidget(self.btn_add_layer)
        
        # No extra spacing here for tightest look
        self.btn_delete_layer = QPushButton()
        self._set_mini_button_style(
            self.btn_delete_layer, 
            os.path.join(Config.ICONS_DIR, "delete.svg"), 
            "Delete Selected Frame"
        )
        self.btn_delete_layer.clicked.connect(self.delete_frame_requested.emit)
        layout.addWidget(self.btn_delete_layer)

    def _set_mini_button_style(self, btn, icon_path, tooltip):
        btn.setFixedSize(28, 28)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setToolTip(tooltip)
        if os.path.exists(icon_path):
            btn.setIcon(QIcon(icon_path))
            btn.setIconSize(QSize(16, 16))
        btn.setStyleSheet("""
            QPushButton { 
                background: transparent; 
                border: none; 
            } 
            QPushButton:hover { 
                background: rgba(255, 255, 255, 0.1); 
                border-radius: 4px; 
            }
        """)

        if self.tooltip_filter:
            btn.installEventFilter(self.tooltip_filter)

    def update_count(self, count):
        self.frame_count = count
        if not self.copy_timer.isActive():
            self.reset_status()

    def show_copied_status(self):
        self.lbl_status.setText("COPIED")
        self.lbl_status.setStyleSheet("""
            color: #2ecc71; 
            font-weight: 700; 
            font-size: 11px; 
            font-family: 'Segoe UI'; 
            letter-spacing: 0.5px; 
            padding-bottom: 1px;
        """)
        self.copy_timer.start(2000)

    def reset_status(self):
        self.lbl_status.setText(f"F{self.frame_count}")
        self.lbl_status.setStyleSheet("""
            color: #666; 
            font-weight: 700; 
            font-size: 11px; 
            font-family: 'Segoe UI'; 
            letter-spacing: 0.5px; 
            padding-bottom: 1px;
        """)

    def set_project_name(self, name, is_dirty=True):
        suffix = " *" if is_dirty else ""
        self.lbl_project.setText(f"{name}{suffix}")
