from typing import Callable
from fabric.widgets.button import Button
from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.utils.helpers import exec_shell_command_async

import config.icons as Icons
from util.ui import add_hover_cursor
from services.notifications import NotificationService

from gi.repository import GLib


class ToolButton(Button):
    def __init__(self, icon: str, label: str | None, on_clicked: Callable, **kwargs):
        children = [
            Label(
                markup=icon,
                style_classes="tool-icon",
            ),
        ]

        if label is not None:
            children.append(
                Label(
                    label=label,
                    style_classes="tool-label",
                )
            )

        super().__init__(
            style_classes="tool-button",
            child=Box(
                spacing=10,
                orientation="h",
                h_align="center",
                v_align="center",
                children=children,
            ),
            on_clicked=on_clicked,
            **kwargs,
        )

        add_hover_cursor(self)


class ScreenshotTool(ToolButton):
    def __init__(self, **kwargs):
        super().__init__(
            icon=Icons.camera,
            label="Screenshot",
            on_clicked=lambda *_: exec_shell_command_async("hyprshot -m region"),
            **kwargs,
        )


class HyprPickerTool(ToolButton):
    def __init__(self, **kwargs):
        super().__init__(
            icon=Icons.color_palette,
            label="HyprPicker",
            on_clicked=self.on_clicked,
            **kwargs,
        )

        self.notification_service = NotificationService.get_instance()

    def on_clicked(self, *args):
        exec_shell_command_async("hyprpicker", self.send_notification)

    def send_notification(self, color: str):
        variant = GLib.Variant(
            # s = string, i = signed int, u = unsigned int, as = string array
            "(sisssasasiu)",
            (
                "HyprPicker",  # app name
                -1,  # replaces_id
                "",  # app_icon
                "Color:",  # summary
                f"<span color='{color}' font-size='200%'>{color}</span>",  # body
                [],  # actions
                [],  # hints
                -1,  # timeout
                1,  # urgency
            ),
        )

        self.notification_service.send_internal_notification(variant)


class SilentModeToggle(ToolButton):
    def __init__(self, **kwargs):
        super().__init__(
            icon=Icons.mood_silence,
            label="Silent Mode",
            on_clicked=self.on_clicked,
            **kwargs,
        )

        self.notification_service = NotificationService.get_instance()

    def on_clicked(self, *args):
        self.notification_service.toggle_silent_mode()

        if self.notification_service.is_silenced:
            self.add_style_class("silent-mode-on")
        else:
            self.remove_style_class("silent-mode-on")


class ThemeSettingsToggle(ToolButton):
    def __init__(self, **kwargs):
        super().__init__(icon=Icons.brush, label=None, **kwargs)
