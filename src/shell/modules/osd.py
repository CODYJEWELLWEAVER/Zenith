from fabric.widgets.wayland import WaylandWindow as Window
from fabric.widgets.overlay import Overlay
from fabric.widgets.label import Label

from widgets.animated_scale import AnimatedScale
from services.media import MediaService
import config.icons as Icons
from config.osd import TIMEOUT_DELAY

from gi.repository import GLib


class VolumeOSD(Window):
    def __init__(self, **kwargs):
        super().__init__(
            layer="overlay",
            anchor="center",
            exclusivity="none",
            h_align="center",
            v_align="center",
            visible=False,
            **kwargs,
        )

        self.timeout_id = None

        self.media_service = MediaService.get_instance()

        self.volume_scale = AnimatedScale(
            value=self.media_service.volume,
            name="volume-osd-scale",
        )
        self.volume_label = Label(
            markup=Icons.volume_high, style_classes="volume-osd-label"
        )
        self.muted_label = Label(
            markup=Icons.volume_muted, style_classes="volume-osd-label"
        )

        self.volume_label.set_visible(not self.media_service.is_muted)
        self.muted_label.set_visible(self.media_service.is_muted)

        self.content = Overlay(
            child=self.volume_scale,
            overlays=[
                self.volume_label,
                self.muted_label,
            ],
        )

        self.add(self.content)

        self.media_service.connect("notify::volume", self._on_notify_volume)
        self.media_service.connect("notify::is-muted", self._on_notify_is_muted)

        # do not allow user to move scale value with clicking
        self.volume_scale.set_sensitive(False)

        self.hide()

    def _on_timeout_expired(self, *args):
        self.hide()
        return False

    def _on_notify_volume(self, *args):
        if self.timeout_id is not None:
            GLib.source_remove(self.timeout_id)
            self.timeout_id = None

        volume = self.media_service.volume

        self.volume_scale.animate_value(volume)

        self.show()

        self.timeout_id = GLib.timeout_add(TIMEOUT_DELAY, self._on_timeout_expired)

    def _on_notify_is_muted(self, *args):
        self.volume_label.set_visible(not self.media_service.is_muted)
        self.muted_label.set_visible(self.media_service.is_muted)
