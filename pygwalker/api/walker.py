from typing import Union, Dict, Optional
import inspect
import html as m_html
import time
import json

from typing_extensions import Literal

from pygwalker import __hash__
from pygwalker.utils.randoms import rand_str
from pygwalker.utils.display import display_html
from pygwalker.props_parsers.base import DataFrame, FieldSpec
from pygwalker.services.global_var import GlobalVarManager
from pygwalker.services.props_parsers import get_props, get_prop_getter
from pygwalker.services.render import render_gwalker_html, DataFrameEncoder
from pygwalker.services.spec import get_spec_json
from pygwalker.services.format_invoke_walk_code import get_formated_spec_params_code


def walk(
    df: DataFrame,
    gid: Union[int, str] = None,
    *,
    env: Literal['Jupyter', 'Streamlit'] = 'Jupyter',
    fieldSpecs: Optional[Dict[str, FieldSpec]] = None,
    hideDataSourceConfig: bool = True,
    themeKey: Literal['vega', 'g2'] = 'g2',
    dark: Literal['media', 'light', 'dark'] = 'media',
    return_html: bool = False,
    **kwargs
):
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
    if fieldSpecs is None:
        fieldSpecs = {}
    if gid is None:
        gid = GlobalVarManager.get_global_gid()
    df = df.sample(frac=1)
    kwargs["sourceInvokeCode"] = get_formated_spec_params_code(
        inspect.stack()[1].code_context[0]
    )
    kwargs["spec"] = get_spec_json(kwargs.get("spec", ""))
    kwargs["id"] = gid
    props = get_props(
        df,
        hideDataSourceConfig=hideDataSourceConfig,
        themeKey=themeKey,
        dark=dark,
        fieldSpecs=fieldSpecs,
        **kwargs
    )
    html = render_gwalker_html(gid, props)
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
        sample_data = props.get('dataSource', [])
        ds_props = props['dataSourceProps']
        if l > len(sample_data):
            display_html(f"""<div id="{caution_id}">Dataframe is too large for ipynb files. """\
                f"""Only {len(sample_data)} sample items are printed to the file.</div>""",
                    env, slot_id=caution_id)
            display_html(f"{progress_hint} {len(sample_data)}/{l}", env, slot_id=progress_id)
        display_html(html, env)

        if l > len(sample_data):
            # static output is truncated.
            time.sleep(0.1)
            chunk = 1 << 14
            prop_getter = get_prop_getter(df)
            df = prop_getter.escape_fname(df, env=env, fieldSpecs=fieldSpecs, **kwargs)
            records = prop_getter.to_records(df)
            for i in range(len(sample_data), l, chunk):
                data = records[i: min(i+chunk, l)]
                msg = {
                    'action': 'postData',
                    'tunnelId': ds_props['tunnelId'],
                    'dataSourceId': ds_props['dataSourceId'],
                    'data': data,
                }
                send_msg(msg)
                display_html(f"{progress_hint} {min(i+chunk, l)}/{l}", env, slot_id=progress_id)
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
