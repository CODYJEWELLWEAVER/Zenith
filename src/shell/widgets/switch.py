from fabric.widgets.scale import Scale
from fabric.core.service import Signal
from fabric.widgets.overlay import Overlay
from fabric.widgets.label import Label


class Switch(Scale):
    """
    Binary (On/Off) Switch
    """
    def __init__(
            self, 
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
            **kwargs
    ):
        super().__init__(
            value=0,
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
            **kwargs
        )

        self.connect("value-changed", self._on_value_changed)


    @Signal("switch-toggled", rtype = bool)
    def switch_toggled(self, is_on: bool) -> None: ...


    def is_on(self):
        return (self.value == 1)
    
    
    def set_is_on(self, is_on: any):
        try:
            value = float(is_on)
        except ValueError as e:
            value = 0.0

        self.set_value(value)

    
    def toggle(self):
        self.set_value(0 if self.is_on() else 1)


    def _on_value_changed(self, *args):
        value = self.get_value()
        value = 0 if value < 0.5 else 1
        # force binary value
        self.set_value(value)
        self.emit("switch-toggled", (value == 1))
        if value == 0:
            self.add_style_class("switch-off")
            self.remove_style_class("switch-on")
        else:
            self.add_style_class("switch-on")
            self.remove_style_class("switch-off")


class IconSwitch(Overlay):
    """
    Binary (On/Off) Switch with icons. If only "icon" is given, then the icon will be the same for
    both states of the switch. 
    """
    def __init__(self, icon: str, icon_off: str | None = None, **kwargs):
        self._switch = Switch(**kwargs)
        self.icon = Label(markup=icon, style_classes="switch-icon", h_align="start", v_align="center",)
        self.icon_off = Label(
            markup=icon_off if icon_off is not None else icon, 
            style_classes="switch-icon-off",
            h_align="end",
            v_align="center",
        )
        overlays = [self.icon] if self.icon_off is None else [self.icon, self.icon_off]

        if self.icon_off is not None:
            switch_is_on = self._switch.is_on()
            self.icon_off.set_visible(not switch_is_on)
            self.icon.set_visible(switch_is_on)

        super().__init__(
            child=self._switch,
            overlays=overlays,
        )

        self.set_overlay_pass_through(self.icon, True)
        if icon_off is not None:
            self.set_overlay_pass_through(self.icon_off, True)
            self._switch.connect("switch-toggled", self._on_switch_toggled)


    def set_is_on(self, is_on: any):
        self._switch.set_is_on(is_on)

    
    def toggle(self):
        self._switch.toggle()


    def _on_switch_toggled(self, _, is_on: bool):
        if is_on:
            self.icon_off.set_visible(False)
            self.icon.set_visible(True)
        else:
            self.icon.set_visible(False)
            self.icon_off.set_visible(True)