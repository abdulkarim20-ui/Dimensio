"""Dimensio - Professional UI Measurement Studio."""

import sys
import os
import ctypes
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

from src.config import Config
from src.manager import FrameManager


def setup_windows_identity():
    """Ensure Windows taskbar correctly groups the window and uses the branding icon."""
    if sys.platform == 'win32':
        try:
            # Set AppUserModelID for proper taskbar grouping
            myappid = 'Dimensio.Studio.Tool.2.0'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception:
            # Fallback for systems where windll might not be available
            pass


def main():
    setup_windows_identity()

    app = QApplication(sys.argv)
    
    # Official Application Identity
    app.setApplicationName("Dimensio")
    app.setOrganizationName("Dimensio")
    app.setApplicationDisplayName("Dimensio")
    
    # Global Icon Setup
    if os.path.exists(Config.APP_LOGO): 
        app.setWindowIcon(QIcon(Config.APP_LOGO))
        
    # Start the core engine
    manager = FrameManager()
    
    # --- Initial Workspace Layout ---
    screen = app.primaryScreen().availableGeometry()
    
    # 1. Create the default primary frame
    manager.create_frame()
    if manager.frames:
        frame = manager.frames[0]
        # Center the frame on the main screen
        frame_rect = frame.frameGeometry()
        frame_rect.moveCenter(screen.center())
        frame.move(frame_rect.topLeft())
    
    # 2. Position the Sidebar control panel
    sidebar_rect = manager.sidebar.frameGeometry()
    # Align to right margin with professional padding
    sidebar_x = screen.right() - sidebar_rect.width() - 40
    sidebar_y = screen.center().y() - (sidebar_rect.height() // 2)
    manager.sidebar.move(sidebar_x, sidebar_y)
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
