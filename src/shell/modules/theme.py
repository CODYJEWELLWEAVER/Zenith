from fabric.widgets.box import Box
from fabric.widgets.scrolledwindow import ScrolledWindow
from fabric.widgets.image import Image
from fabric.widgets.eventbox import EventBox
from fabric.widgets.button import Button
from fabric.widgets.label import Label

from util.ui import add_hover_cursor
from util.helpers import get_pixbuff
from services.theme import ThemeService
import config.icons as Icons

from material_color_utilities import Variant
from pathlib import Path


class ThemeSettings(Box):
    def __init__(self, on_close, **kwargs):
        super().__init__(
            name="theme-settings",
            style_classes="view-box",
            spacing=20,
            visible=True,
            orientation="v",
            v_expand=True,
            v_align="center",
            **kwargs,
        )

        self.service = ThemeService.get_instance()

        self.refresh_button = Button(
            child=Label(
                markup=Icons.refresh,
                style_classes="theme-icon",
            ),
            on_clicked=self.service.load_wallpapers,
        )
        add_hover_cursor(self.refresh_button)

        self.wallpaper_viewer = WallpaperViewer()

        self.theme_options = ThemeOptions()

        self.back_button = Button(
            child=Label(markup=Icons.arrow_right, style_classes="theme-icon"),
            on_clicked=on_close,
        )
        add_hover_cursor(self.back_button)

        self.children = [
            self.theme_options,
            Box(
                spacing=20,
                orientation="h",
                children=[
                    self.refresh_button,
                    self.wallpaper_viewer,
                    self.back_button,
                ],
            ),
        ]


class WallpaperViewer(ScrolledWindow):
    def __init__(self, **kwargs):
        self.service = ThemeService.get_instance()

        self.wallpapers = Box(
            spacing=20,
            orientation="v",
            v_expand=True,
        )
        self.load_wallpapers()

        super().__init__(
            name="wallpaper-viewer",
            style_classes="wallpaper-viewer-scrolled-window",
            child=self.wallpapers,
            v_expand=True,
            **kwargs,
        )

        self.service.connect("notify::wallpapers", self.load_wallpapers)

    def load_wallpapers(self, *args):
        self.wallpapers.children = [
            Wallpaper(path, self.service) for path in self.service.wallpapers
        ]


class Wallpaper(EventBox):
    def __init__(self, wallpaper: Path, service: ThemeService, **kwargs):
        super().__init__(
            events="button-press",
            child=Image(pixbuf=get_pixbuff(str(wallpaper), 600, 520)),
            **kwargs,
        )

        self.service = service
        self.wallpaper = wallpaper

        self.connect("button-press-event", self.on_button_press)
        add_hover_cursor(self)

    def on_button_press(self, widget, event):
        button = event.get_button()[1]

        if button == 1:  # left mouse
            self.service.update_wallpaper(self.wallpaper)


class ThemeOptions(Box):
    def __init__(self, **kwargs):
        self.service = ThemeService.get_instance()

        super().__init__(
            name="theme-options",
            orientation="v",
            v_align="center",
            spacing=20,
            **kwargs,
        )

        toggle_dark_mode_button = DarkModeToggle()

        theme_variant_buttons = [
            ThemeVariantButton(variant=variant)
            for variant in Variant.__members__.values()
        ]

        self.children = [toggle_dark_mode_button] + [
            Box(
                spacing=20,
                orientation="h",
                h_expand=False,
                h_align="center",
                children=theme_variant_buttons[
                    i : min(i + 5, len(theme_variant_buttons))
                ],
            )
            for i in range(0, len(theme_variant_buttons), 5)
        ]


class ThemeVariantButton(Button):
    def __init__(self, variant: Variant, **kwargs):
        self.service = ThemeService.get_instance()
        self.variant = variant
        variant_str = str(variant).rsplit(".")[-1]
        variant_str = variant_str[0] + variant_str[1:].lower()
        variant_label = Label(variant_str, style_classes="theme-variant-label")

        super().__init__(
            h_expand=True,
            h_align="fill",
            style_classes="theme-variant-button",
            child=variant_label,
            on_clicked=self._on_clicked,
            **kwargs,
        )

        add_hover_cursor(self)

    def _on_clicked(self, *args):
        self.service.variant = self.variant


class DarkModeToggle(Button):
    def __init__(self, **kwargs):
        self.service = ThemeService.get_instance()
        self.label = Label(
            "Dark" if self.service.dark else "Light",
        )

        super().__init__(
            style_classes="dark-mode-toggle-button",
            child=self.label,
            on_clicked=self._on_clicked,
            h_align="center",
            **kwargs,
        )

        add_hover_cursor(self)

    def _on_clicked(self, *args):
        self.service.dark = not self.service.dark
        self.label.set_text("Dark" if self.service.dark else "Light")
