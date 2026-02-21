import json
from pathlib import Path
from .project_models import ProjectModel, FrameModel
from .project_validator import ProjectValidator
from datetime import datetime
from .. import __version__ as APP_VERSION

class ProjectSerializer:

    FILE_VERSION = "1.0"

    @staticmethod
    def save(path: str, project: ProjectModel):
        path = Path(path)

        if path.suffix != ".dio":
            path = path.with_suffix(".dio")

        with open(path, "w", encoding="utf-8") as f:
            json.dump(project.to_dict(), f, indent=4)

    @staticmethod
    def load(path: str) -> ProjectModel:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
            
        # Validate structure before processing
        ProjectValidator.validate(raw)

        import inspect
        frame_keys = inspect.signature(FrameModel).parameters.keys()

        frames = [
            FrameModel(**{k: v for k, v in frame_dict.items() if k in frame_keys})
            for frame_dict in raw["frames"]
        ]

        return ProjectModel(
            version=raw["version"],
            app_version=raw.get("app_version", "unknown"),
            created_at=raw.get("created_at", ""),
            frames=frames
        )
