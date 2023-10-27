from typing import Tuple
import argparse

from pygwalker.services.config import (
    reset_all_config,
    set_config,
    get_config_params_help,
    reset_config,
    get_all_config_str,
    CONFIG_PATH
)

parser = argparse.ArgumentParser(
    prog="pygwalker",
    description='PyGWalker: Combining Jupyter Notebook with a Tableau-like UI'
)
subparsers = parser.add_subparsers(dest='command')

# config command
config_parser = subparsers.add_parser(
    'config',
    help=f'Modify configuration file. (default: {CONFIG_PATH})',
    add_help=True,
    description=f'Modify configuration file. (default: {CONFIG_PATH}) \n' + get_config_params_help(),
    formatter_class=argparse.RawTextHelpFormatter
)
config_parser.add_argument(
    '--set',
    nargs='*',
    metavar='key=value',
    help='Set configuration. e.g. "pygwalker config --set privacy=update-only"'
)
config_parser.add_argument(
    '--reset',
    nargs='*',
    metavar='key',
    help='Reset user configuration and use default values instead. e.g. "pygwalker config --reset privacy"'
)
config_parser.add_argument(
    '--reset-all',
    action='store_true',
    help='Reset all user configuration and use default values instead. e.g. "pygwalker config --reset-all"'
)
config_parser.add_argument(
    '--list',
    action='store_true',
    help='List current used configuration.'
)


def command_set_config(value: Tuple[str]):
    config = dict(
        item.split('=')
        for item in value
    )
    set_config(config)


def command_reset_config(value: Tuple[str]):
    reset_config(value)


def command_reset_all_config(_):
    reset_all_config()


def command_list_config(_):
    config = get_all_config_str()
    print("Current configuration:")
    print(config)


def main():
    conifg_command_list = [
        ("set", command_set_config),
        ("reset", command_reset_config),
        ("reset_all", command_reset_all_config),
        ("list", command_list_config)
    ]

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    if args.command == 'config':
        for action, action_func in conifg_command_list:
            value = getattr(args, action)
            if value:
                action_func(value)
                return
        config_parser.print_help()
        return

    parser.print_help()


if __name__ == '__main__':
    main()
