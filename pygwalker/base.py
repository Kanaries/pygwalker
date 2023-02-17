import os, sys, json
import pandas as pd
import typing as tp
import IPython
from IPython.display import display, Javascript, HTML, IFrame

HERE = os.path.dirname(os.path.abspath(__file__))

gwalker_js = None

def gwalker_script():
    global gwalker_js
    if gwalker_js is None:
        with open(os.path.join(HERE, 'templates', 'graphic-walker.umd.js'), 'r') as f:
            gwalker_js = "const process={env:{NODE_ENV:\"production\"} };" + f.read()
    return gwalker_js
        

