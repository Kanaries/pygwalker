from pygwalker.utils.log import init_logging

init_logging()

# pylint: disable=wrong-import-position
import logging

from pygwalker.utils.randoms import rand_str as __rand_str
from pygwalker.services.global_var import GlobalVarManager

__version__ = "0.3.17a1"
__hash__ = __rand_str()

from pygwalker.api.walker import walk
from pygwalker.api.gwalker import GWalker
from pygwalker.api.html import to_html
from pygwalker.data_parsers.base import FieldSpec

if GlobalVarManager.privacy == 'offline':
    logging.getLogger(__name__).info("Running in offline mode. There might be newer releases available. Please check at https://github.com/Kanaries/pygwalker or https://pypi.org/project/pygwalker.")
