from dataclasses import dataclass, asdict
from typing import List, Dict

@dataclass
class FrameModel:
    id: str
    title: str = "Frame"
    x: int = 100
    y: int = 100
    width: int = 200
    height: int = 200
    bg_color: str = "#2c3e50"
    border_color: str = "#ffffff"
    radii: Dict[str, int] = None
    locked: bool = False
    visible: bool = True
    fill_enabled: bool = True

    def __post_init__(self):
        if self.radii is None:
            self.radii = {"tl": 0, "tr": 0, "bl": 0, "br": 0}

@dataclass
class ProjectModel:
    version: str
    app_version: str
    created_at: str
    frames: List[FrameModel]

    def to_dict(self):
        return {
            "version": self.version,
            "app_version": self.app_version,
            "created_at": self.created_at,
            "frames": [asdict(f) for f in self.frames]
        }
