__name__ = 'pygwalker'

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

from .gwalker import to_html, walk, GWalker
