import requests, inspect, json
from .. import base
__update_url__ = 'https://5agko11g7e.execute-api.us-west-1.amazonaws.com/default/check_updates'

def check_update():
    payload = {'pkg': 'pygwalker', 'v': base.__version__, 'hashcode': base.__hash__}
    try:
        resp = requests.get(__update_url__, params=payload).json()
        if resp['data']['outdated'] == True:
            import logging
            release = resp['data']['latest']['release']
            # logging.info(f"[pygwalker]: A new release {release} available.")
    except:
        pass