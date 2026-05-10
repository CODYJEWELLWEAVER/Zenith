from util.singleton import Singleton
from fabric.core import Property, Signal
from fabric.notifications import Notifications, Notification

from gi.repository import GLib


class NotificationService(Notifications, Singleton):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._is_silenced = False

    @Property(bool, default_value=False, flags="readable")
    def is_silenced(self) -> bool:
        return self._is_silenced

    @Signal("silent-mode-changed", arg_types=(bool))
    def silent_mode_changed(self, is_silenced: bool) -> None: ...

    def toggle_silent_mode(self):
        self._is_silenced = not self._is_silenced
        self.emit("silent-mode-changed", self.is_silenced)

    def send_internal_notification(self, variant: GLib.Variant):
        # add a notification internally and
        # emit the notification added signal
        id = self.new_notification_id()
        notification = Notification(id, variant)
        self._notifications[id] = notification
        self.notification_added(id)
