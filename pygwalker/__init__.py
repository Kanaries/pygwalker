import logging

from pygwalker.utils.randoms import rand_str as __rand_str
from pygwalker_utils.config import get_config as __get_config

__version__ = "0.1.11"
__hash__ = __rand_str()

from pygwalker.api.walker import walk
from pygwalker.api.gwalker import GWalker
from pygwalker.api.html import to_html
from pygwalker.data_parsers.base import FieldSpec


logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)


if __get_config('privacy')[0] == 'offline':
    logging.info("Running in offline mode. There might be newer releases available. Please check at https://github.com/Kanaries/pygwalker or https://pypi.org/project/pygwalker.")
else:
    from pygwalker.services.check_update import check_update
    check_update()
