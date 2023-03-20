from .base import *

from .utils.gwalker_props import get_props
from .utils.render import render_gwalker_html

def to_html(df: "pl.DataFrame | pd.DataFrame", gid: tp.Union[int, str]=None, *,
        hideDataSourceConfig: bool=True,
        themeKey: Literal['vega', 'g2']='vega',
        dark: Literal['media', 'light', 'dark']='media',
        **kwargs):
    """Generate embeddable HTML code of Graphic Walker with data of `df`.

    Args:
        - df (pl.DataFrame | pd.DataFrame, optional): dataframe.
        - gid (tp.Union[int, str], optional): GraphicWalker container div's id ('gwalker-{gid}')
    
    Kargs:
        - hideDataSourceConfig (bool, optional): Hide DataSource import and export button (True) or not (False). Default to True
        - themeKey ('vega' | 'g2'): theme type.
        - dark ('media' | 'light' | 'dark'): 'media': auto detect OS theme.
    """
    global global_gid
    if gid is None:
        gid = global_gid
        global_gid += 1
    props = get_props(df, hideDataSourceConfig=hideDataSourceConfig, themeKey=themeKey,
                      dark=dark, **kwargs)
    html = render_gwalker_html(gid, props)
    return html

def walk(df: "pl.DataFrame | pd.DataFrame", gid: tp.Union[int, str]=None, *,
        env: Literal['Jupyter', 'Streamlit', 'Dash']='Jupyter',
        hideDataSourceConfig: bool=True,
        themeKey: Literal['vega', 'g2']='vega',
        dark: Literal['media', 'light', 'dark']='media',
        return_html: bool=False,
        app: "dash.Dash" = None,
        **kwargs):
    """Walk through pandas.DataFrame df with Graphic Walker

    Args:
        - df (pl.DataFrame | pd.DataFrame, optional): dataframe.
        - gid (Union[int, str], optional): GraphicWalker container div's id ('gwalker-{gid}')
    
    Kargs:
        - env (Literal['Jupyter' | 'Streamlit' | 'Dash'], optional): The enviroment using pygwalker. Default as 'Jupyter'
        - hideDataSourceConfig (bool, optional): Hide DataSource import and export button (True) or not (False). Default to True
        - themeKey ('vega' | 'g2'): theme type.
        - dark (Literal['media' | 'light' | 'dark']): 'media': auto detect OS theme.
        - return_html (bool, optional): Directly return a html string. Defaults to False.
        - app (dash.Dash): The instance of Dash class created earliest.
    """
    global global_gid
    if gid is None:
        gid = global_gid
        global_gid += 1
    html = to_html(df, gid, env=env, hideDataSourceConfig=hideDataSourceConfig,
                   themeKey=themeKey, dark=dark, **kwargs)
    import html as m_html
    srcdoc = m_html.escape(html)
    iframe = \
f"""<div id="ifr-pyg-{gid}">
<iframe src="/" width="100%" height="900px" srcdoc="{srcdoc}" frameborder="0" allowfullscreen></iframe>
</div>
"""
    html = iframe
    if return_html:
        return html
    else:
        display_html(html, env, app=app)
        return None


def display_html(html: str, env: Literal['Jupyter', 'Streamlit', 'Dash'] = 'Jupyter', app: "dash.Dash"=None):
    """Judge the presentation method to be used based on the context

    Args:
        - html (str): html string to display.
        - env (Literal['Jupyter' | 'Streamlit' | 'Dash'], optional): The enviroment using pygwalker.
        - app (dash.Dash): The instance of Dash class created earliest.
    """
    if env == 'Jupyter':
        display(HTML(html))
    elif env == 'Streamlit':
        import streamlit.components.v1 as components
        components.html(html, height=1000, scrolling=True)
    elif env == 'Dash':
        import dash_dangerously_set_inner_html
        from dash import html as d_html
        app.layout = d_html.Div([dash_dangerously_set_inner_html.DangerouslySetInnerHTML(html),])
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
    
    # @property
    # def dataSource(self) -> tp.List[tp.Dict]:
    #     from .utils.gwalker_props import to_records
    #     return to_records(self.df)
    
    # @property
    # def rawFields(self) -> tp.List:
    #     from .utils.gwalker_props import raw_fields
    #     return raw_fields(self.df)
    