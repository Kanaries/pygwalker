import sys
from .. import base
__update_url__ = 'https://5agko11g7e.execute-api.us-west-1.amazonaws.com/default/check_updates'

async def check_update_async():
    import logging
    payload = {'pkg': 'pygwalker', 'v': base.__version__, 'hashcode': base.__hash__}
    try:
        resp = {}
        if "pyodide" in sys.modules:
            import pyodide
            payload['pkg'] = 'pygwalker-pyodide'
            params = '&'.join([f"{k}={v}" for k, v in payload.items()])
            resp = await pyodide.http.pyfetch(f"{__update_url__}?{params}")
            resp = await resp.json()
        else:
            import aiohttp
            params = '&'.join([f"{k}={v}" for k, v in payload.items()])
            async with aiohttp.ClientSession() as session:
                resp = await session.get(f"{__update_url__}?{params}")
                resp = await resp.json()
        if resp['data']['outdated'] == True:
            import logging
            release = resp['data']['latest']['release']
            # logging.info(f"[pygwalker]: A new release {release} available.")
        return resp
    except:
        import traceback
        logging.warn(traceback.format_exc())

def check_update():
    import asyncio
    try:
        main_loop = asyncio.get_running_loop()
        main_loop.create_task(check_update_async())
    except:
        main_loop = asyncio.new_event_loop()
        main_loop.run_until_complete(check_update_async())
