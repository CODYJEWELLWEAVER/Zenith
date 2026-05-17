from fabric.core.service import Signal, Property
from fabric.widgets.overlay import Overlay
from fabric.widgets.label import Label
from fabric.widgets.eventbox import EventBox

from widgets.animated_scale import AnimatedScale
from util.ui import add_hover_cursor


class SwitchScale(AnimatedScale):
    """
    Binary (On/Off) Switch. "on_toggled" is the callback to perform actions
    when the switch is toggled.
    """

    def __init__(
        self,
        init_enabled=False,
        on_toggled: callable | None = None,
        orientation="h",
        name=None,
        visible=True,
        style_classes=[],
        small=False,
        tooltip_text=None,
        h_align=None,
        v_align=None,
        h_expand=False,
        v_expand=False,
        size=None,
        **kwargs,
    ):
        self.off_style_class = ("" if not small else "small-") + "switch-off"
        self.on_style_class = ("" if not small else "small-") + "switch-on"

        super().__init__(
            bezier_curve=(0.65, 0.29, 0.36, 0.87),
            duration=0.25,
            value=(1 if init_enabled else 0),
            orientation=orientation,
            increments=[1, 1],
            has_origin=False,
            name=name,
            visible=visible,
            style_classes=[self.off_style_class] + style_classes,
            tooltip_text=tooltip_text,
            h_align=h_align,
            v_align=v_align,
            h_expand=h_expand,
            v_expand=v_expand,
            size=size,
            **kwargs,
        )

        self.set_sensitive(False)
        self._enabled = init_enabled

        self.on_toggled = on_toggled

        self.connect("value-changed", self._on_value_changed)

        if self.on_toggled is not None:
            self.connect("switch-toggled", self.on_toggled)

        add_hover_cursor(self)

    @Signal("switch-toggled", rtype=bool)
    def switch_toggled(self, enabled: bool) -> None: ...

    @Property(bool, "read-write", default_value=False)
    def enabled(self) -> bool:
        return self._enabled
    
    @enabled.setter
    def enabled(self, new_enabled: bool):
        self._enabled = new_enabled

    def toggle(self, signal_toggled=True):
        """If no_signal=True, just update the widget, don't signal. This allows you to 
        update the switch based on outside actions without triggering side effects."""
        value = 1 if self.enabled else 0
        self.animate_value(value)
        if signal_toggled:
            self.emit("switch-toggled", self.enabled)
        

    def _on_value_changed(self, *args):
        if self.value == 0:
            self.add_style_class(self.off_style_class)
            self.remove_style_class(self.on_style_class)
        elif self.value == 1:
            self.add_style_class(self.on_style_class)
            self.remove_style_class(self.off_style_class)

class Switch(Overlay):
    def __init__(
        self,
        icon: str,
        icon_off: str | None = None,
        init_enabled=False,
        on_toggled=None,
        orientation="h",
        name=None,
        visible=True,
        small=False,
        style_classes=[],
        tooltip_text=None,
        h_align="center",
        v_align="center",
        h_expand=False,
        v_expand=False,
        size=None,
        **kwargs,
    ):
        self._switch_scale = SwitchScale(
            init_enabled=init_enabled,
            on_toggled=on_toggled,
            orientation=orientation,
            name=name,
            visible=visible,
            small=small,
            style_classes=style_classes,
            tooltip_text=tooltip_text,
            h_align=h_align,
            v_align=v_align,
            h_expand=h_expand,
            v_expand=v_expand,
            size=size,
            **kwargs,
        )

        icon_style_class = ("" if not small else "small-") + "switch-icon"
        icon_off_style_class = ("" if not small else "small-") + "switch-icon-off"

        self.icon = Label(
            markup=icon,
            style_classes=icon_style_class,
            h_align="start",
            v_align="center",
        )
        self.icon_off = Label(
            markup=icon_off if icon_off is not None else icon,
            style_classes=icon_off_style_class,
            h_align="end",
            v_align="center",
        )
        overlays = [self.icon, self.icon_off]
        self.icon.set_visible(self._switch_scale.enabled)
        self.icon_off.set_visible(not self._switch_scale.enabled)

        self.switch_event_box = EventBox(
            events="button-press",
            child=self._switch_scale,
            style_classes="switch-event-box",
        )
        self.switch_event_box.set_above_child(True)
        add_hover_cursor(self.switch_event_box)

        super().__init__(
            child=self.switch_event_box,
            overlays=overlays,
            h_align=h_align,
            v_align=v_align,
        )

        self._switch_scale.animator.connect("finished", self._update_overlay)
        self.switch_event_box.connect("button-press-event", self.toggle)

        self.set_overlay_pass_through(self.icon, True)
        self.set_overlay_pass_through(self.icon_off, True)

    @Property(bool, "readable", default_value=False)
    def is_animating(self) -> bool:
        return self._switch_scale.animator.playing
    
    def _update_overlay(self, *args):
        enabled = self._switch_scale.enabled
        if enabled:
            self.icon_off.set_visible(False)
            self.icon.set_visible(True)
        else:
            self.icon.set_visible(False)
            self.icon_off.set_visible(True)

    def _set_enabled(self, enabled: bool):
        self._switch_scale.enabled = enabled

    def toggle(self, signal_toggled=True):
        self._set_enabled(not self._switch_scale.enabled)
        self._switch_scale.toggle(signal_toggled)