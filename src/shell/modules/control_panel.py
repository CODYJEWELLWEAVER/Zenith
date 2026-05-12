from fabric.widgets.wayland import WaylandWindow as Window
from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.datetime import DateTime
from fabric.widgets.stack import Stack

from modules.weather import WeatherInfo
from modules.calendar import Calendar
from widgets.custom_image import CustomImage
from config.profile import PROFILE_IMAGE_PATH
from util.helpers import get_system_node_name, get_user_login_name
from util.singleton import Singleton
from modules.network import NetworkOverview, ConnectionSettings
from modules.bluetooth import BluetoothOverview, BluetoothConnections
from modules.notifications import NotificationsOverview
from services.reminders import ReminderService
from modules.reminders import CreateReminderView
from modules.todo import ToDoList
from modules.theme import ThemeSettings
from modules.tools import (
    ScreenshotTool,
    HyprPickerTool,
    SilentModeToggle,
    ThemeSettingsToggle,
)
from util.ui import corner

from gi.repository import GdkPixbuf


class ControlPanel(Window, Singleton):
    def __init__(self, **kwargs):
        super().__init__(
            layer="overlay",
            title="fabric-control-panel",
            name="control-panel",
            anchor="top center",
            exclusivity="none",
            margin="-70px 0px 0px 0px",
            visible=False,
            keyboard_mode="on-demand",
            kwargs=kwargs,
        )

        self.reminder_service = ReminderService.get_instance()

        self.network_overview = NetworkOverview(self.show_network_view)

        self.bluetooth_overview = BluetoothOverview(self.show_bluetooth_view)

        self.network_connection_settings = ConnectionSettings(self.show_main_view)

        self.bluetooth_connection_settings = BluetoothConnections(self.show_main_view)

        self.theme_settings = ThemeSettings(self.show_main_view)

        self.notifications_overview = NotificationsOverview(
            on_switch=self.show_to_do_list
        )

        self.to_do_list = ToDoList(on_switch=self.show_notifications_overview)

        self.profile_image = Box(
            name="profile-image-box",
            h_align="center",
            children=ProfileImage(200, 200),
        )

        self.system_name = Label(
            name="system-name",
            label=f"{get_user_login_name()}@{get_system_node_name()}",
        )

        self.datetime = DateTime(
            formatters="%I:%M %p",
            name="control-panel-time",
        )

        self.weather_info = WeatherInfo(size="large")

        self.profile_box = Box(
            orientation="v",
            spacing=20,
            h_align="center",
            v_align="center",
            children=[
                self.profile_image,
                self.system_name,
                self.datetime,
                self.weather_info,
            ],
        )

        self.calendar = Calendar(
            show_reminder_creation_view=self.show_reminder_creation_view
        )

        self.create_reminder = CreateReminderView(on_close=self.show_main_view)

        self.screenshot_tool = ScreenshotTool()
        self.hyprpicker_tool = HyprPickerTool()
        self.silent_mode_toggle = SilentModeToggle()
        self.theme_tool_toggle = ThemeSettingsToggle(
            on_clicked=self.show_theme_settings_view
        )

        self.productivity_stack = Stack(
            transition_duration=250,
            transition_type="crossfade",
            name="productivity-stack",
            children=[self.notifications_overview, self.to_do_list],
            h_expand=True,
            v_expand=True,
        )

        self.top_row = Box(
            orientation="h",
            spacing=40,
            children=[
                self.profile_box,
                self.calendar,
                self.productivity_stack,
            ],
        )

        self.bottom_row = Box(
            spacing=20,
            orientation="h",
            h_align="center",
            h_expand=True,
            children=[
                self.network_overview,
                self.bluetooth_overview,
                self.screenshot_tool,
                self.hyprpicker_tool,
                self.silent_mode_toggle,
                self.theme_tool_toggle,
            ],
        )

        self.main_view = Box(
            orientation="h",
            children=[
                corner("left", "large"),
                Box(
                    style_classes="view-box",
                    spacing=40,
                    orientation="v",
                    children=[
                        self.top_row,
                        self.bottom_row,
                    ],
                ),
                corner("right", "large"),
            ],
        )

        self.network_connections_view = Box(
            orientation="h",
            children=[
                corner("left", "large"),
                self.network_connection_settings,
                corner("right", "large"),
            ],
        )

        self.create_reminder_view = Box(
            orientation="h",
            children=[
                corner("left", "large"),
                self.create_reminder,
                corner("right", "large"),
            ],
        )

        self.bluetooth_connections_view = Box(
            orientation="h",
            children=[
                corner("left", "large"),
                self.bluetooth_connection_settings,
                corner("right", "large"),
            ],
        )

        self.theme_settings_view = Box(
            orientation="h",
            children=[
                corner("left", "large"),
                self.theme_settings,
                corner("right", "large"),
            ],
        )

        self.main_content_stack = Stack(
            transition_type="over-down-up",
            transition_duration=250,
            interpolate_size=False,  # = True, breaks scrolled windows in views
            h_expand=True,
            v_expand=True,
            children=[
                self.main_view,
                self.network_connections_view,
                self.bluetooth_connections_view,
                self.create_reminder_view,
                self.theme_settings_view,
            ],
        )

        # allow stack to grow and shrink horizontally with each child
        # TODO: there has to be a better way to do this...
        self.main_content_stack.set_hhomogeneous(False)
        self.main_content_stack.set_vhomogeneous(False)

        self.show_main_view()

        self.children = self.main_content_stack

        self.connect("focus-out-event", lambda *_: self.hide())

    def show_main_view(self, *args):
        self.main_content_stack.set_visible_child(self.main_view)

    def show_network_view(self, *args):
        self.main_content_stack.set_visible_child(self.network_connections_view)

    def show_bluetooth_view(self, *args):
        self.main_content_stack.set_visible_child(self.bluetooth_connections_view)

    def show_reminder_creation_view(self, *args):
        self.create_reminder.set_date()
        self.main_content_stack.set_visible_child(self.create_reminder_view)

    def show_theme_settings_view(self, *args):
        self.main_content_stack.set_visible_child(self.theme_settings_view)

    def show_to_do_list(self, *args):
        self.productivity_stack.set_visible_child(self.to_do_list)

    def show_notifications_overview(self, *args):
        self.productivity_stack.set_visible_child(self.notifications_overview)


class ProfileImage(CustomImage):
    def __init__(self, width, height, **kwargs):
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
            PROFILE_IMAGE_PATH, width, height, True
        )

        super().__init__(
            name="profile-image",
            pixbuf=pixbuf,
            **kwargs,
        )
