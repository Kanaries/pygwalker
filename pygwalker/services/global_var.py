from typing_extensions import Literal


class GlobalVarManager:
    """A class to manage global variables."""
    global_gid = 0
    env = None

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
