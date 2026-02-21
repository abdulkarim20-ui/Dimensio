
import os
from PySide6.QtWidgets import QWidget, QLabel, QApplication
from PySide6.QtCore import Qt, QRect, QRectF, QPoint, QSize
from PySide6.QtGui import QPainter, QColor, QPen, QIcon, QPixmap
from PySide6.QtSvg import QSvgRenderer

from ..config import Config


class SpacingOverlay(QWidget):
    """Overlay to draw measurement lines and values between frames."""
    
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool |
            Qt.WindowTransparentForInput
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        
        # Load Icons
        self.icon_h_path = os.path.join(Config.ICONS_DIR, 'spacing-horizontal.svg')
        self.icon_v_path = os.path.join(Config.ICONS_DIR, 'spacing-vertical.svg')
        
        self.renderer_h = QSvgRenderer(self.icon_h_path)
        self.renderer_v = QSvgRenderer(self.icon_v_path)
        
        self.rect1 = None
        self.rect2 = None
        
        # Initialize full screen
        screen = QApplication.primaryScreen()
        self.setGeometry(screen.availableGeometry())

    def update_spacing(self, r1: QRect, r2: QRect):
        """Update the rectangles to measure between and repaint."""
        self.rect1 = r1
        self.rect2 = r2
        
        # Ensure we cover the area needed (or full screen simplicity)
        # Using full screen for now to avoid complex geometry mapping
        screen = QApplication.primaryScreen()
        self.setGeometry(screen.availableGeometry())
        
        self.show()
        self.update()

    def clear(self):
        """Hide measurements."""
        self.rect1 = None
        self.rect2 = None
        self.hide()

    def paintEvent(self, event):
        if not self.rect1 or not self.rect2:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Convert rects to local coordinates (global map)
        # Since this widget is full screen 0,0 is global 0,0 (mostly)
        # We assume measuring on primary screen or handle virtual desktop logic via move()
        # For simplistic "Effort 3", assume we are covering the relevant area.
        
        r1 = self.rect1 # Source
        r2 = self.rect2 # Target
        
        # Color Style
        color = QColor("#FF6666") # Reddish for measurement
        pen = QPen(color)
        pen.setWidth(2)
        pen.setStyle(Qt.DashLine) # Figma uses solid but let's distinguish
        painter.setPen(pen)
        
        font = painter.font()
        font.setFamily("Segoe UI")
        font.setBold(True)
        font.setPixelSize(12)
        painter.setFont(font)
        
        # --- Logic: Calculate Distances ---
        
        # Horizontal
        x_dist = 0
        h_line = None # (x1, y1, x2, y2)
        h_label_pos = None
        
        if r1.right() < r2.left(): # R1 is Left of R2
            dist = r2.left() - r1.right()
            mid_y = r2.center().y() # Align with target center
            
            # Constrain measure line y to be within source Y range if meaningful?
            # Figma logic: Project from Source to Target. 
            # Simple approach: Shortest distance between edges at mid-point.
            
            # If vertically disjoint, use mid point of the vertical overlap extension?
            # Let's just use Target Center Y for the horizontal line
            y = r2.center().y()
            
            # Clamp Y to be visible? 
            # Let's just draw from r1.right to r2.left at r2.center().y()
            
            h_line = (r1.right(), y, r2.left(), y)
            x_dist = dist
            
        elif r1.left() > r2.right(): # R1 is Right of R2
            dist = r1.left() - r2.right()
            y = r2.center().y()
            h_line = (r2.right(), y, r1.left(), y)
            x_dist = dist
            
        # Vertical
        y_dist = 0
        v_line = None # (x1, y1, x2, y2)
        
        if r1.bottom() < r2.top(): # R1 is Above R2
            dist = r2.top() - r1.bottom()
            x = r2.center().x()
            v_line = (x, r1.bottom(), x, r2.top())
            y_dist = dist
            
        elif r1.top() > r2.bottom(): # R1 is Below R2
            dist = r1.top() - r2.bottom()
            x = r2.center().x()
            v_line = (x, r2.bottom(), x, r1.top())
            y_dist = dist
            
        # --- Drawing ---
        
        # Draw Horizontal
        if h_line:
            self._draw_measurement(painter, h_line, x_dist, is_horizontal=True)
            
        # Draw Vertical
        if v_line:
            self._draw_measurement(painter, v_line, y_dist, is_horizontal=False)
            
    def _draw_measurement(self, painter, line, value, is_horizontal):
        painter.save()
        x1, y1, x2, y2 = line
        
        # Color Style for Lines
        color = QColor("#FF6666")
        pen = QPen(color)
        pen.setWidth(2)
        pen.setStyle(Qt.DashLine)
        painter.setPen(pen)
        
        # Draw Line
        painter.drawLine(x1, y1, x2, y2)
        
        # Draw Ends (Ticks)
        tick_len = 4
        if is_horizontal:
            painter.drawLine(x1, y1 - tick_len, x1, y1 + tick_len)
            painter.drawLine(x2, y2 - tick_len, x2, y2 + tick_len)
        else:
            painter.drawLine(x1 - tick_len, y1, x1 + tick_len, y1)
            painter.drawLine(x2 - tick_len, y2, x2 + tick_len, y2)
            
        # Draw Label Pill
        text = f"{value}px"
        font = painter.font()
        font.setFamily("Segoe UI")
        font.setBold(True)
        font.setPixelSize(12)
        painter.setFont(font)
        
        fm = painter.fontMetrics()
        tw = fm.horizontalAdvance(text)
        th = fm.height()
        
        # Icon
        icon_size = 14
        padding = 4
        
        pill_w = tw + icon_size + (padding * 3)
        pill_h = max(th, icon_size) + (padding * 2)
        
        # Center of line
        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2
        
        pill_rect = QRectF(cx - pill_w / 2, cy - pill_h / 2, pill_w, pill_h)
        
        # Pill Background
        painter.setBrush(QColor("#FF6666"))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(pill_rect, 4, 4)
        
        # Icon
        renderer = self.renderer_h if is_horizontal else self.renderer_v
        # Renderer requires target rect to be QRectF
        icon_rect = QRectF(pill_rect.left() + padding, pill_rect.top() + (pill_h - icon_size)/2, icon_size, icon_size)
        renderer.render(painter, icon_rect)
        
        # Text
        painter.setPen(Qt.white)
        # Center text vertically in the pill
        text_rect = QRectF(icon_rect.right() + padding, pill_rect.top(), tw + padding, pill_h)
        painter.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft, text)
        
        painter.restore()
