import os

from typing_extensions import Literal


class GlobalVarManager:
    """A class to manage global variables."""
    global_gid = 0
    env = None
    kanaries_api_key = os.getenv("KANARIES_API_KEY", "")
    kanaries_api_host = "https://api.kanaries.net"

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
