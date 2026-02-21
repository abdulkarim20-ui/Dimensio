"""Settings dropdown menu for advanced UI options."""

import os
from PySide6.QtWidgets import QFrame, QLabel, QHBoxLayout, QVBoxLayout, QPushButton, QWidget
from PySide6.QtCore import Qt, Signal, QSize, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtGui import QIcon
from .file_menu import ToggleSwitch
from ..config import Config

class SettingsMenu(QFrame):
    """Dropdown menu for settings like Fill Overlay."""
    
    fill_toggled = Signal(bool)
    show_name_toggled = Signal(bool)
    show_size_toggled = Signal(bool)

    def __init__(self, parent=None, initial_fill=True, initial_name=True, initial_size=True):
        super().__init__(parent)
        self.initial_fill = initial_fill
        self.initial_name = initial_name
        self.initial_size = initial_size
        self._submenu_active = False
        self._current_height = 78
        
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self._anim = QPropertyAnimation(self, b"menu_height")
        self._anim.setDuration(250)
        self._anim.setEasingCurve(QEasingCurve.InOutQuad)
        self._anim.finished.connect(self._on_anim_finished)
        
        self._init_ui()

    @Property(int)
    def menu_height(self):
        return self._current_height

    @menu_height.setter
    def menu_height(self, h):
        self._current_height = h
        self.setFixedSize(160, h)

    def _init_ui(self):
        self.container = QFrame(self)
        self.container.setObjectName("MenuContainer")
        self.container.setStyleSheet("""
            QFrame#MenuContainer {
                background-color: #1a1a1a;
                border: 1px solid #454545;
                border-radius: 4px;
            }
        """)
        
        self.main_layout = QVBoxLayout(self.container)
        self.main_layout.setContentsMargins(8, 8, 8, 8)
        self.main_layout.setSpacing(10)
        
        # 1. Fill Toggle Row
        fill_row = QHBoxLayout()
        fill_row.setSpacing(12)
        lbl_fill = QLabel("FILL OVERLAY")
        lbl_fill.setStyleSheet("color: #eee; font-size: 10px; font-weight: 700; font-family: 'Segoe UI'; letter-spacing: 0.5px;")
        self.toggle_fill = ToggleSwitch(active_color="#cab2f2")
        self.toggle_fill.set_active(self.initial_fill)
        self.toggle_fill.toggled.connect(self.fill_toggled.emit)
        fill_row.addWidget(lbl_fill)
        fill_row.addStretch()
        fill_row.addWidget(self.toggle_fill)
        self.main_layout.addLayout(fill_row)

        # 2. Show Info Row with Arrow
        info_row = QHBoxLayout()
        lbl_info = QLabel("SHOW INFO")
        lbl_info.setStyleSheet("color: #eee; font-size: 10px; font-weight: 700; font-family: 'Segoe UI'; letter-spacing: 0.5px;")
        
        self.icon_right = os.path.join(Config.ICONS_DIR, "arrow-right.svg")
        self.icon_down = os.path.join(Config.ICONS_DIR, "arrow-down.svg")
        
        self.btn_arrow = QPushButton()
        self.btn_arrow.setFixedSize(24, 24)
        self.btn_arrow.setCursor(Qt.PointingHandCursor)
        if os.path.exists(self.icon_right):
            self.btn_arrow.setIcon(QIcon(self.icon_right))
            self.btn_arrow.setIconSize(QSize(14, 14))
            
        self.btn_arrow.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                padding: 0px;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.05);
                border-radius: 4px;
            }
        """)
        self.btn_arrow.clicked.connect(self._toggle_submenu)
        
        info_row.addWidget(lbl_info)
        info_row.addStretch()
        info_row.addWidget(self.btn_arrow)
        self.main_layout.addLayout(info_row)

        # 3. Submenu Container (Hidden by default)
        self.submenu = QWidget()
        sub_layout = QVBoxLayout(self.submenu)
        sub_layout.setContentsMargins(8, 4, 0, 4)
        sub_layout.setSpacing(8)

        # 3a. Show Frame Name
        row_name = QHBoxLayout()
        lbl_name = QLabel("FRAME NAME")
        lbl_name.setStyleSheet("color: #999; font-size: 9px; font-weight: 700; font-family: 'Segoe UI';")
        self.toggle_name = ToggleSwitch(active_color="#cab2f2")
        self.toggle_name.set_active(self.initial_name)
        self.toggle_name.toggled.connect(self.show_name_toggled.emit)
        row_name.addWidget(lbl_name)
        row_name.addStretch()
        row_name.addWidget(self.toggle_name)
        sub_layout.addLayout(row_name)

        # 3b. Show Frame Size
        row_size = QHBoxLayout()
        lbl_size = QLabel("FRAME SIZE")
        lbl_size.setStyleSheet("color: #999; font-size: 9px; font-weight: 700; font-family: 'Segoe UI';")
        self.toggle_size = ToggleSwitch(active_color="#cab2f2")
        self.toggle_size.set_active(self.initial_size)
        self.toggle_size.toggled.connect(self.show_size_toggled.emit)
        row_size.addWidget(lbl_size)
        row_size.addStretch()
        row_size.addWidget(self.toggle_size)
        sub_layout.addLayout(row_size)

        self.submenu.setVisible(False)
        self.main_layout.addWidget(self.submenu)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.container)
        self.setFixedSize(160, 78)

    def _toggle_submenu(self):
        self._submenu_active = not self._submenu_active
        
        # 1. Update Icon
        icon_path = self.icon_down if self._submenu_active else self.icon_right
        if os.path.exists(icon_path):
            self.btn_arrow.setIcon(QIcon(icon_path))
            
        # 2. Animate Height
        start_h = 142 if not self._submenu_active else 78
        end_h = 78 if not self._submenu_active else 142
        
        self._anim.stop()
        self._anim.setStartValue(start_h)
        self._anim.setEndValue(end_h)
        
        if self._submenu_active:
            self.submenu.setVisible(True)
            
        self._anim.start()
        self.update()

    def _on_anim_finished(self):
        if not self._submenu_active:
            self.submenu.setVisible(False)

    def set_fill(self, active):
        self.toggle_fill.set_active(active)

    def set_info_options(self, name_active, size_active):
        self.toggle_name.set_active(name_active)
        self.toggle_size.set_active(size_active)
