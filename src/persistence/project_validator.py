class ProjectValidator:

    REQUIRED_KEYS = {"version", "frames"}

    @staticmethod
    def validate(raw_data: dict):
        missing = ProjectValidator.REQUIRED_KEYS - raw_data.keys()
        if missing:
            raise ValueError(f"Invalid .dio file. Missing keys: {missing}")

        if not isinstance(raw_data["frames"], list):
            raise ValueError("Invalid frames structure.")
