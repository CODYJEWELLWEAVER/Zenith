from fabric import Application
from fabric.utils import monitor_file, get_relative_path
import setproctitle

from modules.runner import Runner


def main():
    APP_NAME = "Zenith-Runner"

    setproctitle.setproctitle(APP_NAME)

    runner = Runner()
    app = Application(APP_NAME, runner)

    def apply_stylesheet(*_):
        return app.set_stylesheet_from_file(get_relative_path("main.css"))

    style_monitor = monitor_file(get_relative_path("./styles"))
    style_monitor.connect("changed", apply_stylesheet)

    app.set_stylesheet_from_file(get_relative_path("main.css"))

    app.run()


if __name__ == "__main__":
    main()
