"""Core application manager for Dimensio."""

import os
import sys
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any

import logging
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox
from PySide6.QtCore import QObject, QEvent, Qt, QRect, QRectF, QSettings, QDateTime, Slot
from PySide6.QtGui import QCursor, QPainter, QPixmap, QPen, QPainterPath

from src.config import Config
from src.widgets import MeasureFrame, SpacingOverlay, SmartGuides, Sidebar
from src.persistence import ProjectModel, FrameModel, ProjectSerializer
from src.exporters.blueprint_exporter import BlueprintExporter
from src.widgets.sidebar.tooltips import ToolTipFilter


# Configure logging for professional production environment
log_path = os.path.join(Config.USER_DATA, "dimensio.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(log_path, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("FrameManager")


class FrameManager(QObject):
    """
    Manages multiple measure overlay frames and the central Sidebar control panel.
    
    This is the core engine of Dimensio, handling signals between the UI and frames,
    persistence operations, and global event filtering.
    """
    
    def __init__(self):
        super().__init__()
        self.frames: List[MeasureFrame] = []
        self._color_idx: int = 0
        self._settings = QSettings("Dimensio", "Dimensio")
        self.selected_frame: Optional[MeasureFrame] = None
        self.project_path: Optional[str] = None
        self._dirty: bool = False
        
        # Persistent application settings
        self.advanced_settings: Dict[str, Any] = {
            "radius_curve": self._settings.value("radius_curve", False, type=bool),
            "fill_frame": self._settings.value("fill_frame", True, type=bool),
            "show_frame_name": self._settings.value("show_frame_name", True, type=bool),
            "show_frame_size": self._settings.value("show_frame_size", True, type=bool),
            "screenshot": self._settings.value("screenshot", False, type=bool)
        }
        
        self._init_overlays()
        self._init_sidebar()
        self._init_filters()
        
        self._update_sidebar_project_label()

    def _init_overlays(self):
        """Initialize background measurement overlays."""
        self.spacing_overlay = SpacingOverlay()
        self.smart_guides = SmartGuides()

    def _init_sidebar(self):
        """Configure the main control Sidebar."""
        self.sidebar = Sidebar(initial_settings=self.advanced_settings.copy())
        
        # Core Lifecycle
        self.sidebar.btn_close.clicked.connect(QApplication.quit)
        self.sidebar.new_design_requested.connect(self.new_design)
        self.sidebar.save_requested.connect(self.save_design)
        self.sidebar.import_requested.connect(self.import_design)
        
        # Frame Operations
        self.sidebar.new_frame_requested.connect(self.create_frame)
        self.sidebar.settings_changed.connect(self._on_settings_changed)
        self.sidebar.radius_value_changed.connect(self._handle_radius_change)
        self.sidebar.screenshot_requested.connect(lambda: BlueprintExporter.export(self.frames))
        self.sidebar.dimension_input_requested.connect(self._handle_dimension_input)
        self.sidebar.btn_copy.clicked.connect(self._handle_copy_request)
        
        # Layer Management
        self.sidebar.frame_visibility_toggled.connect(self._handle_visibility_toggle)
        self.sidebar.frame_lock_toggled.connect(self._handle_lock_toggle)
        self.sidebar.frame_delete_requested.connect(self._handle_remote_delete)
        self.sidebar.frame_name_changed.connect(self._handle_name_change)
        self.sidebar.frame_clicked.connect(self.select_frame)
        self.sidebar.frame_duplicate_requested.connect(self._handle_duplicate_frame)
        self.sidebar.frame_move_requested.connect(self._handle_move_frame)
        self.sidebar.frame_color_changed.connect(self._handle_color_change)
        
        self.sidebar.show()

    def _init_filters(self):
        """Install global event filters for shortcuts and syncing."""
        self._universal_tooltip_filter = ToolTipFilter(self)
        QApplication.instance().installEventFilter(self._universal_tooltip_filter)
        QApplication.instance().installEventFilter(self)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        """Handle global application events like minimization sync and Alt-measuring."""
        # 1. Synchronize minimization
        if watched == self.sidebar and event.type() == QEvent.WindowStateChange:
            if self.sidebar.isMinimized():
                for f in self.frames:
                    f.hide()
            elif event.oldState() & Qt.WindowMinimized:
                for f in self.frames:
                    if getattr(f, "_intended_visible", True):
                        f.show()
                        f.raise_()
                self.sidebar.raise_()

        # 2. Alt-Key Distance Measuring
        if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Alt:
            self._update_spacing_overlay()
            return False
        if event.type() == QEvent.KeyRelease and (event.key() == Qt.Key_Alt or event.key() == 16777251):
            self.spacing_overlay.clear()
            return False
        if event.type() == QEvent.MouseMove:
            if QApplication.keyboardModifiers() & Qt.AltModifier:
                self._update_spacing_overlay()
        
        return super().eventFilter(watched, event)

    def _handle_copy_request(self):
        """Copy dimensions of selected frame to clipboard."""
        if self.selected_frame:
            self.sidebar.copy_to_clipboard(self.selected_frame.get_dimensions_text())

    def _handle_dimension_input(self, axis: str, value: int):
        """Update selected frame dimensions from manual sidebar input."""
        if self.selected_frame:
            self.selected_frame._on_dimension_input(axis, value)

    def _handle_radius_change(self, radii: Dict[str, int]):
        """Update corner radii from sidebar controls."""
        if self.selected_frame:
            self.selected_frame.on_radius_value_changed(radii)
            self._mark_dirty()

    def _update_spacing_overlay(self):
        """Calculate and show distances between selected frame and frame under mouse."""
        if not self.selected_frame: 
            return
            
        cursor_pos = QCursor.pos()
        target = next((f for f in self.frames 
                      if f != self.selected_frame and f.isVisible() and f.geometry().contains(cursor_pos)), 
                      None)
                      
        if target:
            self.spacing_overlay.update_spacing(self.selected_frame.geometry(), target.geometry())
        else:
            self.spacing_overlay.clear()
        
    def create_frame(self):
        """Create and register a new measurement frame."""
        bg, border = Config.FRAME_COLORS[self._color_idx % len(Config.FRAME_COLORS)]
        self._color_idx += 1
        
        overlay = MeasureFrame(
            bg_color=bg, 
            border_color=border,
            frame_number=len(self.frames) + 1,
            initial_settings=self.advanced_settings.copy(),
            parent=None
        )
        
        # Inherit property if a frame is already selected
        if self.selected_frame:
            overlay.setGeometry(self.selected_frame.geometry().translated(20, 20))
            overlay.on_radius_value_changed(self.selected_frame.corner_radii.copy())

        # Signals
        overlay.geometry_changed.connect(lambda f=overlay: self._on_geometry_changed(f))
        overlay.clicked.connect(lambda f=overlay: self.select_frame(f))
        overlay.frame_closing.connect(self._on_frame_closing)
        overlay.drag_started.connect(self._on_drag_started)
        overlay.drag_finished.connect(self._on_drag_finished)
        
        overlay.show()
        self.frames.append(overlay)
        self.select_frame(overlay)
        self._mark_dirty()

    def _on_geometry_changed(self, frame: MeasureFrame):
        """Update UI and guides when a frame's geometry changes."""
        if frame == self.selected_frame:
            self.sidebar.update_dimensions(frame.width(), frame.height())
        
        # Universal Smart Guides
        others = [f.geometry() for f in self.frames if f != frame and f.isVisible()]
        is_dragging = getattr(frame, '_is_dragging', False)
        self.smart_guides.update_guides(frame.geometry(), others, auto_hide=not is_dragging)

        # Ensure the sidebar stays on top unless menu is open
        if not self.sidebar.file_menu.isVisible():
            self.sidebar.raise_()
        self._mark_dirty()

    def _on_drag_started(self, frame: MeasureFrame):
        pass

    def _on_drag_finished(self, frame: MeasureFrame):
        self.smart_guides.clear()

    def select_frame(self, frame: Optional[MeasureFrame]):
        """Focus a specific frame and update sidebar controls."""
        self.selected_frame = frame
        if frame:
            self.sidebar.update_dimensions(frame.width(), frame.height())
            self.sidebar.radius_panel.set_radii(frame.corner_radii)
            frame.highlight()
            
        self.sidebar.raise_()
        self._update_all_frame_lists()

    def _update_all_frame_lists(self):
        """Sync the Sidebar layer list with current internal state."""
        f_info = []
        # Reverse for Z-order (Top frame first in list)
        for f in reversed(self.frames):
            f_info.append({
                'id': f,
                'name': f.title,
                'visible': f.isVisible(),
                'locked': f.is_locked,
                'selected': f == self.selected_frame,
                'color': f.border_color.name() if hasattr(f.border_color, 'name') else f.border_color
            })
        self.sidebar.update_frame_list(f_info)

    @Slot(object, bool)
    def _handle_visibility_toggle(self, f: MeasureFrame, v: bool):
        if f in self.frames:
            f._intended_visible = v
            f.setVisible(v)
        self._update_all_frame_lists()
        self._mark_dirty()

    @Slot(object, bool)
    def _handle_lock_toggle(self, f: MeasureFrame, l: bool):
        if f in self.frames: 
            f.set_locked(l)
        self._update_all_frame_lists()
        self._mark_dirty()

    @Slot(object)
    def _handle_remote_delete(self, f: MeasureFrame):
        if f in self.frames:
            f.close()
            self._mark_dirty()

    @Slot(object, str)
    def _handle_name_change(self, f: MeasureFrame, n: str):
        if f in self.frames: 
            f.set_title(n)
        self._update_all_frame_lists()
        self._mark_dirty()

    @Slot(object)
    def _handle_duplicate_frame(self, frame: MeasureFrame):
        """Duplicate an existing frame with its properties."""
        if frame not in self.frames: 
            return
            
        new_name = f"{frame.title} copy"
        bg, border = Config.FRAME_COLORS[self._color_idx % len(Config.FRAME_COLORS)]
        self._color_idx += 1
        
        new_frame = MeasureFrame(
            bg_color=bg, 
            border_color=border,
            frame_number=len(self.frames) + 1,
            initial_settings=self.advanced_settings.copy(),
            parent=None
        )
        
        new_frame.setGeometry(frame.geometry().translated(20, 20))
        new_frame.set_title(new_name)
        new_frame.on_radius_value_changed(frame.corner_radii.copy())
        
        new_frame.geometry_changed.connect(lambda f=new_frame: self._on_geometry_changed(f))
        new_frame.clicked.connect(lambda f=new_frame: self.select_frame(f))
        new_frame.frame_closing.connect(self._on_frame_closing)
        new_frame.drag_started.connect(self._on_drag_started)
        new_frame.drag_finished.connect(self._on_drag_finished)
        
        new_frame.show()
        self.frames.append(new_frame)
        self.select_frame(new_frame)
        self._update_all_frame_lists()
        self._mark_dirty()

    @Slot(object, str)
    def _handle_move_frame(self, frame_id: Any, direction: str):
        """Handle nudge movement for frames."""
        frame = frame_id if isinstance(frame_id, MeasureFrame) else None
        if not frame:
            for f in self.frames:
                if f == frame_id:
                    frame = f; break
        
        if not frame or frame.is_locked: 
            return
            
        modifiers = QApplication.keyboardModifiers()
        step = 10 if modifiers & Qt.ShiftModifier else 1
        
        pos = frame.pos()
        if direction == "up": pos.setY(pos.y() - step)
        elif direction == "down": pos.setY(pos.y() + step)
        elif direction == "left": pos.setX(pos.x() - step)
        elif direction == "right": pos.setX(pos.x() + step)
        
        screen = QApplication.screenAt(frame.geometry().center()) or QApplication.primaryScreen()
        screen_geo = screen.availableGeometry()
        
        x = max(screen_geo.left(), min(screen_geo.right() - frame.width(), pos.x()))
        y = max(screen_geo.top(), min(screen_geo.bottom() - frame.height(), pos.y()))
        
        frame.move(x, y)
        self._on_geometry_changed(frame)

    @Slot(object, str)
    def _handle_color_change(self, frame_id: Any, hex_color: str):
        """Apply a new border color to the frame."""
        frame = frame_id if isinstance(frame_id, MeasureFrame) else None
        if not frame:
            for f in self.frames:
                if f == frame_id:
                    frame = f; break
        
        if frame:
            frame.set_color(hex_color)
            self._update_all_frame_lists()
            self._mark_dirty()

    def _on_settings_changed(self, news: Dict[str, Any]):
        """Update global settings and apply them to all frames."""
        self.advanced_settings.update(news)
        for k, v in news.items(): 
            self._settings.setValue(k, v)
        for f in self.frames: 
            f.update_settings(news)
        
    def _on_frame_closing(self, frame: MeasureFrame):
        """Clean up references when a frame is closed."""
        if frame in self.frames: 
            self.frames.remove(frame)
        if self.selected_frame == frame:
            self.selected_frame = self.frames[-1] if self.frames else None
            
        self._renumber_frames()
        self._update_all_frame_lists()
        self._mark_dirty()
    
    def _renumber_frames(self):
        for i, f in enumerate(self.frames, 1): 
            f.set_frame_number(i)


    def _update_sidebar_project_label(self):
        name = os.path.basename(self.project_path) if self.project_path else "Unsaved Project"
        self.sidebar.set_project_name(name, self._dirty)

    def _mark_dirty(self):
        self._dirty = True
        self._update_sidebar_project_label()

    def _export_current_project(self) -> ProjectModel:
        """Serialize current state into a ProjectModel."""
        frame_models = []
        for f in self.frames:
            frame_models.append(FrameModel(
                id=str(uuid.uuid4()),
                title=f.title,
                x=f.x(),
                y=f.y(),
                width=f.width(),
                height=f.height(),
                bg_color=f.bg_color.name() if hasattr(f.bg_color, 'name') else f.bg_color,
                border_color=f.border_color.name() if hasattr(f.border_color, 'name') else f.border_color,
                radii=f.corner_radii.copy(),
                locked=f.is_locked,
                visible=f.isVisible(),
                fill_enabled=f.fill_enabled
            ))

        return ProjectModel(
            version="1.0",
            app_version="2.0.0",
            created_at=datetime.now().isoformat(),
            frames=frame_models
        )

    def new_design(self):
        """Reset the workspace. Auto-saves existing projects, otherwise clears directly."""
        # 1. Autosave if it's already an established project
        if self.project_path and self._dirty and self.frames:
            try:
                self.save_design()
            except Exception as e:
                logger.error(f"New Design autosave failed: {e}")

        # 2. Clear all frames
        for f in list(self.frames):
            f.close()
        self.frames.clear()
        self.selected_frame = None
        self.project_path = None
        self._dirty = False
        self._color_idx = 0

        # 3. Reset Sidebar State
        self._update_all_frame_lists()
        self._update_sidebar_project_label()
        self.sidebar.update_dimensions(0, 0)
        
        # 4. Start with a fresh frame
        self.create_frame()

    def save_design(self):
        """Save the current layout to disk."""
        if not self.frames:
            QMessageBox.warning(None, "Nothing to Save", "No frames available.")
            return

        path = self.project_path or QFileDialog.getSaveFileName(
            None, "Save Project", "", "Dimensio Project (*.dio)"
        )[0]

        if not path: 
            return

        try:
            project = self._export_current_project()
            ProjectSerializer.save(path, project)
            self.project_path = path
            self._dirty = False
            self._update_sidebar_project_label()
        except Exception as e:
            logger.error(f"Save failed: {e}", exc_info=True)
            QMessageBox.critical(None, "Save Error", str(e))

    def import_design(self):
        """Prompt to open an existing project file."""
        path, _ = QFileDialog.getOpenFileName(
            None, "Open Project", "", "Dimensio Project (*.dio)"
        )
        if path:
            self.import_design_from_path(path)

    def import_design_from_path(self, path: str):
        """Load project state from a specific path."""
        try:
            project = ProjectSerializer.load(path)

            for f in list(self.frames):
                f.close()
            self.frames.clear()
            self.project_path = path

            for frame_data in project.frames:
                overlay = MeasureFrame(
                    bg_color=frame_data.bg_color,
                    border_color=frame_data.border_color,
                    frame_number=len(self.frames) + 1,
                    initial_settings=self.advanced_settings.copy(),
                    parent=None
                )
                overlay.setGeometry(frame_data.x, frame_data.y, frame_data.width, frame_data.height)
                overlay.set_title(frame_data.title)
                overlay.set_locked(frame_data.locked)
                overlay.setVisible(frame_data.visible)
                overlay.on_radius_value_changed(frame_data.radii)

                overlay.geometry_changed.connect(lambda f=overlay: self._on_geometry_changed(f))
                overlay.clicked.connect(lambda f=overlay: self.select_frame(f))
                overlay.frame_closing.connect(self._on_frame_closing)
                overlay.drag_started.connect(self._on_drag_started)
                overlay.drag_finished.connect(self._on_drag_finished)

                overlay.show()
                self.frames.append(overlay)

            if self.frames:
                self.select_frame(self.frames[0])

            self._update_all_frame_lists()
            self._dirty = False
            self._update_sidebar_project_label()

        except Exception as e:
            logger.error(f"Import failed: {e}", exc_info=True)
            QMessageBox.critical(None, "Import Error", str(e))
