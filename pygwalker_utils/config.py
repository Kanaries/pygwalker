#!/usr/bin/env python
"""Load configuration files.
The order
"""
import os, sys, json
CONFIG, DEFAULT_CONFIG = {}, {}
HERE = os.path.dirname(os.path.abspath(__file__))
def load_default_config():
    """Load default configuration file.
    """
    global CONFIG, DEFAULT_CONFIG
    with open(os.path.join(HERE, "defaults.json"), 'r', encoding='utf-8') as f:
        DEFAULT_CONFIG = json.load(f)
    CONFIG.update(DEFAULT_CONFIG)
    conf_list = [
        os.path.join(sys.prefix, "etc", "pygwalker", "config.json"),
        os.path.join(os.path.expanduser('~'), ".config", "pygwalker", "config.json")
    ]
    for conf in conf_list:
        try:
            with open(conf, 'r', encoding='utf-8') as f:
                CONFIG.update(json.load(f))
        except:
            pass
load_default_config()

def load_config(filename: str, encoding='utf-8'):
    """Load user-specified configuration file.
    
    Args:
        filename (str): user-specified configuration filename
        encoding (str, optional): Defaults to 'utf-8'.
    """
    try:
        CONFIG.update(json.load(open(filename, 'r', encoding=encoding)))
    except Exception as e:
        import logging
        logging.warn(f"Cannot load user-specified configuration file {filename}: {e}")

class Item:
    __slots__ = ['name', 'type', 'default', 'description']
    def __init__(self, name: str, type_, default=None, description='') -> None:
        self.name, self.type, self.default, self.description = name, type_, default, description
items = [
Item('privacy', ['offline', 'get-only', 'meta', 'any'], 'meta', description="""
    "offline"\t: no data will be transfered other than the front-end and back-end of the notebook.
    "get-only"\t: the data will not be uploaded but only fetched from external servers.
    "meta" \t: only the desensitized data will be processed by external servers. There might be some server-side processing tasks performed on the metadata in future versions.
    "any" \t: the data can be processed by external services."""),
]
        
def print_help():
    print("usage: pygwalker config [--set [key=value ...]] | [--reset [key ...]].\n")
    print("Available configurations:")
    for item in items:
        print(f"- {item.name}\t {item.type} (default: {item.default}).{item.description}")

def set_config(config: dict, save=False):
    """Set configuration.
    
    Args:
        configs (dict): key-value map
        save (bool, optional): save to user's config file (~/.config/pygwalker/config.json). Defaults to False.
    """
    CONFIG.update(config)
    if save:
        filename = os.path.join(os.path.expanduser('~'), ".config", "pygwalker", "config.json")
        user_config = {}
        try:
            with open(filename, 'r') as f:
                user_config.update(json.load(f))
        except Exception as e:  # user config file not existed, create it.
            import logging
            logging.info(f"Cannot access user's config file {filename}. (creating it...)")
            logging.debug(f"{e}")
            user_config.update(DEFAULT_CONFIG)
        try:
            user_config.update(config)
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            # overwrite to file
            with open(filename, 'w') as f:
                json.dump(user_config, f)
        except Exception as e:
            logging.warning(f"Failed to write config file {filename}: {e}")

def reset_config(keys: list=None, save=False):
    """Unset user configuration and use default value instead.
    
    Args:
        keys (List[str], optional): Defaults to None.
    """
    if keys is None:
        set_config(DEFAULT_CONFIG, save=save)
    else:
        config = {}
        for k in keys:
            if k in DEFAULT_CONFIG:
                config[k] = DEFAULT_CONFIG[k]
        set_config(config, save=save)
        

def get_config(key: str=None, default=None):
    """Get configuration.
    
    Args:
        key (str, optional): Defaults to None.
        default (any, optional): Defaults to None.
    
    Returns:
        value, default_value: value of the key
    """
    if key is None:
        return CONFIG, DEFAULT_CONFIG
    return CONFIG.get(key, default), DEFAULT_CONFIG.get(key, default)