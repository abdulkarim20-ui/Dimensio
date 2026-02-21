"""Main sidebar navigation and control panel."""

import os
from typing import Optional
from PySide6.QtWidgets import (QWidget, QLabel, QHBoxLayout, QVBoxLayout, QFrame, 
                             QPushButton, QScrollArea, QStackedWidget, QApplication)
from PySide6.QtCore import Qt, Signal, QSize, QTimer, QPoint

from PySide6.QtGui import QIcon, QKeySequence, QShortcut, QKeyEvent


from ...config import Config
from ..file_menu import FileMenu
from ..settings_menu import SettingsMenu
from .tooltips import ToolTipFilter
from .inputs import EditableLabel
from .position import PositionControl
from .radius import RadiusPanel
from .layers import FrameItem
from .status_bar import StatusBar


class Sidebar(QWidget):
    """Main control panel (Sidebar) for Dimensio."""
    
    new_frame_requested = Signal()
    new_design_requested = Signal()
    settings_changed = Signal(dict)
    radius_value_changed = Signal(dict)
    screenshot_requested = Signal()
    dimension_input_requested = Signal(str, int)
    frame_duplicate_requested = Signal(object)
    frame_move_requested = Signal(object, str)
    frame_color_changed = Signal(object, str)
    save_requested = Signal()
    import_requested = Signal()
    
    frame_visibility_toggled = Signal(object, bool)
    frame_lock_toggled = Signal(object, bool)
    frame_delete_requested = Signal(object)
    frame_name_changed = Signal(object, str)
    frame_clicked = Signal(object)
    
    def __init__(self, parent=None, theme_color=None, initial_settings=None):
        super().__init__(parent)
        self.theme_color = "#ffffff"
        self.initial_settings = initial_settings or {"fill_frame": True}
        self.frame_items = []
        self.selected_frame_id = None
        
        self.dup_shortcut = QShortcut(QKeySequence("Ctrl+J"), self)
        self.dup_shortcut.activated.connect(self._on_shortcut_duplicate)
        
        self.new_shortcut = QShortcut(QKeySequence("Ctrl+N"), self)
        self.new_shortcut.activated.connect(self.new_frame_requested.emit)

        self.new_design_shortcut = QShortcut(QKeySequence("Ctrl+Shift+N"), self)
        self.new_design_shortcut.activated.connect(self.new_design_requested.emit)

        self.save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        self.save_shortcut.activated.connect(self.save_requested.emit)

        self.import_shortcut = QShortcut(QKeySequence("Ctrl+O"), self)
        self.import_shortcut.activated.connect(self.import_requested.emit)

        
        self.copy_timer = QTimer()
        self.copy_timer.setSingleShot(True)
        self.copy_timer.timeout.connect(self._reset_copy_button)
        
        self.tooltip_filter = ToolTipFilter(self)
        
        self._init_frame()
        self._init_ui()
        self._apply_initial_settings()
        
    def _apply_initial_settings(self):
        if not hasattr(self, 'file_menu'):
            self.file_menu = FileMenu(theme_color=self.theme_color)
            self.file_menu.new_requested.connect(self.new_design_requested.emit)
            self.file_menu.save_requested.connect(self.save_requested.emit)
            self.file_menu.import_requested.connect(self.import_requested.emit)

        if not hasattr(self, 'settings_menu'):
            self.settings_menu = SettingsMenu(
                initial_fill=self.initial_settings.get("fill_frame", True),
                initial_name=self.initial_settings.get("show_frame_name", True),
                initial_size=self.initial_settings.get("show_frame_size", True)
            )
            self.settings_menu.fill_toggled.connect(self._on_fill_toggled)
            self.settings_menu.show_name_toggled.connect(self._on_name_toggled)
            self.settings_menu.show_size_toggled.connect(self._on_size_toggled)
        
        self.btn_screenshot.setVisible(True)
        self.updateGeometry()
        self.adjustSize()
        
    def _init_frame(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_AlwaysShowToolTips, True)
        self.setWindowIcon(QIcon(Config.APP_LOGO))
        
    def _init_ui(self):
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")
        
        self.icon_settings_path = os.path.join(Config.ICONS_DIR, "settings-gear.svg")
        self.icon_screenshot_path = Config.ICON_SCREENSHOT
        self.icon_copy_path = os.path.join(Config.ICONS_DIR, "copy.svg")


        self.container = QFrame(self)
        self.container.setObjectName("Container")
        self.container.setStyleSheet("QFrame#Container { background-color: #1a1a1a; border: 1px solid #ffffff; border-radius: 4px; }")
        
        layout_main = QVBoxLayout(self.container)
        layout_main.setContentsMargins(0, 0, 0, 0)
        layout_main.setSpacing(0)
        layout_main.setSizeConstraint(QVBoxLayout.SetFixedSize)
        self.setFixedWidth(240)

        # TOP HEADER ROW (Replacing TitleBar)
        self.header_row = QFrame()
        self.header_row.setFixedHeight(34)
        self.header_row.setStyleSheet("background-color: #000; border-top-left-radius: 4px; border-top-right-radius: 4px;")
        layout_header = QHBoxLayout(self.header_row)
        layout_header.setContentsMargins(10, 0, 8, 0)
        layout_header.setSpacing(8)

        # Logo Icon
        self.lbl_logo = QLabel()
        self.lbl_logo.setFixedSize(16, 16)
        if os.path.exists(Config.APP_LOGO):
            from PySide6.QtGui import QPixmap
            self.lbl_logo.setPixmap(QPixmap(Config.APP_LOGO).scaled(16, 16, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        layout_header.addWidget(self.lbl_logo)

        # FILE Button (Renamed from MENU, removed border)
        self.btn_menu = QPushButton("File")
        self.btn_menu.setFixedSize(36, 22)
        self.btn_menu.setCursor(Qt.PointingHandCursor)
        self.btn_menu.setStyleSheet("""
            QPushButton { 
                background: transparent; 
                border: none; 
                color: #888; 
                font-weight: 600; 
                font-size: 11px; 
                font-family: 'Segoe UI';
                padding-left: 4px;
                padding-right: 4px;
            } 
            QPushButton:hover { 
                background: rgba(255, 255, 255, 0.1); 
                color: #fff;
                border-radius: 3px;
            }
        """)
        self.btn_menu.clicked.connect(self._toggle_file_menu)
        layout_header.addWidget(self.btn_menu)
        
        layout_header.addSpacing(4)

        
        layout_header.addStretch()

        # Minimize Button
        self.btn_minimize = QPushButton()
        self.btn_minimize.setFixedSize(28, 28)
        self.btn_minimize.setIcon(QIcon(os.path.join(Config.ICONS_DIR, "minimize.svg")))
        self.btn_minimize.setIconSize(QSize(14, 14))
        self.btn_minimize.setCursor(Qt.PointingHandCursor)
        self.btn_minimize.setStyleSheet("""
            QPushButton { background: transparent; border: none; } 
            QPushButton:hover { background: rgba(255, 255, 255, 0.1); border-radius: 4px; }
        """)
        self.btn_minimize.clicked.connect(self.showMinimized)
        layout_header.addWidget(self.btn_minimize)

        # Close Button
        self.btn_close = QPushButton()
        self.btn_close.setFixedSize(28, 28)
        self.btn_close.setIcon(QIcon(os.path.join(Config.ICONS_DIR, "close.svg")))
        self.btn_close.setIconSize(QSize(14, 14))
        self.btn_close.setCursor(Qt.PointingHandCursor)
        self.btn_close.setStyleSheet("""
            QPushButton { background: transparent; border: none; } 
            QPushButton:hover { background: #e74c3c; border-radius: 4px; }
        """)
        layout_header.addWidget(self.btn_close)

        layout_main.addWidget(self.header_row)


        # CONTENT
        self.content_container = QFrame()
        self.content_container.setFixedHeight(64)
        layout_content = QHBoxLayout(self.content_container)
        layout_content.setContentsMargins(10, 8, 10, 8)
        layout_content.setSpacing(0)
        
        self.accent_bar = QFrame()
        self.accent_bar.setFixedWidth(3)
        self.accent_bar.setStyleSheet("background-color: #ffffff; border-radius: 1px;")
        layout_content.addWidget(self.accent_bar)
        layout_content.addSpacing(12)

        l_w = QVBoxLayout()
        l_w.setSpacing(0)
        l_w.setAlignment(Qt.AlignCenter)
        lbl_w = QLabel("WIDTH")
        lbl_w.setStyleSheet("color: #666; font-weight: bold; font-size: 9px; font-family: 'Segoe UI'; letter-spacing: 0.5px;")
        self.lbl_width_val = EditableLabel("0")
        self.lbl_width_val.value_changed.connect(lambda v: self.dimension_input_requested.emit("width", v))
        l_w.addWidget(lbl_w)
        l_w.addWidget(self.lbl_width_val)
        layout_content.addLayout(l_w)
        
        layout_content.addSpacing(10)

        self.sep_vert = QFrame()
        self.sep_vert.setFixedWidth(1)
        self.sep_vert.setFixedHeight(24)
        self.sep_vert.setStyleSheet("background-color: #333333;")
        layout_content.addWidget(self.sep_vert)
        
        layout_content.addSpacing(10)

        l_h = QVBoxLayout()
        l_h.setSpacing(0)
        l_h.setAlignment(Qt.AlignCenter)
        lbl_h = QLabel("HEIGHT")
        lbl_h.setStyleSheet("color: #666; font-weight: bold; font-size: 9px; font-family: 'Segoe UI'; letter-spacing: 0.5px;")
        self.lbl_height_val = EditableLabel("0")
        self.lbl_height_val.value_changed.connect(lambda v: self.dimension_input_requested.emit("height", v))
        l_h.addWidget(lbl_h)
        l_h.addWidget(self.lbl_height_val)
        layout_content.addLayout(l_h)
        
        layout_content.addSpacing(15)

        self.btn_copy = QPushButton()
        self._set_button_style(self.btn_copy, self.icon_copy_path, "Copy Dimensions to Clipboard")
        self.btn_copy.clicked.connect(self._handle_copy_click)
        
        self.btn_screenshot = QPushButton()
        self._set_button_style(self.btn_screenshot, self.icon_screenshot_path, "Blueprint Wireframe")
        self.btn_screenshot.clicked.connect(self.screenshot_requested.emit)

        self.btn_settings = QPushButton()
        self._set_button_style(self.btn_settings, self.icon_settings_path, "Advanced UI Options")
        self.btn_settings.clicked.connect(self._toggle_settings_menu)

        layout_content.addStretch()

        btns = QHBoxLayout()
        btns.setSpacing(6)
        btns.addWidget(self.btn_copy)
        btns.addWidget(self.btn_screenshot)
        btns.addWidget(self.btn_settings)
        layout_content.addLayout(btns)
        layout_main.addWidget(self.content_container)

        # TAB SECTION
        self.layers_header = QFrame()
        self.layers_header.setFixedHeight(32)
        self.layers_header.setStyleSheet("background-color: #0a0a0a; border-top: 1px solid #000;")
        h_layout = QHBoxLayout(self.layers_header)
        h_layout.setContentsMargins(0, 0, 4, 0)
        h_layout.setSpacing(0)
        
        self.tab_layers = QPushButton("LAYERS")
        self.tab_position = QPushButton("POSITION")
        self.tab_curves = QPushButton("CURVES")
        
        for tab in [self.tab_layers, self.tab_position, self.tab_curves]:
            tab.setFixedHeight(32)
            tab.setCursor(Qt.PointingHandCursor)
            tab.setCheckable(True)
            tab.setFocusPolicy(Qt.NoFocus)
            
        self.tab_layers.setChecked(True)
        h_layout.addWidget(self.tab_layers)
        h_layout.addWidget(self.tab_position)
        h_layout.addWidget(self.tab_curves)
        h_layout.addStretch()
        layout_main.addWidget(self.layers_header)

        # STACK
        self.stack = QStackedWidget()
        self.stack.setFixedHeight(180)
        self.stack.setStyleSheet("background-color: #1a1a1a;")
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setStyleSheet("""
            QScrollArea { background: transparent; }
            QScrollBar:vertical { border: none; background: transparent; width: 10px; }
            QScrollBar::handle:vertical { background: rgba(255, 255, 255, 0.1); min-height: 30px; border-radius: 5px; margin: 2px 2px 2px 4px; }
            QScrollBar::handle:vertical:hover { background: rgba(255, 255, 255, 0.2); }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
        """)
        
        self.scroll_content = QWidget()
        self.layout_frame_list = QVBoxLayout(self.scroll_content)
        self.layout_frame_list.setContentsMargins(0, 0, 0, 0)
        self.layout_frame_list.setSpacing(0)
        self.layout_frame_list.addStretch()
        self.scroll_area.setWidget(self.scroll_content)
        
        self.position_panel = PositionControl()
        self.position_panel.move_requested.connect(self._on_pos_move_requested)

        self.radius_panel = RadiusPanel(theme_color="#cab2f2")
        self.radius_panel.radius_changed.connect(self.radius_value_changed.emit)
        self.radius_panel.height_delta_changed.connect(self._on_radius_panel_height_changed)
        
        self.stack.addWidget(self.scroll_area)
        self.stack.addWidget(self.position_panel)
        self.stack.addWidget(self.radius_panel)
        
        self.tab_layers.clicked.connect(lambda: self._switch_tab(0))
        self.tab_position.clicked.connect(lambda: self._switch_tab(1))
        self.tab_curves.clicked.connect(lambda: self._switch_tab(2))
        self._update_tab_styles()
        layout_main.addWidget(self.stack)
        
        # STATUS BAR
        self.status_bar = StatusBar(tooltip_filter=self.tooltip_filter, parent=self)
        self.status_bar.add_frame_requested.connect(self.new_frame_requested.emit)
        self.status_bar.delete_frame_requested.connect(self._on_delete_active_requested)
        layout_main.addWidget(self.status_bar)


        layout_root = QVBoxLayout(self)
        layout_root.setContentsMargins(0, 0, 0, 0)
        layout_root.addWidget(self.container)
        layout_root.setSizeConstraint(QVBoxLayout.SetFixedSize)

    def _set_button_style(self, btn, icon_path, tooltip):
        btn.setFixedSize(32, 32)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setToolTip(tooltip)
        if os.path.exists(icon_path):
            btn.setIcon(QIcon(icon_path))
            btn.setIconSize(QSize(18, 18))
        btn.setStyleSheet("""
            QPushButton { 
                background: transparent; 
                border: 1px solid #333; 
                border-radius: 6px; 
            } 
            QPushButton:hover { 
                background: rgba(255, 255, 255, 0.05); 
                border-color: #666; 
            }
        """)
        btn.installEventFilter(self.tooltip_filter)



    def _handle_copy_click(self):
        self.btn_copy.setStyleSheet("QPushButton { background: rgba(46, 204, 113, 0.2); border: 1px solid #2ecc71; border-radius: 4px; }")
        self.status_bar.show_copied_status()
        self.copy_timer.start(2000)

    def _reset_copy_button(self):
        self._set_button_style(self.btn_copy, self.icon_copy_path, "Copy Dimensions to Clipboard")
        self.status_bar.reset_status()



    def _on_radius_panel_height_changed(self, delta):
        self.updateGeometry()
        self.adjustSize()

    def update_frame_list(self, frames_info):
        self.selected_frame_id = None
        for i in reversed(range(self.layout_frame_list.count())):
            item = self.layout_frame_list.itemAt(i).widget()
            if item: item.deleteLater()
        self.layout_frame_list.takeAt(self.layout_frame_list.count()-1)

        for f_data in frames_info:
            if f_data['selected']:
                self.selected_frame_id = f_data['id']
            
            item = FrameItem(
                f_data['name'], 
                is_visible=f_data['visible'], 
                is_locked=f_data['locked'],
                is_selected=f_data['selected'],
                color_hex=f_data['color']
            )
            fid = f_data['id']
            item.visibility_toggled.connect(lambda v, i=fid: self.frame_visibility_toggled.emit(i, v))
            item.lock_toggled.connect(lambda l, i=fid: self.frame_lock_toggled.emit(i, l))
            item.delete_requested.connect(lambda i=fid: self.frame_delete_requested.emit(i))
            item.name_changed.connect(lambda n, i=fid: self.frame_name_changed.emit(i, n))
            item.clicked.connect(lambda i=fid: self._on_item_clicked(i))
            item.duplicate_requested.connect(lambda i=fid: self.frame_duplicate_requested.emit(i))
            item.color_changed.connect(lambda c, i=fid: self.frame_color_changed.emit(i, c))
            self.layout_frame_list.insertWidget(self.layout_frame_list.count()-1, item)
            
        self.layout_frame_list.addStretch()
        self.frame_items = frames_info 
        self.status_bar.update_count(len(self.frame_items))


    def update_dimensions(self, w, h):
        self.lbl_width_val.blockSignals(True)
        self.lbl_height_val.blockSignals(True)
        self.lbl_width_val.setText(str(w))
        self.lbl_height_val.setText(str(h))
        self.lbl_width_val.blockSignals(False)
        self.lbl_height_val.blockSignals(False)

    def _toggle_file_menu(self):
        pos = self.btn_menu.mapToGlobal(self.btn_menu.rect().bottomLeft())
        self.file_menu.move(pos.x() - self.file_menu.width() + self.btn_menu.width(), pos.y() + 5)
        self.file_menu.show()

    def _toggle_settings_menu(self):
        pos = self.btn_settings.mapToGlobal(self.btn_settings.rect().bottomRight())
        self.settings_menu.move(pos.x() - self.settings_menu.width(), pos.y() + 5)
        self.settings_menu.show()

    def _on_shortcut_duplicate(self):
        if self.selected_frame_id:
            self.frame_duplicate_requested.emit(self.selected_frame_id)

    def _on_delete_active_requested(self):
        if self.selected_frame_id:
            self.frame_delete_requested.emit(self.selected_frame_id)

    def _on_item_clicked(self, fid):
        """Handle item click: set focus to sidebar for keyboard shortcuts and emit signal."""
        self.setFocus()
        self.frame_clicked.emit(fid)

    def _switch_tab(self, index):
        self.stack.setCurrentIndex(index)
        self.tab_layers.setChecked(index == 0)
        self.tab_position.setChecked(index == 1)
        self.tab_curves.setChecked(index == 2)
        self._update_tab_styles()
        if index == 1:
            self.setFocus()

    def _update_tab_styles(self):
        active = "color: #eee; font-weight: 900; font-size: 8px; letter-spacing: 1.5px; background: #1a1a1a; border: none; padding: 0 15px; border-top-left-radius: 4px; border-top-right-radius: 4px;"
        inactive = "color: #555; font-weight: 900; font-size: 8px; letter-spacing: 1.5px; background: #0a0a0a; border: none; padding: 0 15px;"
        self.tab_layers.setStyleSheet(active if self.stack.currentIndex() == 0 else inactive)
        self.tab_position.setStyleSheet(active if self.stack.currentIndex() == 1 else inactive)
        self.tab_curves.setStyleSheet(active if self.stack.currentIndex() == 2 else inactive)

    def _get_selected_item(self) -> Optional[FrameItem]:
        """Find the FrameItem widget that corresponds to the selected frame id."""
        for i in range(self.layout_frame_list.count()):
            item = self.layout_frame_list.itemAt(i).widget()
            if isinstance(item, FrameItem) and item.is_selected:
                return item
        return None

    def _on_pos_move_requested(self, direction):
        if self.selected_frame_id:
            self.frame_move_requested.emit(self.selected_frame_id, direction)

    def keyPressEvent(self, event: QKeyEvent):
        if not self.selected_frame_id:
            super().keyPressEvent(event)
            return

        # 1. Rename (F2)
        if event.key() == Qt.Key_F2:
            item = self._get_selected_item()
            if item:
                item._start_rename()
                event.accept()
                return

        # 2. Delete (Delete Key)
        if event.key() == Qt.Key_Delete:
            self._on_delete_active_requested()
            event.accept()
            return

        direction = None
        if event.key() == Qt.Key_Up: direction = "up"
        elif event.key() == Qt.Key_Down: direction = "down"
        elif event.key() == Qt.Key_Left: direction = "left"
        elif event.key() == Qt.Key_Right: direction = "right"
        
        if direction:
            self.frame_move_requested.emit(self.selected_frame_id, direction)
            event.accept()
        else:
            super().keyPressEvent(event)

    def mouseMoveEvent(self, event):
        if hasattr(self, 'start_drag_pos') and self.start_drag_pos and (event.buttons() & Qt.LeftButton):
            curr_pos = event.globalPosition().toPoint()
            delta = curr_pos - self.start_drag_pos
            screen = QApplication.screenAt(curr_pos) or QApplication.primaryScreen()
            s_rect = screen.availableGeometry()
            target_pos = self.pos() + delta
            x = max(s_rect.left(), min(s_rect.right() - self.width(), target_pos.x()))
            y = max(s_rect.top(), min(s_rect.bottom() - self.height(), target_pos.y()))
            self.move(x, y)
            self.start_drag_pos = curr_pos
            event.accept()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start_drag_pos = event.globalPosition().toPoint()
            event.accept()

    def mouseReleaseEvent(self, event):
        self.start_drag_pos = None

    def copy_to_clipboard(self, text):
        from PySide6.QtGui import QClipboard
        QApplication.clipboard().setText(text)
        old_text = self.btn_copy.toolTip()
        self.btn_copy.setToolTip("Copied!")
        QTimer.singleShot(1500, lambda: self.btn_copy.setToolTip(old_text))

    def _on_fill_toggled(self, active):
        self.settings_changed.emit({"fill_frame": active})

    def _on_name_toggled(self, active):
        self.settings_changed.emit({"show_frame_name": active})

    def _on_size_toggled(self, active):
        self.settings_changed.emit({"show_frame_size": active})

    def set_project_name(self, name, is_dirty=True):
        self.status_bar.set_project_name(name, is_dirty)
