from fabric.core.service import Service, Property, Signal
from fabric.utils.helpers import exec_shell_command_async, invoke_repeater, exec_shell_command

from config.theme import DEFAULT_COLOR_THEME, DEFAULT_CONTRAST, DEFAULT_VARIANT
from util.singleton import Singleton
from util.theme import (
    ThemeColors,
)

from material_color_utilities import Theme, theme_from_image, Variant
from config.theme import COLOR_STYLESHEET, CURRENT_WALLPAPER_PATH, WALLPAPERS_DIR
import re
from PIL import Image
from pathlib import Path
from loguru import logger
import asyncio

REFRESH_WALLPAPERS_TIMEOUT = 60000


class ThemeService(Service, Singleton):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._loop = asyncio.get_event_loop()

        self._wallpaper = CURRENT_WALLPAPER_PATH
        self._colors = DEFAULT_COLOR_THEME
        self._variant = DEFAULT_VARIANT
        self._contrast = DEFAULT_CONTRAST
        self._dark = True
        self._wallpapers = []

        self.load_wallpapers()
        self.update_theme()

        self.connect("theme-changed", self.update_theme)

        invoke_repeater(
            REFRESH_WALLPAPERS_TIMEOUT, self.load_wallpapers, initial_call=False
        )

    @Signal
    def theme_changed(self) -> None: ...

    @Property(ThemeColors, flags="read-write")
    def colors(self) -> ThemeColors:
        return self._colors

    @colors.setter
    def colors(self, colors: ThemeColors) -> None:
        self._colors = colors
        self.theme_changed()
        self.notify("colors")

    @Property(Variant, flags="read-write")
    def variant(self) -> Variant:
        return self._variant

    @variant.setter
    def variant(self, variant: Variant) -> None:
        self._variant = variant
        self.theme_changed()
        self.notify("variant")

    @Property(float, "read-write")
    def contrast(self) -> float:
        return self._contrast

    @contrast.setter
    def contrast(self, contrast: float) -> None:
        self._contrast = contrast
        self.theme_changed()
        self.notify("contrast")

    @Property(bool, "read-write", default_value=True)
    def dark(self) -> bool:
        return self._dark

    @dark.setter
    def dark(self, dark: bool) -> None:
        self._dark = dark
        self.theme_changed()
        self.notify("dark")

    @Property(list[Path], "read-write")
    def wallpapers(self) -> list[Path]:
        return self._wallpapers

    @wallpapers.setter
    def wallpapers(self, new_wallpapers: list[Path]) -> None:
        self._wallpapers = new_wallpapers
        self.notify("wallpapers")

    def update_theme(self, *args):
        async def _update():
            self._colors = self.create_colortheme_from_image(
                self._wallpaper.resolve(), self.contrast, self.variant, self.dark
            )
            self.update_color_styles()

        self._loop.create_task(_update())

    def create_colortheme_from_image(
        self, image_path: str, contrast: float, variant: Variant, use_dark: bool
    ) -> Theme:
        image = Image.open(image_path)
        theme = theme_from_image(image, contrast=contrast, variant=variant)

        if use_dark:
            mat_colors = theme.schemes.dark
        else:
            mat_colors = theme.schemes.light

        return ThemeColors(
            mat_colors.primary,
            mat_colors.on_surface,
            mat_colors.background,
            mat_colors.surface_container,
            mat_colors.surface_bright,
            mat_colors.tertiary,
            mat_colors.error,
        )

    def update_color_styles(self) -> None:
        try:
            with open(COLOR_STYLESHEET, "r") as color_stylesheet:
                styles = color_stylesheet.read()

            hex_pattern = "#[0-9a-zA-Z]{6,8}"
            styles = re.sub(
                rf"--foreground: {hex_pattern}",
                f"--foreground: {self.colors.foreground}",
                styles,
            )
            styles = re.sub(
                rf"--foreground-alt: {hex_pattern}",
                f"--foreground-alt: {self.colors.foreground_alt}",
                styles,
            )
            styles = re.sub(
                rf"--background: {hex_pattern}",
                f"--background: {self.colors.background}",
                styles,
            )
            styles = re.sub(
                rf"--background-alt: {hex_pattern}",
                f"--background-alt: {self.colors.background_alt}",
                styles,
            )
            styles = re.sub(
                rf"--background-highlight: {hex_pattern}",
                f"--background-highlight: {self.colors.background_highlight}",
                styles,
            )
            styles = re.sub(
                rf"--highlight: {hex_pattern}",
                f"--highlight: {self.colors.highlight}",
                styles,
            )
            styles = re.sub(
                rf"--status-fail: {hex_pattern}",
                f"--status-fail: {self.colors.error}",
                styles,
            )

            with open(COLOR_STYLESHEET, "w") as color_stylesheet:
                color_stylesheet.write(styles)

        except Exception as e:
            print(f"Error: Could not update color styles! {e}")

    def hyprpaper_update(self):
        exec_shell_command(f"hyprctl hyprpaper wallpaper , {CURRENT_WALLPAPER_PATH},")

    def update_wallpaper(self, new_path: Path) -> None:
        # gotta trick hyprpaper into thinking the symlink is a photo
        if " " in str(new_path):
            logger.error("New wallpaper path contains a space. Spaces are not allowed in wallpaper paths.")
        proc, _ = exec_shell_command_async(
            f"ln -sf {str(new_path)} {self._wallpaper}"
        )

        def on_sm_created(*args):
            self.theme_changed()
            self.hyprpaper_update()

        if proc is not None:
            proc.wait_async(None, on_sm_created, None)

    def load_wallpapers(self, *args) -> None:
        if not WALLPAPERS_DIR.exists() or not WALLPAPERS_DIR.is_dir():
            logger.error("WALLPAPER DIRECTORY DOES NOT EXIST!")
            return []

        self.wallpapers = [path for path in WALLPAPERS_DIR.iterdir()]
