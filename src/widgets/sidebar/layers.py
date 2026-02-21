"""Layer list components and frame rows."""

import os
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QFrame, QLineEdit, QLabel
from PySide6.QtCore import Qt, Signal, QSize, QEvent
from PySide6.QtGui import QColor, QPixmap, QIcon
from ...config import Config
from ..context_menu import PremiumContextMenu
from .tooltips import ToolTipFilter

class ElidedLabel(QLabel):
    """A label that elides text with '...' when it doesn't fit."""
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self._original_text = text
        self.setMinimumWidth(20)

    def setText(self, text):
        self._original_text = text
        self._elide_text()

    def resizeEvent(self, event):
        self._elide_text()
        super().resizeEvent(event)

    def _elide_text(self):
        from PySide6.QtGui import QFontMetrics
        metrics = QFontMetrics(self.font())
        elided = metrics.elidedText(self._original_text, Qt.ElideRight, self.width())
        super().setText(elided)

class FrameItem(QFrame):
    """A single frame row in the layers list, mimicking Photoshop layers."""
    
    visibility_toggled = Signal(bool)
    lock_toggled = Signal(bool)
    delete_requested = Signal()
    name_changed = Signal(str)
    clicked = Signal()
    duplicate_requested = Signal()
    color_changed = Signal(str)
    
    def __init__(self, name, is_visible=True, is_locked=False, is_selected=False, color_hex="#ffffff", parent=None):
        super().__init__(parent)
        self.setFixedHeight(30)
        self.is_selected = is_selected
        
        self.setObjectName("FrameItem")
        self.setAttribute(Qt.WA_StyledBackground)

        self.tooltip_filter = ToolTipFilter(self)
        

        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 0, 6, 0)
        layout.setSpacing(8)
        
        self.btn_eye = QPushButton()
        self.btn_eye.setFixedSize(26, 26)
        self.btn_eye.setCursor(Qt.PointingHandCursor)
        self.btn_eye.setToolTip("Toggle Visibility")
        self.btn_eye.setCheckable(True)
        self.btn_eye.setChecked(is_visible)
        self.btn_eye.setStyleSheet("QPushButton { background: transparent; border: none; } QPushButton:hover { background: rgba(255,255,255,15); border-radius: 2px; }")
        
        self.icon_eye = os.path.join(Config.ICONS_DIR, "eye.svg")
        self.icon_eye_closed = os.path.join(Config.ICONS_DIR, "eye-closed.svg")
        self._update_eye_icon()
        self.btn_eye.clicked.connect(self._on_eye_clicked)
        layout.addWidget(self.btn_eye)
        
        self.indicator = QFrame()
        self.indicator.setFixedSize(16, 12)
        self.indicator.setStyleSheet(f"background-color: {color_hex}; border: 1px solid #444; border-radius: 1px;")
        layout.addWidget(self.indicator)
        
        self.lbl_name = ElidedLabel(name)
        self.lbl_name.installEventFilter(self)

        
        self.edit_name = QLineEdit(name)
        self.edit_name.setStyleSheet("background: #000; color: white; border: 1px solid #fff; font-size: 11px;")
        self.edit_name.setVisible(False)
        self.edit_name.editingFinished.connect(self._finish_rename)
        self.edit_name.returnPressed.connect(self._finish_rename)
        
        layout.addWidget(self.lbl_name, 1)
        layout.addWidget(self.edit_name, 1)
        
        layout.addStretch()

        self.btn_lock = QPushButton()
        self.btn_lock.setFixedSize(26, 26)
        self.btn_lock.setCursor(Qt.PointingHandCursor)
        self.btn_lock.setToolTip("Lock Frame")
        self.btn_lock.setCheckable(True)
        self.btn_lock.setChecked(is_locked)
        self.btn_lock.setStyleSheet("QPushButton { background: transparent; border: none; opacity: 0.5; } QPushButton:hover { background: rgba(255,255,255,15); border-radius: 2px; opacity: 1.0; } QPushButton:checked { opacity: 1.0; }")
        
        self.icon_lock = os.path.join(Config.ICONS_DIR, "lock.svg")
        self.icon_unlock = os.path.join(Config.ICONS_DIR, "unlock.svg")
        self._update_lock_icon()
        self.btn_lock.clicked.connect(self._on_lock_clicked)
        layout.addWidget(self.btn_lock)
        
        self._setup_style()

        
        self.btn_eye.installEventFilter(self.tooltip_filter)
        self.btn_lock.installEventFilter(self.tooltip_filter)

    def contextMenuEvent(self, event):
        menu = PremiumContextMenu(self)
        
        # 1. Rename Option
        rename_action = menu.addAction("Rename")
        rename_action.setShortcut("F2")
        rename_action.triggered.connect(self._start_rename)
        
        # 2. Duplicate Option
        dup_action = menu.addAction("Duplicate Frame")
        dup_action.setShortcut("Ctrl+J")
        dup_action.triggered.connect(self.duplicate_requested.emit)
        
        menu.addSeparator()

        color_menu = menu.addMenu("Color")
        colors = [
            ("None", None),
            ("Red", "#e74c3c"),
            ("Orange", "#e67e22"),
            ("Yellow", "#f1c40f"),
            ("Green", "#2ecc71"),
            ("Blue", "#3498db"),
            ("Violet", "#9b59b2"),
            ("Gray", "#95a5a6"),
        ]
        
        for name, hexcode in colors:
            action = color_menu.addAction(name)
            if hexcode:
                pix = QPixmap(12, 12)
                pix.fill(QColor(hexcode))
                action.setIcon(QIcon(pix))
                action.triggered.connect(lambda checked, h=hexcode: self.color_changed.emit(h))
            else:
                action.triggered.connect(lambda checked: self.color_changed.emit("#ffffff"))
        
        menu.addSeparator()
        
        # 3. Delete Option (Renamed from Delete Layer)
        del_action = menu.addAction("Delete")
        del_action.setShortcut("Del")
        del_action.triggered.connect(self.delete_requested.emit)
        
        menu.exec_(event.globalPos())

    def _setup_style(self):
        if self.is_selected:
            bg = "#3b3b3b" # Distinct selection gray
            border_l = "3px solid #ffffff"
            text_color = "#ffffff"
            opacity = "1.0"
        else:
            bg = "transparent"
            border_l = "3px solid transparent"
            text_color = "#9fa3a7" # Soft gray for unselected
            opacity = "0.5"
            
        self.setStyleSheet(f"""
            QFrame#FrameItem {{
                background-color: {bg};
                border-left: {border_l};
                border-bottom: 1px solid #222;
            }}
            QFrame#FrameItem:hover {{
                background-color: {"#444444" if self.is_selected else "rgba(255, 255, 255, 0.05)"};
            }}
        """)

        
        if hasattr(self, 'lbl_name'):
            self.lbl_name.setStyleSheet(f"color: {text_color}; font-size: 13px; font-family: 'Segoe UI'; font-weight: 500; background: transparent;")
        
        if hasattr(self, 'btn_lock'):
            self.btn_lock.setStyleSheet(f"QPushButton {{ background: transparent; border: none; opacity: {opacity}; }} QPushButton:hover {{ background: rgba(255,255,255,15); border-radius: 2px; opacity: 1.0; }}")
        
        if hasattr(self, 'btn_eye'):
             self.btn_eye.setStyleSheet(f"QPushButton {{ background: transparent; border: none; opacity: {opacity}; }} QPushButton:hover {{ background: rgba(255,255,255,15); border-radius: 2px; opacity: 1.0; }}")


    def set_active(self, active):
        self.is_selected = active
        self._setup_style()


    def eventFilter(self, obj, event):
        if obj == self.lbl_name and event.type() == QEvent.MouseButtonDblClick:
            if event.button() == Qt.LeftButton:
                self._start_rename()
                return True
        if event.type() == QEvent.MouseButtonPress:
            if event.button() == Qt.LeftButton:
                self.clicked.emit()
        return super().eventFilter(obj, event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def _start_rename(self):
        self.lbl_name.setVisible(False)
        self.edit_name.setVisible(True)
        self.edit_name.setFocus()
        self.edit_name.selectAll()

    def _finish_rename(self):
        if self.edit_name.isVisible():
            new_name = self.edit_name.text().strip()
            if new_name:
                self.lbl_name.setText(new_name)
                self.name_changed.emit(new_name)
            self.edit_name.setVisible(False)
            self.lbl_name.setVisible(True)

    def _on_eye_clicked(self):
        self._update_eye_icon()
        self.visibility_toggled.emit(self.btn_eye.isChecked())

    def _update_eye_icon(self):
        path = self.icon_eye if self.btn_eye.isChecked() else self.icon_eye_closed
        if os.path.exists(path):
            self.btn_eye.setIcon(QIcon(path))
            self.btn_eye.setIconSize(QSize(18, 18))

    def _on_lock_clicked(self):
        self._update_lock_icon()
        self.lock_toggled.emit(self.btn_lock.isChecked())

    def _update_lock_icon(self):
        path = self.icon_lock if self.btn_lock.isChecked() else self.icon_unlock
        if os.path.exists(path):
            self.btn_lock.setIcon(QIcon(path))
            self.btn_lock.setIconSize(QSize(18, 18))
