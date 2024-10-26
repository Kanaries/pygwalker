from pygwalker.utils.log import init_logging as __init_logging

__init_logging()

# pylint: disable=wrong-import-position
import logging

from pygwalker.utils.randoms import rand_str as __rand_str
from pygwalker.utils.execute_env_check import check_kaggle as __check_kaggle
from pygwalker.services.global_var import GlobalVarManager
from pygwalker.services.kaggle import show_tips_user_kaggle as __show_tips_user_kaggle

__version__ = "0.4.9.11"
__hash__ = __rand_str()

from pygwalker.api.jupyter import walk, render, table
from pygwalker.api.html import to_html
from pygwalker.data_parsers.base import FieldSpec
from pygwalker.api.component import component

if GlobalVarManager.privacy == 'offline':
    logging.getLogger(__name__).info("Running in offline mode. There might be newer releases available. Please check at https://github.com/Kanaries/pygwalker or https://pypi.org/project/pygwalker.")

if __check_kaggle():
    __show_tips_user_kaggle()

__all__ = ["walk", "render", "table", "to_html", "FieldSpec", "GlobalVarManager", "component"]
