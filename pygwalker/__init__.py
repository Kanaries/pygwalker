from pygwalker.utils.log import init_logging as __init_logging

__init_logging()

# pylint: disable=wrong-import-position
import logging

from pygwalker.utils.randoms import rand_str as __rand_str
from pygwalker.utils.execute_env_check import check_kaggle as __check_kaggle
from pygwalker.services.global_var import GlobalVarManager
from pygwalker.services.kaggle import show_tips_user_kaggle as __show_tips_user_kaggle

__version__ = "0.3.18a1"
__hash__ = __rand_str()

from pygwalker.api.walker import walk
from pygwalker.api.gwalker import GWalker
from pygwalker.api.html import to_html
from pygwalker.data_parsers.base import FieldSpec

if GlobalVarManager.privacy == 'offline':
    logging.getLogger(__name__).info("Running in offline mode. There might be newer releases available. Please check at https://github.com/Kanaries/pygwalker or https://pypi.org/project/pygwalker.")

if __check_kaggle():
    __show_tips_user_kaggle()

__all__ = ["walk", "GWalker", "to_html", "FieldSpec", "GlobalVarManager"]
