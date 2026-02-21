"""Smart Guides for frame alignment (Figma-style)."""

import os
from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtCore import Qt, QRect, QPoint, QLine, QTimer
from PySide6.QtGui import QPainter, QColor, QPen

class SmartGuides(QWidget):
    """Overlay to draw alignment guide lines between frames."""
    
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
        
        self.active_guides = [] # List of (x1, y1, x2, y2)
        
        # Auto-hide timer for keyboard/scroll/input interactions
        self.hide_timer = QTimer()
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.clear)
        
        # Initialize full screen
        screen = QApplication.primaryScreen()
        self.setGeometry(screen.availableGeometry())


    def update_guides(self, moving_rect: QRect, other_rects: list[QRect], auto_hide=True):
        """Calculate and update alignment guides with pixel-perfect precision."""
        self.active_guides = []
        
        if auto_hide:
            self.hide_timer.start(1000)
        else:
            self.hide_timer.stop()

        # Use boundary-based coordinates for perfect alignment
        # m_x1: Left edge, m_x2: Right edge, m_xc: Horizontal Center
        m_x1 = float(moving_rect.x())
        m_x2 = float(moving_rect.x() + moving_rect.width())
        m_xc = m_x1 + (moving_rect.width() / 2.0)
        
        m_y1 = float(moving_rect.y())
        m_y2 = float(moving_rect.y() + moving_rect.height())
        m_yc = m_y1 + (moving_rect.height() / 2.0)
        
        m_points_x = {"L": m_x1, "C": m_xc, "R": m_x2}
        m_points_y = {"T": m_y1, "C": m_yc, "B": m_y2}
        
        tol = 1.0 # Tolerance for showing guides
        
        # Group participating frames by the shared coordinate (X or Y)
        # matches_x: { coord_value: [ участвующие_границы_y ] }
        matches_x = {} # key: x_coord, value: list of (y1, y2) bounds
        matches_y = {} # key: y_coord, value: list of (x1, x2) bounds

        for r in other_rects:
            if r == moving_rect: continue
            
            r_x1 = float(r.x())
            r_x2 = float(r.x() + r.width())
            r_xc = r_x1 + (r.width() / 2.0)
            
            r_y1 = float(r.y())
            r_y2 = float(r.y() + r.height())
            r_yc = r_y1 + (r.height() / 2.0)
            
            r_points_x = [r_x1, r_xc, r_x2]
            r_points_y = [r_y1, r_yc, r_y2]

            # Check X Alignments
            for m_key, m_val in m_points_x.items():
                for rv in r_points_x:
                    if abs(m_val - rv) <= tol:
                        if m_val not in matches_x: matches_x[m_val] = []
                        # Add both moving and target spans to know how long the line should be
                        matches_x[m_val].append((m_y1, m_y2))
                        matches_x[m_val].append((r_y1, r_y2))

            # Check Y Alignments
            for m_key, m_val in m_points_y.items():
                for rv in r_points_y:
                    if abs(m_val - rv) <= tol:
                        if m_val not in matches_y: matches_y[m_val] = []
                        matches_y[m_val].append((m_x1, m_x2))
                        matches_y[m_val].append((r_x1, r_x2))

        # Convert groups to consolidated draw lines
        for x, spans in matches_x.items():
            y_min = min(s[0] for s in spans)
            y_max = max(s[1] for s in spans)
            self.active_guides.append((x, y_min, x, y_max))

        for y, spans in matches_y.items():
            x_min = min(s[0] for s in spans)
            x_max = max(s[1] for s in spans)
            self.active_guides.append((x_min, y, x_max, y))

        if self.active_guides:
            screen = QApplication.screenAt(moving_rect.center()) or QApplication.primaryScreen()
            s_rect = screen.availableGeometry()
            self.setGeometry(s_rect)
            self.show()
            self.raise_()
            self.update()
        else:
            self.hide()


        if self.active_guides:
            # Match screen geometry to handle multi-monitor or offsets
            # For simplicity, use the screen containing the moving rect
            self.setGeometry(s_rect)
            self.show()
            self.raise_()
            self.update()
        else:
            self.hide()

    def clear(self):
        self.active_guides = []
        self.hide_timer.stop()
        self.hide()


    def paintEvent(self, event):
        if not self.active_guides: return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Custom Smart Guide Yellow
        guide_color = QColor("#fefe00")
        pen = QPen(guide_color, 1)

        painter.setPen(pen)
        
        # Geometry offset for local drawing
        offset = self.geometry().topLeft()
        
        for g in self.active_guides:
            x1, y1, x2, y2 = g
            # Use floating point for crisper 1px lines if needed? 
            # painter.drawLine(QRectF(x1 - offset.x(), y1 - offset.y(), x2 - offset.x(), y2 - offset.y()))
            painter.drawLine(x1 - offset.x(), y1 - offset.y(), x2 - offset.x(), y2 - offset.y())
            
            # Draw tiny circles/points at alignment intersections for extra polish?
            # painter.drawEllipse(QPoint(x1 - offset.x(), y1 - offset.y()), 2, 2)

