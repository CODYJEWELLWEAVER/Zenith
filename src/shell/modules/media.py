from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.button import Button
from fabric.utils import truncate, bulk_connect, exec_shell_command_async

from gi.repository import Playerctl, GLib

from services.media import MediaService
from widgets.switch import IconSwitch
from util.ui import add_hover_cursor
from config.media import HEADPHONES
import config.icons as Icons


class MediaControl(Box):
    def __init__(self, **kwargs):
        super().__init__(
            name="media-control",
            spacing=20,
            v_align="center",
            h_align="center",
            **kwargs,
        )

        self.media_service = MediaService.get_instance()

        self.title = Label(
            name="info-box-title",
        )
        self.artist = Label(
            name="info-box-artist",
        )
        self.media_info = Box(
            name="info-box",
            orientation="v",
            v_align="center",
            v_expand=True,
            h_align="center",
            children=[self.title, self.artist],
            visible=False,
        )

        self.output_control = Button(
            child=Label(style_classes="media-control-icon", markup=Icons.speaker),
            on_clicked=lambda *_: self.media_service.swap_speaker(),
        )
        add_hover_cursor(self.output_control)

        self.prev_track_control = Button(
            child=Label(style_classes="media-control-icon", markup=Icons.skip_prev),
            on_clicked=lambda *_: self.media_service.skip_previous(),
        )
        add_hover_cursor(self.prev_track_control)

        self.play_control_label = Label(
            style_classes="media-control-icon", markup=Icons.play
        )
        self.play_control = Button(
            child=self.play_control_label,
            on_clicked=lambda *_: self.media_service.toggle_play_pause(),
        )
        add_hover_cursor(self.play_control)

        self.next_track_control = Button(
            child=Label(style_classes="media-control-icon", markup=Icons.skip_next),
            on_clicked=lambda *_: self.media_service.skip_next(),
        )
        add_hover_cursor(self.next_track_control)

        self.mute_switch = MuteSwitch()

        self.launch_settings = Button(
            child=Label(
                markup=Icons.adjustments_cog, style_classes="media-control-icon"
            ),
            on_clicked=lambda *_: exec_shell_command_async("pavucontrol"),
        )
        add_hover_cursor(self.launch_settings)

        self.children = [
            self.launch_settings,
            self.media_info,
            self.output_control,
            self.prev_track_control,
            self.play_control,
            self.next_track_control,
            self.mute_switch,
        ]

        bulk_connect(
            self.media_service,
            {
                "notify::speaker": self.on_notify_speaker,
                "playback-status": self.on_playback_status,
                "metadata": self.on_metadata,
                "notify::is-muted": self.on_notify_is_muted,
            },
        )

    def on_playback_status(self, service, status: Playerctl.PlaybackStatus):
        if status == Playerctl.PlaybackStatus.PLAYING:
            label = Label(style_classes="media-control-icon", markup=Icons.pause)
        else:
            label = Label(style_classes="media-control-icon", markup=Icons.play)

        self.play_control.children = label

    def on_metadata(self, service, metadata: GLib.Variant):
        """
        Update media info on bar and on media panel
        """
        self.update_title(metadata)

        self.update_artist(metadata)

        self.update_media_info_visibility(metadata)

    def update_title(self, metadata: dict):
        if "xesam:title" in metadata.keys() and metadata["xesam:title"] != "":
            self.media_info.set_property("visible", True)

            title = truncate(metadata["xesam:title"], 36)
            self.title.set_property("label", title)
            self.title.set_property("visible", True)
        else:
            self.title.set_property("visible", False)

    def update_artist(self, metadata: dict):
        if "xesam:artist" in metadata.keys() and metadata["xesam:artist"] != [""]:
            self.media_info.set_property("visible", True)

            artist = truncate(metadata["xesam:artist"][0], 36)
            self.artist.set_property("label", artist)
            self.artist.set_property("visible", True)
        else:
            self.artist.set_property("visible", False)

    def update_media_info_visibility(self, metadata: dict):
        if (
            "xesam:title" in metadata.keys()
            and metadata["xesam:title"] == ""
            and "xesam:artist" in metadata.keys()
            and metadata["xesam:artist"] == [""]
        ):
            self.media_info.set_property("visible", False)

    def on_notify_speaker(self, *args):
        if self.media_service.speaker.name in HEADPHONES:
            icon = Icons.headphones
        else:
            icon = Icons.speaker

        label = Label(style_classes="media-control-icon", markup=icon)

        self.output_control.children = label

    def on_notify_is_muted(self, *args):
        self.mute_switch.set_is_on(not self.media_service.is_muted)


class MuteSwitch(IconSwitch):
    def __init__(self, **kwargs):
        self.media_service = MediaService.get_instance()

        super().__init__(
            small=True,
            icon=Icons.volume_high,
            icon_off=Icons.volume_muted,
            on_toggled=self._on_toggled,
            **kwargs,
        )

        self.set_is_on(not self.media_service.is_muted)

    def _on_toggled(self, w, enabled):
        # ensure that we are consistent with the media service, enabled = not muted
        # this ensures we do not toggle mute if the switch was changed as a result of
        # mute that did not originate from a click on the switch
        if enabled == self.media_service.is_muted:
            self.media_service.toggle_mute()
