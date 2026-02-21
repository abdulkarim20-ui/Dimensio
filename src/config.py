import sys
import os
from PySide6.QtGui import QColor


def resource_path(relative_path: str) -> str:
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Resolve to project root (parent of 'src' folder)
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    return os.path.join(base_path, relative_path)


def get_config_dir() -> str:
    """Get the directory where projects and logs should be stored."""
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    config_dir = os.path.join(base_dir, 'logs')
    if not os.path.exists(config_dir):
        os.makedirs(config_dir, exist_ok=True)
    return config_dir


class Config:
    """Application configuration and styling constants."""
    
    # Paths using resource_path for PyInstaller compatibility
    BASE_DIR = resource_path("")
    ICONS_DIR = resource_path("icons")
    APP_LOGO = resource_path(os.path.join("icons", "app_logo.ico"))
    ICON_SCREENSHOT = resource_path(os.path.join("icons", "screenshot.svg"))
    
    # Directory for persistent data
    USER_DATA = get_config_dir()
    
    # Size constraints
    MIN_SIZE = 10
    MAX_SIZE = 4000
    MARGIN_RESIZE = 20
    
    # Colors
    COLOR_BG = QColor(0, 180, 255, 40)
    COLOR_BORDER = QColor(0, 180, 255, 220)
    COLOR_BORDER_HOVER = QColor(0, 200, 255, 255)
    
    # Preset colors for multi-frame mode
    FRAME_COLORS = [
        (QColor(0, 180, 255, 40), QColor(0, 180, 255, 220)),   # Blue (Default)
        (QColor(46, 204, 113, 40), QColor(46, 204, 113, 220)), # Green
        (QColor(231, 76, 60, 40), QColor(231, 76, 60, 220)),   # Red
        (QColor(155, 89, 182, 40), QColor(155, 89, 182, 220)), # Purple
        (QColor(241, 196, 15, 40), QColor(241, 196, 15, 220)), # Yellow
        (QColor(230, 126, 34, 40), QColor(230, 126, 34, 220)), # Orange
        (QColor(26, 188, 156, 40), QColor(26, 188, 156, 220)), # Teal
    ]

