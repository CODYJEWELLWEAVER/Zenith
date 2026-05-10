from pathlib import Path
from helpers import get_app_icon_pixbuf


ICON_WIDTH = 50
ICON_HEIGHT = 50


class DesktopApp:
    def __init__(self, name: str, path: Path, icon: str):
        self.name = name
        self.path = path
        self.icon_pixbuf = (
            get_app_icon_pixbuf(icon, ICON_WIDTH, ICON_HEIGHT)
            if icon is not None
            else None
        )

    @classmethod
    def from_path(cls, path: Path):
        if path.exists():
            name = None
            icon = None

            with path.open() as file:
                for line in file.readlines():
                    line = line.rstrip()
                    components = line.split("=", maxsplit=1)
                    if len(components) != 2:
                        continue

                    prop, value = components

                    if prop == "Name":
                        name = value
                    elif prop == "Icon":
                        icon = value

                    if name is not None and icon is not None:
                        break

            return cls(name, path, icon)
