import sys
from .. import base
__update_url__ = 'https://5agko11g7e.execute-api.us-west-1.amazonaws.com/default/check_updates'

def check_update():
    payload = {'pkg': 'pygwalker', 'v': base.__version__, 'hashcode': base.__hash__}
    try:
        resp = {}
        if "pyodide" in sys.modules:
            import pyodide, asyncio
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:  # 'RuntimeError: There is no current event loop...'
                loop = None
            payload['pkg'] = 'pygwalker-pyodide'
            params = '&'.join([f"{k}={v}" for k, v in payload.items()])
            async def check():
                resp = await pyodide.http.pyfetch(f"{__update_url__}?{params}")
                resp = await resp.json()
                if resp['data']['outdated'] == True:
                    import logging
                    release = resp['data']['latest']['release']
                    # logging.info(f"[pygwalker]: A new release {release} available.")
            if loop and loop.is_running():
                tsk = loop.create_task(check())
            else:
                asyncio.run(check())

        else:
            import requests
            resp = requests.get(__update_url__, params=payload).json()
        if resp['data']['outdated'] == True:
            import logging
            release = resp['data']['latest']['release']
            # logging.info(f"[pygwalker]: A new release {release} available.")
    except:
        pass