from .base import *

from .utils.gwalker_props import get_props
from .utils.render import render_gwalker_html

def to_html(df: "pl.DataFrame | pd.DataFrame", gid: tp.Union[int, str]=None, **kwargs):
    """Generate embeddable HTML code of Graphic Walker with data of `df`.

    Args:
        df (pl.DataFrame | pd.DataFrame , optional): dataframe.
        gid (tp.Union[int, str], optional): GraphicWalker container div's id ('gwalker-{gid}')
        hideDataSourceConfig (bool, optional): Hide DataSource import and export button (True) or not (False). Default to True
    """
    global global_gid
    if gid is None:
        gid = global_gid
        global_gid += 1
    props = get_props(df, **kwargs)
    html = render_gwalker_html(gid, props)
    return html
    
def walk(df: "pl.DataFrame | pd.DataFrame", gid: tp.Union[int, str]=None, **kwargs):
    """walk through pandas.DataFrame df with Graphic Walker

    Args:
        df (pl.DataFrame | pd.DataFrame, optional): dataframe.
        gid (tp.Union[int, str], optional): GraphicWalker container div's id ('gwalker-{gid}')
        hideDataSourceConfig (bool, optional): Hide DataSource import and export button (True) or not (False). Default to True
        return_html (bool, optional): Directly return a html string. Defaults to False.
    """
    global global_gid
    return_html = kwargs.get('return_html', False)
    if gid is None:
        gid = global_gid
        global_gid += 1
    html = to_html(df, gid, **kwargs)
    if return_html:
        return html
    else:
        display(HTML(html))

class GWalker:
    def __init__(self, df: "pl.DataFrame | pd.DataFrame"=None, **kwargs):
        global global_gid
        self.gid = global_gid
        global_gid += 1
        self.df = df
    
    def to_html(self, **kwargs):
        html = to_html(self.df, self.gid, **kwargs)
        return html
    
    def walk(self, **kwargs):
        html = self.to_html(**kwargs)
        display(HTML(html))
        
    def update(self, df: "pl.DataFrame | pd.DataFrame"=None, **kwargs):
        pass
    
    @property
    def dataSource(self) -> tp.List[tp.Dict]:
        from .utils.gwalker_props import to_records
        return to_records(self.df)
    
    @property
    def rawFields(self) -> tp.List:
        from .utils.gwalker_props import raw_fields
        return raw_fields(self.df)
    