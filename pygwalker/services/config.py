import os
import json
from typing import List, Optional, Dict
from functools import lru_cache

from pygwalker.utils.randoms import generate_hash_code

from appdirs import user_config_dir


DEFAULT_CONFIG = {
    "privacy": "events",
    "kanaries_token": "",
}
CONFIG_KEYS = list(DEFAULT_CONFIG.keys())
APP_DIR = user_config_dir("pygwalker")
CONFIG_PATH = os.path.join(APP_DIR, "config.json")
USER_CONFIG_PATH = os.path.join(APP_DIR, "user_config.json")


class ConfigItem:
    """Configuration item."""
    def __init__(
        self,
        name: str,
        type_list: List[str],
        default: Optional[str] = None,
        description: str = ''
    ) -> None:
        self.name = name
        self.type_list = type_list
        self.default = default
        self.description = description

    def __str__(self) -> str:
        return f"- {self.name}  {self.type_list} (default: {self.default}).{self.description}"


privacy_item = ConfigItem(
    "privacy",
    ["offline", "update-only", "events"],
    default="events",
    description="""
    "offline": fully offline, no data is send or api is requested
    "update-only": only check whether this is a new version of pygwalker to update
    "events": share which events about which feature is used in pygwalker, it only contains events data about which feature you arrive for product optimization. No DATA YOU ANALYSIS IS SEND.
    """
)
kanati_token_item = ConfigItem(
    "kanaries_token",
    ["your kanaries token"],
    default="empty string",
    description="""
    your kanaries token, you can get it from https://kanaries.net.
    refer: https://space.kanaries.net/t/how-to-get-api-key-of-kanaries.
    by kanaries token, you can use kanaries service in pygwalker, such as share chart, share config.
    """
)
config_items = [privacy_item, kanati_token_item]


def get_config_params_help() -> str:
    help_str = ""
    help_str += "Available configurations:\n\n"
    for item in config_items: 
        help_str += (str(item) + "\n")
    return help_str


def _read_and_create_file(path: str, default_content: Dict[str, str]) -> Dict[str, str]:
    try:
        if not os.path.exists(path):
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding="utf-8") as f:
                json.dump(default_content, f, indent=4)

        with open(path, 'r', encoding="utf-8") as f:
            file_content = json.load(f)
        return file_content
    except Exception:
        return default_content


def set_config(new_config: Dict[str, str]):
    """Set configuration.

    Args:
        configs (dict): key-value map
        save (bool, optional): save to user's config path. Defaults to False.
    """
    config = _read_and_create_file(CONFIG_PATH, DEFAULT_CONFIG)

    config.update(new_config)

    with open(CONFIG_PATH, 'w', encoding="utf-8") as f:
        json.dump(config, f, indent=4)


def reset_config(keys: List[str]):
    """Unset user configuration and use default value instead.
    Args:
        keys (List[str], optional): Defaults to None.
    """
    config = _read_and_create_file(CONFIG_PATH, DEFAULT_CONFIG)

    for key in keys:
        if key in DEFAULT_CONFIG:
            config[key] = DEFAULT_CONFIG[key]
        else:
            config.pop(key, None)

    with open(CONFIG_PATH, 'w', encoding="utf-8") as f:
        json.dump(config, f, indent=4)


def reset_all_config():
    """Unset all user configuration and use default value instead."""
    with open(CONFIG_PATH, 'w', encoding="utf-8") as f:
        json.dump(DEFAULT_CONFIG, f, indent=4)


def get_config(key: str) -> str:
    """Get configuration.

    Args:
        key (str, optional): Defaults to None.
        default (any, optional): Defaults to None.

    Returns:
        value, default_value: value of the key
    """
    config = _read_and_create_file(CONFIG_PATH, DEFAULT_CONFIG)
    return config.get(key, "")


def get_config_dict() -> Dict[str, str]:
    config = _read_and_create_file(CONFIG_PATH, DEFAULT_CONFIG)
    return config


def get_all_config_str() -> str:
    config = _read_and_create_file(CONFIG_PATH, DEFAULT_CONFIG)
    return json.dumps(config, indent=4)


@lru_cache(maxsize=1)
def get_local_user_id() -> str:
    return _read_and_create_file(
        USER_CONFIG_PATH,
        {"user_id": generate_hash_code()}
    ).get("user_id", "")
