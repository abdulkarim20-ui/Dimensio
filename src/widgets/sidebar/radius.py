"""Radius and curve controls."""

import os
from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QFrame, QGridLayout, QGraphicsOpacityEffect
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
from ...config import Config
from ..file_menu import ToggleSwitch
from .inputs import FigmaInput
from .tooltips import ToolTipFilter

class RadiusPanel(QFrame):
    """Integrated Radius Panel inside Sidebar with Figma-style controls."""
    radius_changed = Signal(dict)
    height_delta_changed = Signal(int)

    def __init__(self, theme_color="#2ecc71", initial_radius=0, parent=None):
        super().__init__(parent)
        self.theme_color = theme_color
        self.global_radius = initial_radius
        self.radii = {"tl": initial_radius, "tr": initial_radius, "bl": initial_radius, "br": initial_radius}
        self._is_advanced = False
        
        self.tooltip_filter = ToolTipFilter(self)
        
        self.setStyleSheet("background: transparent; border: none;")
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 14)
        layout.setSpacing(12)
        
        # 1. Radius Header
        main_row = QHBoxLayout()
        main_row.setSpacing(8)
        
        lbl_icon = QLabel()
        lbl_icon.setFixedSize(16, 16)
        rad_icon = os.path.join(Config.ICONS_DIR, "radius-curve.svg")
        if os.path.exists(rad_icon):
            lbl_icon.setPixmap(QIcon(rad_icon).pixmap(14, 14))
        
        self.global_input = FigmaInput(str(self.global_radius))
        self.global_input.value_changed.connect(self._on_global_changed)
        
        self.lbl_independent = QLabel("Advanced")
        self.lbl_independent.setStyleSheet("color: #666; font-size: 10px; font-weight: 800; font-family: 'Segoe UI'; text-transform: uppercase; letter-spacing: 0.5px;")
        
        self.toggle_independent = ToggleSwitch(active_color=self.theme_color)
        self.toggle_independent.toggled.connect(self._on_independent_toggled)
        
        main_row.addWidget(lbl_icon)
        main_row.addWidget(self.global_input)
        main_row.addStretch()
        main_row.addWidget(self.lbl_independent)
        main_row.addWidget(self.toggle_independent)
        layout.addLayout(main_row)

        # 2. Grid for individual radii
        self.grid_container = QWidget()
        grid = QGridLayout(self.grid_container)
        grid.setContentsMargins(0, 4, 0, 0)
        grid.setSpacing(10)
        
        self.inputs = {}
        positions = {
            "tl": (0, 0, "Top Left"), 
            "tr": (0, 1, "Top Right"),
            "bl": (1, 0, "Bottom Left"), 
            "br": (1, 1, "Bottom Right")
        }
        
        for key, (r, c, full_name) in positions.items():
            cell = QHBoxLayout()
            cell.setSpacing(6)
            
            lbl = QLabel(key.upper())
            lbl.setFixedWidth(18)
            lbl.setStyleSheet(f"color: {self.theme_color}; font-size: 9px; font-weight: 800; font-family: 'Segoe UI'; border: 1px solid #333; border-radius: 2px; padding: 1px;")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setToolTip(full_name)
            lbl.installEventFilter(self.tooltip_filter)
            
            inp = FigmaInput(str(self.radii[key]))
            inp.value_changed.connect(lambda v, k=key: self._on_individual_changed(k, v))
            
            cell.addWidget(lbl)
            cell.addWidget(inp)
            grid.addLayout(cell, r, c)
            self.inputs[key] = inp
            
        layout.addWidget(self.grid_container)
        
        self.grid_opacity = QGraphicsOpacityEffect(self.grid_container)
        self.grid_opacity.setOpacity(0.2)
        self.grid_container.setGraphicsEffect(self.grid_opacity)
        self.grid_container.setEnabled(False)
        
        layout.addStretch()

    def set_radii(self, radii):
        self.radii = radii.copy()
        is_uniform = len(set(radii.values())) <= 1
        
        if not is_uniform and not self._is_advanced:
            self.toggle_independent.set_active(True)
        
        for key, val in radii.items():
            if key in self.inputs:
                self.inputs[key].blockSignals(True)
                self.inputs[key].setText(str(val))
                self.inputs[key].blockSignals(False)
        
        ref_val = list(radii.values())[0] if radii else 0
        self.global_input.blockSignals(True)
        self.global_input.setText(str(ref_val))
        self.global_input.blockSignals(False)
        self.global_radius = ref_val

    def _on_global_changed(self, value):
        self.global_radius = value
        if not self._is_advanced:
            self.radii = {"tl": value, "tr": value, "bl": value, "br": value}
            for k, v in self.radii.items():
                if k in self.inputs:
                    self.inputs[k].blockSignals(True)
                    self.inputs[k].setText(str(v))
                    self.inputs[k].blockSignals(False)
            self.radius_changed.emit(self.radii)

    def _on_independent_toggled(self, active):
        self._is_advanced = active
        self.grid_container.setEnabled(active)
        self.grid_opacity.setOpacity(1.0 if active else 0.2)
        
        self.lbl_independent.setStyleSheet(f"color: {self.theme_color if active else '#666'}; font-size: 10px; font-weight: 800; font-family: 'Segoe UI'; text-transform: uppercase; letter-spacing: 0.5px;")
        self.updateGeometry()
        self.global_input.setEnabled(not active)
        
        self.layout().setSpacing(4 if active else 10)
        
        bg = "#080808" if active else "transparent"
        brdr = "#333" if active else "transparent"
        self.global_input.setStyleSheet(f"""
            QLineEdit {{
                background: {bg};
                border: 1px solid {brdr};
                border-radius: 3px;
                color: #888;
            }}
        """)
        
        self.height_delta_changed.emit(0) 
        
        if not active:
            val = self.global_radius
            self.radii = {"tl": val, "tr": val, "bl": val, "br": val}
            for k, v in self.radii.items():
                if k in self.inputs: self.inputs[k].setText(str(v))
            self.radius_changed.emit(self.radii)
        else:
            self.radius_changed.emit(self.radii)

    def _on_individual_changed(self, key, value):
        self.radii[key] = value
        if self._is_advanced:
            self.radius_changed.emit(self.radii)
