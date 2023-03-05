# -*- coding: utf-8 -*-
import os, sys, toml
from setuptools import setup

HERE = os.path.dirname(os.path.abspath(__file__))

packages = \
['pygwalker', 'pygwalker.utils']

package_data = \
{'': ['*'], 'pygwalker': ['templates/*', 'templates/dist/*']}

install_requires = \
['ipython', 'jinja2']

extras_require = \
{'all': ['pandas', 'polars'], 'pandas': ['pandas'], 'polars': ['polars']}

with open(os.path.join(HERE, 'README.md'), 'r') as f:
    description = f.read()

pyproject = toml.load(os.path.join(HERE, 'pyproject.toml'))

setup_kwargs = {
    'name': 'pygwalker',
    'version': pyproject['tool']['version'],
    'description': 'pygwalker: Combining Jupyter Notebook with a Tableau-like UI',
    'long_description': description,
    'author': 'Asm.Def',
    'author_email': 'woojson@zju.edu.cn',
    'maintainer': 'None',
    'maintainer_email': 'None',
    'url': 'None',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'extras_require': extras_require,
    'python_requires': '>=3.5,<4.0',
}


setup(**setup_kwargs)

