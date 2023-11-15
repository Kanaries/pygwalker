import os

from pandas import DataFrame
from typing_extensions import Literal

from .config import get_config


class GlobalVarManager:
    """A class to manage global variables."""
    global_gid = 0
    env = None
    privacy = get_config("privacy") or "events"
    kanaries_api_key = get_config("kanaries_token") or os.getenv("KANARIES_API_KEY", "")
    kanaries_api_host = "https://api.kanaries.net"
    kanaries_main_host = "https://kanaries.net"
    last_exported_dataframe = None

    @classmethod
    def get_global_gid(cls) -> int:
        return_gid = cls.global_gid
        cls.global_gid += 1
        return return_gid

    @classmethod
    def set_env(cls, env: Literal['Jupyter', 'Streamlit']):
        cls.env = env

    @classmethod
    def get_env(cls) -> Literal['Jupyter', 'Streamlit']:
        return cls.env

    @classmethod
    def set_kanaries_api_key(cls, api_key: str):
        cls.kanaries_api_key = api_key

    @classmethod
    def set_kanaries_api_host(cls, api_host: str):
        cls.kanaries_api_host = api_host

    @classmethod
    def set_kanaries_main_host(cls, main_host: str):
        cls.kanaries_main_host = main_host

    @classmethod
    def set_privacy(cls, privacy: Literal['offline', 'update-only', 'events']):
        cls.privacy = privacy

    @classmethod
    def set_last_exported_dataframe(cls, df: DataFrame):
        cls.last_exported_dataframe = df
