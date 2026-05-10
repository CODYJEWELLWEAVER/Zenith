from fabric.core import Service, Signal, Property
from fabric.audio import Audio as AudioService, AudioStream
from fabric.utils import invoke_repeater, bulk_connect

from util.singleton import Singleton
from config.media import VOLUME_AND_MUTED_UPDATE_INTERVAL, UNSUPPORTED_PLAYER_NAMES
from services.bluetooth import BluetoothService

import pulsectl
from gi.repository import Playerctl, GLib
from loguru import logger


# TODO: add microphone support


MICROSECONDS_PER_SECOND = 1e6


def microseconds_to_seconds(microseconds: int) -> int:
    return microseconds // MICROSECONDS_PER_SECOND


class MediaService(Service, Singleton):
    @Property(float, flags="read-write")
    def volume(self) -> float:
        return self._volume

    @volume.setter
    def volume(self, new_volume: float):
        self._volume = new_volume

    @Property(bool, default_value=False, flags="read-write")
    def is_muted(self) -> bool:
        return self._is_muted

    @is_muted.setter
    def is_muted(self, new_muted: bool):
        self._is_muted = new_muted

    @Property(AudioStream, flags="readable")
    def speaker(self) -> AudioStream:
        return self.audio_service.speaker

    @Property(Playerctl.Player | None, flags="read-write")
    def player(self) -> Playerctl.Player | None:
        return self._player

    @player.setter
    def player(self, new_player: Playerctl.Player | None):
        self._player = new_player

    @Signal("playback-status", arg_types=Playerctl.PlaybackStatus)
    def playback_status(self, status: Playerctl.PlaybackStatus) -> None: ...

    @Signal("metadata", arg_types=GLib.Variant)
    def metadata(self, metadata: GLib.Variant) -> None: ...

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._position_repeater_id = None

        self.pulse = pulsectl.Pulse()
        self.audio_service = AudioService()
        self.player_manager = Playerctl.PlayerManager()
        self.bluetooth_service = BluetoothService.get_instance()

        self.volume = self.get_pulse_volume()
        self.is_muted = self.get_pulse_is_muted()

        invoke_repeater(
            VOLUME_AND_MUTED_UPDATE_INTERVAL,
            self.update_volume_and_is_muted,
        )

        self.audio_service.connect("speaker-changed", self.on_speaker_changed)

        for player_name in self.player_manager.props.player_names:
            self.init_player(player_name)

        self.player = self.get_top_player()

        self.player_manager.connect("name-appeared", self.on_name_appeared)

        bulk_connect(
            self.player_manager,
            {
                "name-appeared": self.on_name_appeared,
                "player-appeared": self.on_player,
                "player-vanished": self.on_player,
            },
        )

    def get_pulse_volume(self) -> float:
        sink = self.pulse.sink_default_get()
        volume = sink.volume.value_flat
        return volume

    def get_pulse_is_muted(self) -> bool:
        sink = self.pulse.sink_default_get()
        is_muted = sink.mute
        return bool(is_muted)

    def update_volume_and_is_muted(self):
        volume = self.get_pulse_volume()
        is_muted = self.get_pulse_is_muted()
        if is_muted:
            volume = 0.0

        if volume != self.volume:
            self.volume = volume
        if is_muted != self.is_muted:
            self.is_muted = is_muted

        return True

    def on_speaker_changed(self, *args):
        self.notify("speaker")

    def init_player(self, player_name):
        if player_name.name in UNSUPPORTED_PLAYER_NAMES:
            return

        player = Playerctl.Player.new_from_name(player_name)
        player.connect("playback-status", self.on_playback_status, self.player_manager)
        player.connect("metadata", self.on_metadata, self.player_manager)
        self.player_manager.manage_player(player)

    def on_playback_status(self, player, status, manager):
        self.playback_status(status)
        if status == Playerctl.PlaybackStatus.PLAYING and self.player is not None:
            # make sure the current track's metadata is dispersed
            self.metadata(self.player.props.metadata)

    def on_metadata(self, player, metadata, manager):
        if metadata is not None:
            self.metadata(metadata)
            # make sure that bluetooth device is shown in control panel
            self.bluetooth_service.notifier("connected-devices")

    def on_name_appeared(self, manager, player_name):
        self.init_player(player_name)

    def on_player(self, manager, player):
        self.player = self.get_top_player()

    def swap_speaker(self):
        """
        Changes audio output by rotating through the sinks
        detected by pulse audio.
        """
        sink_names = [sink.name for sink in self.pulse.sink_list()]
        default_sink = self.pulse.sink_default_get()
        default_sink_idx = sink_names.index(default_sink.name)

        new_sink_idx = (default_sink_idx + 1) % len(sink_names)
        new_sink_name = sink_names[new_sink_idx]

        try:
            new_sink = self.pulse.get_sink_by_name(new_sink_name)
            self.pulse.sink_default_set(new_sink)
        except pulsectl.pulsectl.PulseIndexError:
            logger.error(f"Could not set default sink: {new_sink_name}")

    def get_top_player(self) -> Playerctl.Player | None:
        players = self.player_manager.props.players
        if players is not None and len(players) != 0:
            return self.player_manager.props.players[0]
        else:
            return None

    def toggle_play_pause(self):
        if self.player is None:
            return

        try:
            self.player.play_pause()
        except GLib.GError as e:
            logger.warning(f"Could not play pause: {e}")

    def skip_previous(self):
        if self.player is None:
            return

        try:
            self.player.previous()
        except GLib.GError as e:
            logger.warning(f"Could not skip to previous track: {e}")

    def skip_next(self):
        if self.player is None:
            return

        try:
            self.player.next()
        except GLib.GError as e:
            logger.warning(f"Could not skip to next track: {e}")

    def toggle_mute(self):
        sink = self.pulse.sink_default_get()
        self.pulse.mute(sink, not sink.mute)
