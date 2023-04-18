from .__version__ import __version__

# from .base import *

# with open(os.path.join(HERE, 'templates', 'graphic-walker.umd.js'), 'r') as f:
#     gwalker_js = "const process={env:{NODE_ENV:'production'} };" + f.read()

# def loadJs():
#         display(HTML(f"""<head>
#             <script>{gwalker_js}</script></head>"""))
#             # <meta charset="UTF-8">
#             # <meta http-equiv="X-UA-Compatible" content="IE=edge">
#             # <meta name="viewport" content="width=device-width, initial-scale=1.0">
# loadJs()

from .gwalker import to_html, walk, FieldSpec, GWalker
    
import logging
from .utils.config import get_config, set_config, load_config, print_help
if get_config('privacy')[0] != 'offline':
    from .utils.check_update import check_update
else: # offline mode
    logging.info("Running in offline mode. There might be newer releases available. Please check at https://github.com/Kanaries/pygwalker or https://pypi.org/project/pygwalker.")
