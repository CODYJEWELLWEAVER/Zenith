from fabric.widgets.scale import Scale
from fabric.core.service import Signal
from fabric.widgets.overlay import Overlay
from fabric.widgets.label import Label

from util.ui import add_hover_cursor

from loguru import logger


class Switch(Scale):
    """
    Binary (On/Off) Switch. "on_toggled" is the callback to perform actions
    when the switch is toggled.
    """

    def __init__(
        self,
        on_toggled: callable | None = None,
        orientation="h",
        name=None,
        visible=True,
        style_classes=["switch-off"],
        tooltip_text=None,
        h_align=None,
        v_align=None,
        h_expand=False,
        v_expand=False,
        size=None,
        **kwargs,
    ):
        super().__init__(
            orientation=orientation,
            increments=[1, 1],
            has_origin=False,
            name=name,
            digits=0,
            visible=visible,
            style_classes=style_classes,
            tooltip_text=tooltip_text,
            h_align=h_align,
            v_align=v_align,
            h_expand=h_expand,
            v_expand=v_expand,
            size=size,
            **kwargs,
        )

        self.on_toggled = on_toggled

        self.connect("value-changed", self._on_value_changed)

        if self.on_toggled is not None:
            self.connect("switch-toggled", self.on_toggled)

        add_hover_cursor(self)

    @Signal("switch-toggled", rtype=bool)
    def switch_toggled(self, is_on: bool) -> None: ...

    def is_on(self):
        return self.value == 1

    def set_is_on(self, is_on: any):
        try:
            value = float(is_on)
        except ValueError:
            value = 0.0

        self.set_value(value)

    def toggle(self):
        self.set_value(0 if self.is_on() else 1)

    def _on_value_changed(self, *args):
        value = self.get_value()

        if value == 1 or value == 0:
            self.emit("switch-toggled", (value == 1))
            if value == 0:
                self.add_style_class("switch-off")
                self.remove_style_class("switch-on")
            else:
                self.add_style_class("switch-on")
                self.remove_style_class("switch-off")
        else:
            binary_value = 0 if value < 0.5 else 1
            # force binary value
            self.set_value(binary_value)
        


class IconSwitch(Overlay):
    """
    Binary (On/Off) Switch with icons. If only "icon" is given, then the icon will be the same for
    both states of the switch.
    """

    def __init__(
        self,
        icon: str,
        icon_off: str | None = None,
        on_toggled=None,
        orientation="h",
        name=None,
        visible=True,
        style_classes=["switch-off"],
        tooltip_text=None,
        h_align="center",
        v_align="center",
        h_expand=False,
        v_expand=False,
        size=None,
        **kwargs,
    ):
        self._switch = Switch(
            on_toggled=on_toggled,
            orientation=orientation,
            name=name,
            visible=visible,
            style_classes=style_classes,
            tooltip_text=tooltip_text,
            h_align=h_align,
            v_align=v_align,
            h_expand=h_expand,
            v_expand=v_expand,
            size=size,
            **kwargs,
        )
        self.icon = Label(
            markup=icon,
            style_classes="switch-icon",
            h_align="start",
            v_align="center",
        )
        self.icon_off = Label(
            markup=icon_off if icon_off is not None else icon,
            style_classes="switch-icon-off",
            h_align="end",
            v_align="center",
        )
        overlays = [self.icon, self.icon_off]
        switch_is_on = self._switch.is_on()
        self.icon_off.set_visible(not switch_is_on)
        self.icon.set_visible(switch_is_on)

        super().__init__(
            child=self._switch,
            overlays=overlays,
            h_align=h_align,
            v_align=v_align,
        )

        self.set_overlay_pass_through(self.icon, True)
        self.set_overlay_pass_through(self.icon_off, True)
        self._switch.connect("switch-toggled", self._update_overlay)

    def set_is_on(self, is_on: any):
        self._switch.set_is_on(is_on)

    def toggle(self):
        self._switch.toggle()

    def _update_overlay(self, _, is_on: bool):
        if is_on:
            self.icon_off.set_visible(False)
            self.icon.set_visible(True)
        else:
            self.icon.set_visible(False)
            self.icon_off.set_visible(True)
