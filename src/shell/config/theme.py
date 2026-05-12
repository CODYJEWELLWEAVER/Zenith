import os
from pathlib import Path

from material_color_utilities import Variant

from util.theme import ThemeColors

COLOR_STYLESHEET = os.getcwd() + "/src/shell/styles/colors.css"

WALLPAPERS_DIR = Path("~/Pictures/Wallpapers").expanduser()

CURRENT_WALLPAPER_PATH = Path("~/Pictures/Wallpapers/current.png").expanduser()

DEFAULT_COLOR_THEME = ThemeColors(
    "#8ad7a8",
    "#e6e0ec",
    "#14121a",
    "#222028",
    "#3d3a43",
    "#d0bef6",
    "#ffb4ab",
)

DEFAULT_VARIANT = Variant.RAINBOW

DEFAULT_CONTRAST: float = 0.01

ENV_DARKMODE = "ZENITH_DARKMODE"
ENV_THEME_VARIANT = "ZENITH_THEME_VARIANT"

STRING_TO_VARIANT_MAP = Variant.__members__