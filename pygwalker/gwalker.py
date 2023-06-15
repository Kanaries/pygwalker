import inspect

from pygwalker_utils.config import get_config
from .base import *
from .utils.gwalker_props import get_props, FieldSpec, DataFrame
from .utils.render import render_gwalker_html
from .utils.spec import get_spec_json
from .utils.format_invoke_walk_code import get_formated_spec_params_code

LAST_PROPS = {}

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
    global global_gid, LAST_PROPS
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
        LAST_PROPS = props

    except Exception as e:
        import logging, traceback
        logging.error(traceback.format_exc())
        return f"<div>{str(e)}</div>"
    return html

def walk(df: "pl.DataFrame | pd.DataFrame", gid: tp.Union[int, str] = None, *,
         env: Literal['Jupyter', 'Streamlit'] = 'Jupyter',
         fieldSpecs: tp.Dict[str, FieldSpec] = {},
         hideDataSourceConfig: bool = True,
         themeKey: Literal['vega', 'g2'] = 'g2',
         dark: Literal['media', 'light', 'dark'] = 'media',
         return_html: bool = False,
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
        - spec (str): chart config data. config id, json, remote file url
    """
    global global_gid, LAST_PROPS
    if gid is None:
        gid = global_gid
        global_gid += 1
    df = df.sample(frac=1)
    kwargs["sourceInvokeCode"] = get_formated_spec_params_code(
        inspect.stack()[1].code_context[0]
    )
    kwargs["spec"] = get_spec_json(kwargs.get("spec", ""))
    kwargs["id"] = gid
    html = to_html(
        df, gid, env=env, fieldSpecs=fieldSpecs, 
        hideDataSourceConfig=hideDataSourceConfig, themeKey=themeKey, dark=dark, **kwargs
    )
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
    
    import time
    import json
    from .utils.render import DataFrameEncoder
    from .utils.gwalker_props import get_prop_getter
    
    from .base import __hash__, rand_str
    def rand_slot_id():
        return __hash__ + '-' + rand_str(6)
    slot_cnt, cur_slot = 8, 0
    display_slots = [rand_slot_id() for _ in range(slot_cnt)]
    def send_js(js_code):
        nonlocal cur_slot
        # import html as m_html
        # js_code = m_html.escape(js_code)
        display_html(
            f"""<style onload="(()=>{{let f=()=>{{{js_code}}};setTimeout(f,0);}})();this.remove()" />""", env, slot_id=display_slots[cur_slot])
        cur_slot = (cur_slot + 1) % slot_cnt
        
    def send_msg(msg):
        msg = json.loads(json.dumps(msg, cls=DataFrameEncoder))
        js_code = f"document.getElementById('gwalker-{gid}')?"\
            ".contentWindow?"\
            f".postMessage({msg}, '*');"
        # display(Javascript(js));
        # js = m_html.escape(js)
        send_js(js_code)

    if return_html:
        return html
    else:
        l = len(df)
        d_id = 0
        caution_id = __hash__ + rand_str(6)
        progress_id = __hash__ + rand_str(6)
        progress_hint = "Dynamically loading into the frontend..."
        sample_data = LAST_PROPS.get('dataSource', [])
        ds_props = LAST_PROPS['dataSourceProps']
        if l > len(sample_data):
            display_html(f"""<div id="{caution_id}">Dataframe is too large for ipynb files. """\
                f"""Only {len(sample_data)} sample items are printed to the file.</div>""",
                    env, slot_id=caution_id)
            display_html(f"{progress_hint} {len(sample_data)}/{l}", env, slot_id=progress_id)
        display_html(html, env)
        
        # time.sleep(1)
        # print("send_msg")
        # send_msg({'action': 'dataReady', 'tunnelId': 'tunnel!', 'dataSourceId': 'dataSource!' })
        if l > len(sample_data):
            # static output is truncated.
            time.sleep(0.1)
            chunk = 1 << 14
            prop_getter = get_prop_getter(df)
            df = prop_getter.escape_fname(df, env=env, fieldSpecs=fieldSpecs, **kwargs)
            records = prop_getter.to_records(df)
            # matrix = prop_getter.to_matrix(df)
            for i in range(len(sample_data), l, chunk):
                # s = df[i: min(i+chunk, l)]
                # data = prop_getter.to_records(s)
                data = records[i: min(i+chunk, l)]
                # data = matrix[i: min(i+chunk, l)]
                msg = {
                    'action': 'postData',
                    'tunnelId': ds_props['tunnelId'],
                    'dataSourceId': ds_props['dataSourceId'],
                    'data': data,
                }
                send_msg(msg)
                display_html(f"{progress_hint} {min(i+chunk, l)}/{l}", env, slot_id=progress_id)
                # time.sleep(1e-3)
            msg = {
                'action': 'finishData',
                'tunnelId': ds_props['tunnelId'],
                'dataSourceId': ds_props['dataSourceId'],
            }
            send_msg(msg)
            time.sleep(0.5)
            display_html("", env, slot_id=progress_id)
            send_js(f"document.getElementById('{caution_id}')?.remove()")
            for i in range(cur_slot, slot_cnt):
                display_html("", env, slot_id=display_slots[i])
            for i in range(cur_slot):
                display_html("", env, slot_id=display_slots[i])
        
        return None


DISPLAY_HANDLER = dict()
def display_html(html: str, env: Literal['Jupyter', 'Streamlit', 'Widgets'] = 'Jupyter', *,
                 slot_id: str=None):
    """Judge the presentation method to be used based on the context

    Args:
        - html (str): html string to display.
        - env: (Literal['Widgets' | 'Streamlit' | 'Jupyter'], optional): The enviroment using pygwalker
        *
        - slot_id(str): display with given id.
    """
    if env == 'Jupyter':
        if slot_id is None:
            display(HTML(html))
        else:
            handler = DISPLAY_HANDLER.get(slot_id)
            if handler is None:
                handler = display(HTML(html), display_id=slot_id)
                DISPLAY_HANDLER[slot_id] = handler
            else:
                handler.update(HTML(html))
            
    elif env == 'Streamlit':
        import streamlit.components.v1 as components
        components.html(html, height=1000, scrolling=True)
    elif env == 'Widgets':
        import ipywidgets as wgt
        
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
