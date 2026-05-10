from gi.repository import GdkPixbuf, Gtk, Gdk
from loguru import logger


def get_app_icon_pixbuf(
    name: str, width: int, height: int, preserve_aspect_ratio: bool = True
) -> GdkPixbuf.Pixbuf:
    icon_theme = Gtk.IconTheme.get_default()
    icon_info = icon_theme.lookup_icon(name, width, 0)  # No Flags
    if icon_info is not None:
        icon_path = icon_info.get_filename()
        try:
            icon_pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                icon_path, width, height, preserve_aspect_ratio
            )
            return icon_pixbuf
        except Exception as e:
            logger.error(f"{e}")
            return None

    return None


def add_hover_cursor(widget):
    """
    Changes cursor when hovering over widget and resets when moving away from widget.
    Credit to https://github.com/Axenide for this.
    """
    widget.add_events(Gdk.EventMask.ENTER_NOTIFY_MASK | Gdk.EventMask.LEAVE_NOTIFY_MASK)
    widget.connect(
        "enter-notify-event",
        lambda w, event: w.get_window().set_cursor(
            Gdk.Cursor.new_from_name(Gdk.Display.get_default(), "pointer")
        ),
    )
    widget.connect(
        "leave-notify-event", lambda w, event: w.get_window().set_cursor(None)
    )
