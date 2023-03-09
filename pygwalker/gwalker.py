from .base import *

from .utils.gwalker_props import get_props
from .utils.render import render_gwalker_html

def to_html(df: "pl.DataFrame | pd.DataFrame", gid: tp.Union[int, str]=None, **kwargs):
    """Generate embeddable HTML code of Graphic Walker with data of `df`.

    Args:
        df (pl.DataFrame | pd.DataFrame, optional): dataframe.
        gid (tp.Union[int, str], optional): GraphicWalker container div's id ('gwalker-{gid}')
        **
        hideDataSourceConfig (bool, optional): Hide DataSource import and export button (True) or not (False). Default to True
        themeKey ('vega' | 'g2'): theme type.
        dark ('media' | 'light' | 'dark'): 'media': auto detect OS theme.
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
        **
        env: (Jupyter | Streamlit, optional): The enviroment using pygwalker
        hideDataSourceConfig (bool, optional): Hide DataSource import and export button (True) or not (False). Default to True
        themeKey ('vega' | 'g2'): theme type.
        dark ('media' | 'light' | 'dark'): 'media': auto detect OS theme.
        return_html (bool, optional): Directly return a html string. Defaults to False.
    """
    global global_gid
    return_html = kwargs.get('return_html', False)
    if gid is None:
        gid = global_gid
        global_gid += 1
    html = to_html(df, gid, **kwargs)
    env = kwargs.get('env', 'Jupyter')
    if return_html:
        return html
    else:
        display_html(html, env)


def display_html(html: str, env: str):
    """Judge the presentation method to be used based on the context

    Args:
        html (html): stringed html.
        env: (Jupyter | Streamlit, optional): The enviroment using pygwalker
    """
    if env == 'Jupyter':
        display(HTML(html))
    elif env == 'Streamlit':
        import streamlit.components.v1 as components
        components.html(html, height=1000, scrolling=True)
    else:
        print("The environment is not supported yet, Please use the options given")


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
        return walk(self.df, self.gid, **kwargs)
        
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
    