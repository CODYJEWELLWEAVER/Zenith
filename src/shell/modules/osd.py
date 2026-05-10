from fabric.widgets.wayland import WaylandWindow as Window
from fabric.widgets.box import Box
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

        self.content = Box(
            orientation="v",
            children=[
                self.volume_scale,
                self.volume_label,
            ],
        )

        self.add(self.content)

        self.media_service.connect("notify::volume", self.on_notify_volume)

        # do allow user to move scale value with clicking
        self.volume_scale.set_sensitive(False)

        self.hide()

    def on_timeout_expired(self, *args):
        self.hide()
        return False

    def on_notify_volume(self, *args):
        if self.timeout_id is not None:
            GLib.source_remove(self.timeout_id)
            self.timeout_id = None

        volume = self.media_service.volume

        self.volume_scale.animate_value(volume)

        self.show()

        self.timeout_id = GLib.timeout_add(TIMEOUT_DELAY, self.on_timeout_expired)
