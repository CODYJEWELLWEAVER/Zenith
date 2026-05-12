from loguru import logger
import setproctitle
from fabric import Application
from fabric.utils import get_relative_path, monitor_file
from modules.bar import Bar
from modules.control_panel import ControlPanel
from modules.notifications import NotificationPopUp
from modules.osd import VolumeOSD
from services.theme import ThemeService

from util.helpers import init_data_directory, init_env
from config.storage import STORAGE_DIRECTORY

import asyncio
from gi.events import GLibEventLoopPolicy


@logger.catch
def main():
    init_data_directory()
    init_env()
    logger.add(STORAGE_DIRECTORY + "shell.log", retention="1 days")

    APP_NAME = "Zenith"
    setproctitle.setproctitle(APP_NAME)

    asyncio.set_event_loop_policy(GLibEventLoopPolicy())

    ThemeService.get_instance()
    control_panel = ControlPanel.get_instance()
    bar = Bar()
    notification_pop_up = NotificationPopUp()
    volume_osd = VolumeOSD()

    app = Application(
        APP_NAME,
        bar,
        control_panel,
        notification_pop_up,
        volume_osd,
        open_inspector=False,
    )

    def apply_stylesheet(*_):
        return app.set_stylesheet_from_file(get_relative_path("main.css"))

    style_monitor = monitor_file(get_relative_path("./styles"))
    style_monitor.connect("changed", apply_stylesheet)

    app.set_stylesheet_from_file(get_relative_path("main.css"))

    app.run()


if __name__ == "__main__":
    main()
