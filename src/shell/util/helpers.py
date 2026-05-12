from gi.repository import Gtk, GdkPixbuf
import os
import platform
import locale
from pathlib import Path

from loguru import logger

from config.storage import STORAGE_DIRECTORY
from fabric.utils import exec_shell_command, exec_shell_command_async


ENV_VAR_PATH = Path(".env")


def get_file_path_from_mpris_url(mpris_url: str) -> str:
    return Path.from_uri(mpris_url).__fspath__()


def get_pixbuff(
    path: str, width: int, height: int, preserve_aspect_ration: bool = True
) -> GdkPixbuf.Pixbuf | None:
    try:
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
            path, width, height, preserve_aspect_ration
        )
        return pixbuf
    except Exception as e:
        logger.error(f"{e}")
        return None


def get_app_icon_pixbuf(
    name: str, width: int, height: int, preserve_aspect_ratio: bool = True
) -> GdkPixbuf.Pixbuf | None:
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


def get_user_login_name():
    login_name = os.getenv("LOGNAME")
    return login_name if login_name else "user"


def get_system_node_name():
    node_name = platform.node()
    return node_name if node_name != "" else "system"


def get_country_code():
    try:
        language_code = locale.getlocale()[0]
        return language_code.split("_")[1]
    except IndexError:
        logger.warning("Could not find current country code, defaulting to US.")
        return "US"


def init_data_directory():
    storage_directory = Path(STORAGE_DIRECTORY)
    storage_directory.mkdir(exist_ok=True)


def init_env():
    if not ENV_VAR_PATH.exists():
        with open(ENV_VAR_PATH.resolve(), mode="x") as env_file:
            env_file.writelines(
                [
                    "export ZENITH_DARKMODE=1\n",
                    "export ZENITH_THEME_VARIANT=MONOCHROME\n",
                ]
            )

        exec_shell_command(f"source {ENV_VAR_PATH.resolve()}")


def set_env_var(name: str, old_value_pattern: str, value: str) -> None:
    exec_shell_command_async(
        f"sed -i -E 's/{name}={old_value_pattern}/{name}={value}/g' {ENV_VAR_PATH.resolve()}"
    )


def set_env_var_bool(name: str, value: bool) -> None:
    if isinstance(value, bool):
        str_value = "1" if value else "0"
        set_env_var(name, "[0-1]", str_value)
    else:
        logger.error(
            f"Incorrect value passed for bool env var: {name}, value: {value}."
        )


def set_env_var_str(name: str, value: str) -> None:
    if isinstance(value, str):
        set_env_var(name, "[A-Z]+", value)
    else:
        logger.error(
            f"Incorrect value passed for string env var: {name}, value: {value}."
        )


def get_env_var_bool(name: str) -> bool:
    var = os.environ.get(name)
    if var is None:
        logger.warning(
            f"""Could not get bool env var: {name}. Defaulting to True. This may cause unexpected behaviour. 
            Check Zenith/.env. You can regenerate the .env file by deleting if it is corrupted."""
        )
        return True
    else:
        return int(var) == 1


def get_env_var_str(name: str, default: str) -> str:
    var = os.environ.get(name)
    if var is None:
        logger.warning(
            f"""Could not get string env var: {name}. Defaulting to {default}. This may cause unexpected behaviour. 
            Check Zenith/.env. You can regenerate the .env file by deleting if it is corrupted."""
        )
        return default
    else:
        return var
