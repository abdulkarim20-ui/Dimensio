"""Main overlay widget - External Info Panel Version."""

import os

from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtCore import Qt, QPoint, QRect, QRectF, QEvent, Signal, Property, QEasingCurve, QPropertyAnimation, QTimer
from PySide6.QtGui import QPainter, QMouseEvent, QPaintEvent, QPen, QColor, QFont, QPixmap
from PySide6.QtSvg import QSvgRenderer

from ..config import Config
from ..enums import ResizeMode


class MeasureFrame(QWidget):
    """Transparent, resizable overlay frame for measuring dimensions."""
    
    frame_closing = Signal(object)
    geometry_changed = Signal()
    clicked = Signal()
    title_changed = Signal()
    drag_started = Signal(object)
    drag_finished = Signal(object)

    
    def __init__(self, bg_color=None, border_color=None, frame_number=1, initial_settings=None, parent=None):
        super().__init__(parent)
        self.bg_color = bg_color or Config.COLOR_BG
        self.border_color = border_color or Config.COLOR_BORDER
        self.frame_number = frame_number
        self.initial_settings = initial_settings or {}
        
        # State
        self.title = f"Frame {self.frame_number}"
        self._is_locked = False
        self._radius_active = False
        self._fill_enabled = self.initial_settings.get("fill_frame", True)
        self._show_frame_name = self.initial_settings.get("show_frame_name", True)
        self._show_frame_size = self.initial_settings.get("show_frame_size", True)
        self.corner_radii = {"tl": 0, "tr": 0, "bl": 0, "br": 0}
        self._intended_visible = True
        
        self._init_frame()
        self._init_state()

    @property
    def is_locked(self) -> bool:
        """Whether the frame is locked (cannot be resized or moved)."""
        return self._is_locked

    @is_locked.setter
    def is_locked(self, value: bool):
        self._is_locked = value
        self.update()

    @property
    def fill_enabled(self) -> bool:
        """Whether the frame's background fill is visible."""
        return self._fill_enabled

    @fill_enabled.setter
    def fill_enabled(self, value: bool):
        self._fill_enabled = value
        self.update()

    @property
    def show_frame_name(self) -> bool:
        """Whether the frame title is visible inside the frame."""
        return self._show_frame_name

    @show_frame_name.setter
    def show_frame_name(self, value: bool):
        self._show_frame_name = value
        self.update()

    @property
    def show_frame_size(self) -> bool:
        """Whether the dimension text is visible inside the frame."""
        return self._show_frame_size

    @show_frame_size.setter
    def show_frame_size(self, value: bool):
        self._show_frame_size = value
        self.update()

    @property
    def is_radius_active(self) -> bool:
        """Whether the frame has any non-zero corner radii."""
        return self._radius_active

    def highlight(self):
        """Show a quick solid white flash for 400ms."""
        self._trigger_feedback(400)
        self.raise_()

    def _trigger_feedback(self, ms=250):
        """Show the white border for a specific duration."""
        self._highlight_active = True
        self.update()
        self._highlight_timer.start(ms)

    def _init_frame(self):
        """Configure frame properties."""
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self.setMinimumSize(Config.MIN_SIZE, Config.MIN_SIZE)
        self.setMaximumSize(Config.MAX_SIZE, Config.MAX_SIZE)
        self.resize(400, 250)
    
    def wheelEvent(self, event):
        """Resize frame using mouse wheel while respecting screen boundaries."""
        delta = event.angleDelta().y()
        step = 10 if delta > 0 else -10
        
        # Current geometry
        rect = self.geometry()
        screen = QApplication.screenAt(event.globalPosition().toPoint()) or QApplication.primaryScreen()
        s_rect = screen.availableGeometry()
        
        # Calculate new dimensions
        nw = max(Config.MIN_SIZE, rect.width() + step)
        nh = max(Config.MIN_SIZE, rect.height() + step)
        
        # Center-based resize
        nx = rect.center().x() - nw // 2
        ny = rect.center().y() - nh // 2
        
        # Constrain to screen boundaries
        if nx < s_rect.left(): nx = s_rect.left()
        if ny < s_rect.top(): ny = s_rect.top()
        if nx + nw > s_rect.right(): nw = s_rect.right() - nx
        if ny + nh > s_rect.bottom(): nh = s_rect.bottom() - ny
        
        # Ensure minimum size after constraint
        nw = max(Config.MIN_SIZE, nw)
        nh = max(Config.MIN_SIZE, nh)
        
        self.setGeometry(int(nx), int(ny), int(nw), int(nh))
        self.geometry_changed.emit()
        
        # Show white border during scroll
        self._wheel_active = True
        self.update()
        self._wheel_timer.start(150) # Very short duration for live scroll feel
        
        event.accept()
    
    def _init_state(self):
        """Initialize interaction state."""
        self._drag_mode = ResizeMode.NONE
        self._start_geom = QRect()
        self._start_mouse = QPoint()
        self._is_dragging = False
        self._border_hover = False
        
        # Highlight state: Solid flash, no fade
        self._highlight_active = False
        self._highlight_timer = QTimer(self)
        self._highlight_timer.setSingleShot(True)
        self._highlight_timer.timeout.connect(self._stop_highlight)
        
        # Scroll feedback state
        self._wheel_active = False
        self._wheel_timer = QTimer(self)
        self._wheel_timer.setSingleShot(True)
        self._wheel_timer.timeout.connect(self._stop_wheel_feedback)

    def _stop_wheel_feedback(self):
        self._wheel_active = False
        self.update()

    def _stop_highlight(self):
        self._highlight_active = False
        self.update()

    def closeEvent(self, event):
        self.frame_closing.emit(self)
        super().closeEvent(event)

    def get_dimensions_text(self):
        """Get formatted dimensions for clipboard."""
        text = f"W: {self.width()}px; H: {self.height()}px;"
        if self._radius_active:
            tl, tr, bl, br = self.corner_radii.values()
            if len(set(self.corner_radii.values())) == 1:
                text += f" Radius: {tl}px;"
            else:
                text += f" Radius: TL:{tl}, TR:{tr}, BL:{bl}, BR:{br};"
        return text
    
    def set_color(self, hex_color):
        """Update frame color dynamically."""
        self.border_color = QColor(hex_color)
        self.border_color.setAlpha(220)
        # Background is usually 40 opacity version of border
        self.bg_color = QColor(hex_color)
        self.bg_color.setAlpha(40)
        self.update()

    def set_frame_number(self, number: int):
        """Update the frame sequential number and default title."""
        old_default = f"Frame {self.frame_number}"
        if self.title == old_default:
            self.title = f"Frame {number}"
        self.frame_number = number
        self.update()

    def set_locked(self, locked: bool):
        """Legacy setter for is_locked property."""
        self.is_locked = locked

    def set_title(self, title: str):
        """Update the frame's display title and notify listeners."""
        self.title = title
        self.title_changed.emit()
        self.update()

    def set_radius_active(self, active):
        self._radius_active = active
        self.update()
        self.geometry_changed.emit()

    def on_radius_value_changed(self, radii_dict):
        self.corner_radii = radii_dict
        self._radius_active = any(v > 0 for v in radii_dict.values())
        self._trigger_feedback(150)
        self.update()
        self.geometry_changed.emit()

    def _on_dimension_input(self, axis: str, value: int):
        # Determine screen boundaries to prevent window from going off-screen
        screen = QApplication.screenAt(self.geometry().center()) or QApplication.primaryScreen()
        s_rect = screen.availableGeometry()
        
        val = max(Config.MIN_SIZE, value)
        
        if axis == "width":
            # Cap width so it doesn't go beyond screen right edge
            max_w = s_rect.right() - self.x()
            val = min(val, max_w)
            self.resize(val, self.height())
        else:
            # Cap height so it doesn't go beyond screen bottom edge
            max_h = s_rect.bottom() - self.y()
            val = min(val, max_h)
            self.resize(self.width(), val)
            
        self._trigger_feedback(200) # Quick white border feedback
        self.geometry_changed.emit()

    def update_settings(self, settings):
        if "fill_frame" in settings:
            self._fill_enabled = settings["fill_frame"]
        if "show_frame_name" in settings:
            self._show_frame_name = settings["show_frame_name"]
        if "show_frame_size" in settings:
            self._show_frame_size = settings["show_frame_size"]
        self.update()

    def mousePressEvent(self, event: QMouseEvent):
        self.clicked.emit()
        if event.button() != Qt.LeftButton:
            super().mousePressEvent(event)
            return
        
        pos = event.position().toPoint()
        self._drag_mode = self._get_resize_mode(pos)
        self._start_mouse = event.globalPosition().toPoint()
        self._start_geom = QRect(self.geometry())
        self._is_dragging = True
        self.grabMouse()
        self.drag_started.emit(self)
        self.update() # Trigger white border
        event.accept()


    def mouseMoveEvent(self, event: QMouseEvent):
        pos = event.position().toPoint()
        if not self._is_dragging:
            mode = self._get_resize_mode(pos)
            self._update_cursor(mode)
            is_near = self._is_near_border(pos)
            if is_near != self._border_hover:
                self._border_hover = is_near
                self.update()
            return

        if self._drag_mode != ResizeMode.NONE:
            self._perform_drag(event.globalPosition().toPoint())
            self.geometry_changed.emit()
        event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._is_dragging = False
            self._drag_mode = ResizeMode.NONE
            self.releaseMouse()
            self.drag_finished.emit(self)
            self.update() # Return to natural color
            event.accept()


    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Background fill
        fill_color = self.bg_color if self._fill_enabled else QColor(0, 0, 0, 1)
        painter.setBrush(fill_color)
        
        # Border (White when dragging, scrolling, or flashing highlight)
        if self._is_dragging or self._wheel_active or self._highlight_active:
            border_c = QColor(255, 255, 255)
            pen_width = 2
        else:
            border_c = QColor(self.border_color)
            if self._border_hover:
                border_c = border_c.lighter(110)
            pen_width = 1
            
        painter.setPen(QPen(border_c, pen_width))
        painter.setBrush(fill_color)
        
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        
        if self._radius_active:
            from PySide6.QtGui import QPainterPath
            path = QPainterPath()
            r = self.corner_radii
            tl, tr = r.get("tl", 0), r.get("tr", 0)
            bl, br = r.get("bl", 0), r.get("br", 0)
            
            path.moveTo(rect.left() + tl, rect.top())
            path.lineTo(rect.right() - tr, rect.top())
            path.arcTo(rect.right() - 2*tr, rect.top(), 2*tr, 2*tr, 90, -90)
            path.lineTo(rect.right(), rect.bottom() - br)
            path.arcTo(rect.right() - 2*br, rect.bottom() - 2*br, 2*br, 2*br, 0, -90)
            path.lineTo(rect.left() + bl, rect.bottom())
            path.arcTo(rect.left(), rect.bottom() - 2*bl, 2*bl, 2*bl, 270, -90)
            path.lineTo(rect.left(), rect.top() + tl)
            path.arcTo(rect.left(), rect.top(), 2*tl, 2*tl, 180, -90)
            path.closeSubpath()
            painter.drawPath(path)
        else:
            painter.drawRect(rect)
            
            
        # Draw Title and Dimensions in center if permitted and not too small
        if (self._show_frame_name or self._show_frame_size) and self.width() > 60 and self.height() > 30:
            painter.setPen(border_c)
            painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
            
            lines = []
            if self._show_frame_name:
                lines.append(f"{self.title}")
            if self._show_frame_size:
                lines.append(f"{self.width()} × {self.height()}")
                
            text = "\n".join(lines)
            painter.drawText(self.rect(), Qt.AlignCenter, text)

    def resizeEvent(self, event):
        self.geometry_changed.emit()
        super().resizeEvent(event)

    def moveEvent(self, event):
        self.geometry_changed.emit()
        super().moveEvent(event)

    def _get_resize_mode(self, p: QPoint):
        if self._is_locked: return ResizeMode.NONE
        w, h = self.width(), self.height()
        m = min(Config.MARGIN_RESIZE, w // 3, h // 3)
        left, right = p.x() < m, p.x() > w - m
        top, bottom = p.y() < m, p.y() > h - m
        
        if top and left: return ResizeMode.RESIZE_TOP_LEFT
        if top and right: return ResizeMode.RESIZE_TOP_RIGHT
        if bottom and left: return ResizeMode.RESIZE_BOTTOM_LEFT
        if bottom and right: return ResizeMode.RESIZE_BOTTOM_RIGHT
        if left: return ResizeMode.RESIZE_LEFT
        if right: return ResizeMode.RESIZE_RIGHT
        if top: return ResizeMode.RESIZE_TOP
        if bottom: return ResizeMode.RESIZE_BOTTOM
        return ResizeMode.MOVE

    def _is_near_border(self, p: QPoint):
        w, h = self.width(), self.height()
        m = Config.MARGIN_RESIZE
        return p.x() < m or p.x() > w - m or p.y() < m or p.y() > h - m

    def _update_cursor(self, mode):
        cursor_map = {
            ResizeMode.MOVE: Qt.SizeAllCursor,
            ResizeMode.RESIZE_LEFT: Qt.SizeHorCursor,
            ResizeMode.RESIZE_RIGHT: Qt.SizeHorCursor,
            ResizeMode.RESIZE_TOP: Qt.SizeVerCursor,
            ResizeMode.RESIZE_BOTTOM: Qt.SizeVerCursor,
            ResizeMode.RESIZE_TOP_LEFT: Qt.SizeFDiagCursor,
            ResizeMode.RESIZE_BOTTOM_RIGHT: Qt.SizeFDiagCursor,
            ResizeMode.RESIZE_TOP_RIGHT: Qt.SizeBDiagCursor,
            ResizeMode.RESIZE_BOTTOM_LEFT: Qt.SizeBDiagCursor,
        }
        self.setCursor(cursor_map.get(mode, Qt.ArrowCursor))

    def _perform_drag(self, curr_mouse):
        delta = curr_mouse - self._start_mouse
        screen = QApplication.screenAt(curr_mouse) or QApplication.primaryScreen()
        s_rect = screen.availableGeometry()
        
        self.setUpdatesEnabled(False)
        try:
            if self._drag_mode == ResizeMode.MOVE:
                new_pos = self._start_geom.topLeft() + delta
                x = max(s_rect.left(), min(s_rect.right() - self.width(), new_pos.x()))
                y = max(s_rect.top(), min(s_rect.bottom() - self.height(), new_pos.y()))
                self.move(int(x), int(y))
                
            else:
                orig = self._start_geom
                nx, ny, nw, nh = orig.x(), orig.y(), orig.width(), orig.height()
                
                if self._drag_mode in [ResizeMode.RESIZE_LEFT, ResizeMode.RESIZE_TOP_LEFT, ResizeMode.RESIZE_BOTTOM_LEFT]:
                    nw = max(Config.MIN_SIZE, orig.width() - delta.x())
                    # Constrain nx to screen left
                    nx = max(s_rect.left(), orig.right() - nw)
                    # Re-calculate nw based on constrained nx
                    nw = orig.right() - nx
                elif self._drag_mode in [ResizeMode.RESIZE_RIGHT, ResizeMode.RESIZE_TOP_RIGHT, ResizeMode.RESIZE_BOTTOM_RIGHT]:
                    nw = max(Config.MIN_SIZE, orig.width() + delta.x())
                    # Constrain nw to screen right
                    if orig.left() + nw > s_rect.right():
                        nw = s_rect.right() - orig.left()
                    
                if self._drag_mode in [ResizeMode.RESIZE_TOP, ResizeMode.RESIZE_TOP_LEFT, ResizeMode.RESIZE_TOP_RIGHT]:
                    nh = max(Config.MIN_SIZE, orig.height() - delta.y())
                    # Constrain ny to screen top
                    ny = max(s_rect.top(), orig.bottom() - nh)
                    # Re-calculate nh based on constrained ny
                    nh = orig.bottom() - ny
                elif self._drag_mode in [ResizeMode.RESIZE_BOTTOM, ResizeMode.RESIZE_BOTTOM_LEFT, ResizeMode.RESIZE_BOTTOM_RIGHT]:
                    nh = max(Config.MIN_SIZE, orig.height() + delta.y())
                    # Constrain nh to screen bottom
                    if orig.top() + nh > s_rect.bottom():
                        nh = s_rect.bottom() - orig.top()
                
                self.setGeometry(int(nx), int(ny), int(nw), int(nh))
        finally:
            self.setUpdatesEnabled(True)
            self.update()
