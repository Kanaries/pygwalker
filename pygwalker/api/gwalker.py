from pygwalker.services.global_var import GlobalVarManager

from pygwalker._typing import DataFrame
from .html import to_html
from .walker import walk


class GWalker:
    def __init__(self, df: DataFrame = None):
        self.gid = GlobalVarManager.get_global_gid()
        self.df = df

    def to_html(self, **kwargs):
        html = to_html(self.df, self.gid, **kwargs)
        return html

    def walk(self, **kwargs):
        return walk(self.df, self.gid, **kwargs)

    def update(self, df: DataFrame = None, **kwargs):
        pass
