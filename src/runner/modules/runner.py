from fabric.widgets.wayland import WaylandWindow as Window
from fabric.widgets.scrolledwindow import ScrolledWindow
from fabric.widgets.box import Box
from fabric.widgets.entry import Entry

from pathlib import Path
from modules.desktop_app import DesktopApp
from modules.app_element import AppElement, AppElementList


ENTER_KEY_CODE = 65293
ESCAPE_KEY_CODE = 65307
UP_ARROW_KEY_CODE = 65362
DOWN_ARROW_KEY_CODE = 65364
APPLICATION_DIR = Path("/usr/share/applications")
if not APPLICATION_DIR.exists() or not APPLICATION_DIR.is_dir():
    raise FileNotFoundError("GTK user applications directory does not exist.")


class Runner(Window):
    def __init__(self, **kwargs):
        super().__init__(
            layer="overlay",
            anchor="center",
            exclusivity="none",
            keyboard_mode="exclusive",
            title="gem-runner",
            name="runner-window",
            **kwargs,
        )

        self.connect("key-press-event", self.on_key_press)

        self.search_entry = Entry(
            name="search-entry",
            text="",
        )
        self.search_entry.connect("notify::text", self.on_notify_search_text)

        app_elements = self.get_app_elements()
        self.app_element_list = AppElementList(app_elements)

        self.app_list_box = Box(
            spacing=20,
            orientation="v",
            v_expand=True,
            name="app-list",
            children=self.app_element_list.get_all_elements(),
        )
        self.scrolled_window = ScrolledWindow(
            name="runner-scrolled-window",
            v_align=True,
            child=self.app_list_box,
        )

        self.add(
            Box(
                name="runner-content-box",
                orientation="v",
                children=[
                    self.search_entry,
                    self.scrolled_window,
                ],
            )
        )

        # Grab focus here so the entry is realized and mapped
        self.search_entry.grab_focus()

        self.selected_app_index = 0
        self.select_app_element(index=self.selected_app_index)

    def on_key_press(self, widget, event):
        if event.keyval == ESCAPE_KEY_CODE:
            exit(0)
        elif event.keyval == ENTER_KEY_CODE:
            self.run_selected_app()
        elif event.keyval == UP_ARROW_KEY_CODE:
            new_index = max(0, self.selected_app_index - 1)
            self.select_app_element(new_index)
        elif event.keyval == DOWN_ARROW_KEY_CODE:
            new_index = min(
                len(self.app_list_box.children) - 1, self.selected_app_index + 1
            )
            self.select_app_element(new_index)

        return False

    def select_app_element(self, index):
        if index < 0 or index >= len(self.app_list_box.children):
            raise ValueError(
                "Invalid index passed! If you believe this is an error, check if there are any app elements loaded."
            )

        app_elements = self.app_list_box.children
        previous_selected_app = app_elements[self.selected_app_index]
        previous_selected_app.remove_style_class("selected-element")

        new_selected_app = app_elements[index]
        new_selected_app.add_style_class("selected-element")
        self.selected_app_index = index

        vadjustment = self.scrolled_window.get_vadjustment()
        scroll_multiplier = 90
        vadjustment.set_value(self.selected_app_index * scroll_multiplier)

    def run_selected_app(self):
        selected_app = self.app_list_box.children[self.selected_app_index]
        selected_app.run_app()
        exit(0)

    def on_notify_search_text(self, *args):
        query = self.search_entry.get_text()
        if query == "":
            self.app_list_box.children = self.app_element_list.get_all_elements()
            return

        selected_app = self.app_list_box.children[self.selected_app_index]
        selected_app.remove_style_class("selected-element")
        self.app_list_box.children = self.app_element_list.search(query)
        self.select_app_element(0)

    def get_app_elements(self) -> list[AppElement]:
        paths = self.get_app_paths()

        desktop_apps = self.get_desktop_apps(paths)

        return [
            AppElement(app, lambda name: self.app_element_list.record_history(name))
            for app in desktop_apps
        ]

    def get_app_paths(self) -> list[Path]:
        paths = []

        for posix_path in APPLICATION_DIR.glob("*.desktop"):
            if not posix_path.is_file():
                return

            path = posix_path.resolve()
            paths.append(path)

        return paths

    def get_desktop_apps(self, paths: list[Path]) -> list[DesktopApp]:
        return [DesktopApp.from_path(path) for path in paths]
