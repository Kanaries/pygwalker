__version__ = "0.1.10"

import logging

from pygwalker_utils.config import get_config
from pygwalker.utils.randoms import rand_str

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

__hash__ = rand_str()

from .gwalker import to_html, walk, FieldSpec, GWalker

if get_config('privacy')[0] != 'offline':
    from pygwalker.services.check_update import check_update
else: # offline mode
    logging.info("Running in offline mode. There might be newer releases available. Please check at https://github.com/Kanaries/pygwalker or https://pypi.org/project/pygwalker.")

