import os

from pandas import DataFrame
from typing_extensions import Literal, deprecated

from .config import get_config


class GlobalVarManager:
    """A class to manage global variables."""
    env = None
    privacy = get_config("privacy") or "events"
    kanaries_api_key = get_config("kanaries_token") or os.getenv("KANARIES_API_KEY", "")
    kanaries_api_host = "https://api.kanaries.net"
    kanaries_main_host = "https://kanaries.net"
    last_exported_dataframe = None
    max_data_length = 1000 * 1000
    component_url = ""

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

    @classmethod
    @deprecated("use ui config instead.")
    def set_max_data_length(cls, length: int):
        cls.max_data_length = length

    @classmethod
    def set_component_url(cls, url: str):
        cls.component_url = url
