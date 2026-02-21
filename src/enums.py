"""Enumeration types for the application."""

from enum import Enum


class ResizeMode(Enum):
    """Resize and drag modes for the overlay window."""
    NONE = 0
    MOVE = 1
    RESIZE_LEFT = 2
    RESIZE_RIGHT = 3
    RESIZE_TOP = 4
    RESIZE_BOTTOM = 5
    RESIZE_TOP_LEFT = 6
    RESIZE_TOP_RIGHT = 7
    RESIZE_BOTTOM_LEFT = 8
    RESIZE_BOTTOM_RIGHT = 9
