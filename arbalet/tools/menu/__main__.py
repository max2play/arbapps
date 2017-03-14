import argparse
from .menu import Menu

parser = argparse.ArgumentParser(description='Application Menu: Start different Applications defined in a menu.json')
parser.add_argument('-q', '--menu',
                    type=str,
                    default='menus/default.json',
                    nargs='?',
                    help='Configuration file describing the sequence of apps to launch')
Menu(parser).start()
