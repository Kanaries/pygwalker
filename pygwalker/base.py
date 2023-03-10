import os, sys, json
import typing as tp
import IPython
from IPython.display import display, Javascript, HTML, IFrame

HERE = os.path.dirname(os.path.abspath(__file__))

gwalker_js = None

global_gid = 0

def setup_pygwalker():
    return {
        'command': ['python', '-m', 'http.server', '--directory', os.path.join(HERE, '.'), '{port}']
    }