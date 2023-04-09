from .base import *

from .utils.gwalker_props import get_props, FieldSpec, DataFrame
from .utils.render import render_gwalker_html
from .utils.config import get_config

def to_html(df: DataFrame, gid: tp.Union[int, str]=None, *,
        fieldSpecs: tp.Dict[str, FieldSpec]={},
        hideDataSourceConfig: bool=True,
        themeKey: Literal['vega', 'g2']='g2',
        dark: Literal['media', 'light', 'dark']='media',
        **kwargs):
    """Generate embeddable HTML code of Graphic Walker with data of `df`.

    Args:
        - df (pl.DataFrame | pd.DataFrame, optional): dataframe.
        - gid (tp.Union[int, str], optional): GraphicWalker container div's id ('gwalker-{gid}')
    
    Kargs:
        - fieldSpecs (Dict[str, FieldSpec], optional): Specifications of some fields. They'll been automatically inferred from `df` if some fields are not specified.

        - hideDataSourceConfig (bool, optional): Hide DataSource import and export button (True) or not (False). Default to True
        - themeKey ('vega' | 'g2'): theme type.
        - dark ('media' | 'light' | 'dark'): 'media': auto detect OS theme.
    """
    global global_gid
    if get_config('privacy')[0] != 'offline':
        try:
            from .utils.check_update import check_update
            check_update()
        except:
            pass
    if gid is None:
        gid = global_gid
        global_gid += 1
    try:
        props = get_props(df, hideDataSourceConfig=hideDataSourceConfig, themeKey=themeKey,
                        dark=dark, fieldSpecs=fieldSpecs, **kwargs)
        html = render_gwalker_html(gid, props)
    except Exception as e:
        print(e, file=sys.stderr)
        return f"<div>{str(e)}</div>"
    return html

def walk(df: "pl.DataFrame | pd.DataFrame", gid: tp.Union[int, str]=None, *,
        env: Literal['Jupyter', 'Streamlit']='Jupyter',
        fieldSpecs: tp.Dict[str, FieldSpec]={},
        hideDataSourceConfig: bool=True,
        themeKey: Literal['vega', 'g2']='g2',
        dark: Literal['media', 'light', 'dark']='media',
        return_html: bool=False,
        **kwargs):
    """Walk through pandas.DataFrame df with Graphic Walker

    Args:
        - df (pl.DataFrame | pd.DataFrame, optional): dataframe.
        - gid (Union[int, str], optional): GraphicWalker container div's id ('gwalker-{gid}')
    
    Kargs:
        - env: (Literal['Jupyter' | 'Streamlit'], optional): The enviroment using pygwalker. Default as 'Jupyter'
        - fieldSpecs (Dict[str, FieldSpec], optional): Specifications of some fields. They'll been automatically inferred from `df` if some fields are not specified.
        - hideDataSourceConfig (bool, optional): Hide DataSource import and export button (True) or not (False). Default to True
        - themeKey ('vega' | 'g2'): theme type.
        - dark (Literal['media' | 'light' | 'dark']): 'media': auto detect OS theme.
        - return_html (bool, optional): Directly return a html string. Defaults to False.
    """
    global global_gid
    if gid is None:
        gid = global_gid
        global_gid += 1
    html = to_html(df, gid, env=env, fieldSpecs=fieldSpecs, 
        hideDataSourceConfig=hideDataSourceConfig, themeKey=themeKey, dark=dark, **kwargs)
    import html as m_html
    srcdoc = m_html.escape(html)
    iframe = \
f"""<div id="ifr-pyg-{gid}" style="height: auto">
<head><script>
function resizeIframe{gid}(obj, h){{
    const doc = obj.contentDocument || obj.contentWindow.document;
    if (!h) {{
        let e = doc.documentElement;
        h = Math.max(e.scrollHeight, e.offsetHeight, e.clientHeight);
    }}
    obj.style.height = 0; obj.style.height = (h + 10) + 'px';
}}
window.addEventListener("message", (event) => {{
    if (event.iframeToResize !== "gwalker-{gid}") return;
    resizeIframe(document.querySelector("#gwalker-{gid}"), event.desiredHeight);
}});
</script></head>
<iframe src="/" width="100%" height="100px" id="gwalker-{gid}" onload="resizeIframe{gid}(this)" srcdoc="{srcdoc}" frameborder="0" allow="clipboard-read; clipboard-write" allowfullscreen></iframe>
</div>
"""
    html = iframe
    if return_html:
        return html
    else:
        display_html(html, env)
        return None


def display_html(html: str, env: Literal['Jupyter', 'Streamlit'] = 'Jupyter'):
    """Judge the presentation method to be used based on the context

    Args:
        - html (str): html string to display.
        - env: (Literal['Jupyter' | 'Streamlit'], optional): The enviroment using pygwalker
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
    
    # @property
    # def dataSource(self) -> tp.List[tp.Dict]:
    #     from .utils.gwalker_props import to_records
    #     return to_records(self.df)
    
    # @property
    # def rawFields(self) -> tp.List:
    #     from .utils.gwalker_props import raw_fields
    #     return raw_fields(self.df)
    