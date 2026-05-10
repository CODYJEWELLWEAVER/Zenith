from typing import Callable
from fabric.widgets.box import Box
from fabric.widgets.image import Image
from fabric.widgets.label import Label
from fabric.widgets.button import Button
from fabric.utils.helpers import exec_shell_command_async, truncate

from modules.desktop_app import DesktopApp
from helpers import add_hover_cursor
import string
from pathlib import Path
from loguru import logger
import json

HISTORY_FILE_PATH = "~/.zenith/runner_history.json"


class AppElement(Button):
    def __init__(self, app: DesktopApp, history_callback: Callable, **kwargs):
        self.app = app
        self.history_callback = history_callback

        super().__init__(style_classes="app-element", on_clicked=self.run_app, **kwargs)

        box = Box(
            style_classes="app-element-button-box",
            spacing=20,
            orientation="h",
        )

        if app.icon_pixbuf is not None:
            box.add(Image(pixbuf=app.icon_pixbuf, style_classes="app-element-pixbuf"))

        box.add(
            Label(style_classes="app-element-name-label", label=truncate(app.name, 24))
        )

        self.add(box)

        add_hover_cursor(self)

    def run_app(self, *args):
        exec_shell_command_async(f"gtk-launch {self.app.path.name}")
        self.history_callback(self.app.name)
        exit(0)


class AppElementList:
    def __init__(self, app_elements: list[AppElement]):
        self._path = None
        self._history = None

        self._init_history_file()

        self.app_table = {element.app.name: element for element in app_elements}

    def get_all_elements(self) -> list[AppElement]:
        elements = []

        if self._history is not None:
            for app_name in self._history:
                elements.append(self.app_table[app_name])

        for element in self.app_table.values():
            if element not in elements:
                elements.append(element)

        return elements

    def search(self, query: str) -> list[AppElement]:
        query = query.lower()
        scored_apps = {}

        for app_name, _ in self.app_table.items():
            score = self._score_name(app_name.lower(), query)
            if score is not None:
                scored_apps[app_name] = score

        scored_apps = sorted(
            scored_apps.items(), key=lambda item: item[1], reverse=False
        )

        return [self.app_table[app_name] for app_name, _ in scored_apps]

    def _score_name(self, name: str, query: str) -> int | None:
        query_score = name.find(query)

        if query_score != -1:
            return query_score

        char_score = 0
        for char in query:
            if char in string.whitespace:
                continue

            char_index = name.find(char)
            if char_index != -1:
                char_score += char_index
            else:
                return None

        return char_score

    def _init_history_file(self) -> None:
        self._path = Path(HISTORY_FILE_PATH)

        try:
            if not self._path.exists():
                json.dump(list(), self._path.open("w"))

            json_file = self._path.open("r+")
        except Exception as e:
            logger.error(
                f"Could not initialize runner history file. Encountered error {e}"
            )
        else:
            with json_file:
                self._history = json.load(json_file)

    def record_history(self, app_name: str) -> None:
        if self._history is None or (len(self._history) > 0 and self._history[0]) == app_name:
            return

        if app_name in self._history:
            # remove current app_name from history if present so we
            # can move it to the front
            app_name_idx = self._history.index(app_name)
            self._history.pop(app_name_idx)

        self._history.insert(0, app_name)

        if len(self._history) > 3:
            self._history = self._history[:3]

        if self._path is not None:
            json.dump(self._history, self._path.open("w"))
