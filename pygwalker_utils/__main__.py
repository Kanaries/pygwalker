#!/usr/bin/env python
import argparse
from . import config

parser = argparse.ArgumentParser(description='PyGWalker: Combining Jupyter Notebook with a Tableau-like UI')
subparsers = parser.add_subparsers(dest='command')
# config
config_parser = subparsers.add_parser('config', help='Modify configuration file. (default: ~/.config/pygwalker/config.json)', add_help=True, description='Modify configuration file.')
config_parser.add_argument('--set', nargs='*', metavar='key=value', help='Set configuration. e.g. "pygwalker config --set privacy=get-only"')
config_parser.add_argument('--reset', nargs='*', metavar='key', help='Reset user configuration and use default values instead. e.g. "pygwalker config --reset privacy"')
config_parser.add_argument('--reset-all', action='store_true', help='Reset all user configuration and use default values instead. e.g. "pygwalker config --reset-all"')
config_parser.add_argument('--list', action='store_true', help='List current used configuration.')
# other commands

def main():
    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
    elif args.command == 'config':
        if args.set is not None:
            if len(args.set):
                configs = {}
                for item in args.set:
                    k, v = item.split('=')
                    configs[k] = v
                config.set_config(configs, save=True)
            else:
                config.print_help()
        elif args.reset is not None:
            if len(args.reset):
                config.reset_config(args.reset, save=True)
            else:
                config.print_help()
        elif args.reset_all:
            config.reset_config(save=True)
        elif args.list:
            conf, default_conf = config.get_config()
            print("PyGWalker Configuration:\n\n{}\n".format('\n'.join([f"{k}={v}\t# {default_conf.get(k, None)}" for k, v in conf.items()])))
        else:
            config_parser.print_help()
    # other commands

if __name__ == '__main__':
    main()
