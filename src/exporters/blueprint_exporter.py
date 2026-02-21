"""Blueprint Export Logic for Dimensio."""

import os
import logging
from PySide6.QtWidgets import QFileDialog, QMessageBox
from PySide6.QtCore import Qt, QRect, QRectF, QDateTime
from PySide6.QtGui import QPixmap, QPainter, QPen, QPainterPath

logger = logging.getLogger("BlueprintExporter")

class BlueprintExporter:
    """Handles professional PNG wireframe exports."""

    @staticmethod
    def export(frames):
        """Export the frame layout as a high-quality PNG blueprint."""
        try:
            if not frames:
                return
                
            # 1. Calculate bounding box of all frames with padding
            total = QRect()
            for f in frames:
                total = total.united(f.geometry())
            total.adjust(-100, -100, 100, 100)
            
            # 2. Render blueprint on high-contrast canvas
            pix = QPixmap(total.size())
            pix.fill(Qt.white)
            ptr = QPainter(pix)
            ptr.setRenderHint(QPainter.Antialiasing)
            ptr.translate(-total.topLeft())
            
            for f in frames:
                geom = f.geometry()
                ptr.setPen(QPen(Qt.black, 2))
                
                # Draw Frame Shape (handling curves)
                if f.is_radius_active:
                    path = QPainterPath()
                    rf = QRectF(geom).adjusted(0.5, 0.5, -0.5, -0.5)
                    tl, tr, bl, br = f.corner_radii.values()
                    path.moveTo(rf.left() + tl, rf.top())
                    path.lineTo(rf.right() - tr, rf.top())
                    path.arcTo(rf.right() - 2*tr, rf.top(), 2*tr, 2*tr, 90, -90)
                    path.lineTo(rf.right(), rf.bottom() - br)
                    path.arcTo(rf.right() - 2*br, rf.bottom() - 2*br, 2*br, 2*br, 0, -90)
                    path.lineTo(rf.left() + bl, rf.bottom())
                    path.arcTo(rf.left(), rf.bottom() - 2*bl, 2*bl, 2*bl, 270, -90)
                    path.lineTo(rf.left(), rf.top() + tl)
                    path.arcTo(rf.left(), rf.top(), 2*tl, 2*tl, 180, -90)
                    path.closeSubpath()
                    ptr.drawPath(path)
                else: 
                    ptr.drawRect(geom)
                    
                # Draw metadata label
                label = f"{f.title} ({geom.width()} x {geom.height()})"
                ptr.drawText(geom.adjusted(10, 8, -10, -8), Qt.AlignLeft | Qt.AlignTop, label)
            
            ptr.end()
            
            # 3. Save to disk
            default_path = os.path.join(
                os.path.expanduser("~"), 
                "Pictures", 
                f"Dimensio_{QDateTime.currentDateTime().toString('yyyyMMdd_HHmmss')}.png"
            )
            
            path, _ = QFileDialog.getSaveFileName(
                None, 
                "Save Blueprint", 
                default_path, 
                "Images (*.png)"
            )
            
            if path: 
                pix.save(path)
                logger.info(f"Blueprint exported: {path}")
                
        except Exception as e:
            logger.error(f"Export failed: {e}", exc_info=True)
            QMessageBox.critical(None, "Export Error", f"Could not save blueprint: {e}")
