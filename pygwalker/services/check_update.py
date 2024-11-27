"""
Check_Update Module: This module enables you to check if
the version is up-to-date.

Updated on Tue November 11 15:15:48 2024

@author: Kanaries

"""

import asyncio
import logging
import sys
import json
from typing import Dict, Any, Coroutine
from urllib import request
from threading import Thread
from pygwalker import __version__
from pygwalker.services.global_var import GlobalVarManager
from .config import get_local_user_id


_UPDATE_URL = 'https://5agko11g7e.execute-api.us-west-1.amazonaws.com/default/check_updates'

logger = logging.getLogger(__name__)


def _sync_get_async_result(co: Coroutine[Any, Any, Any]) -> Any:
    """
    fetch asynchronous result.

    Parameters
    ----------
    co : Coroutine
        asynchronous parameter.

    """
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(co)
    finally:
        loop.close()


async def _request_on_pyodide(url: str) -> Dict[str, Any]:
    """
    request url.

    Parameters
    ----------
    url : string
        url string.
    Returns
    ---------
    Dict

    """
    import pyodide
    resp = await pyodide.http.pyfetch(url)
    return await resp.json()


def _request_on_python(url: str) -> Dict[str, Any]:
    """
    request url on python.

    Parameters
    ----------
    url : string
        url string.
    Returns
    ---------
    Dict

    """
    with request.urlopen(url, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _check_update() -> Dict[str, Any]:
    """
    Internal function to Check for updates.

    Parameters
    ----------
    None

    Returns
    ---------
    Dict

    """
    payload = {'pkg': 'pygwalker', 'v': __version__, 'hashcode': get_local_user_id()}
    request_func = _request_on_python

    if "pyodide" in sys.modules:
        payload['pkg'] = 'pygwalker-pyodide'
        request_func = _request_on_pyodide

    params = '&'.join([f"{k}={v}" for k, v in payload.items()])
    url = f"{_UPDATE_URL}?{params}"

    try:
        result = request_func(url)
        if isinstance(result, Coroutine):
            result = _sync_get_async_result(result)
        return result
    finally:
        pass


def check_update() -> None:
    """
    Check for update.

    Parameters
    ----------
    None

    """
    if GlobalVarManager.privacy != "offline":
        Thread(target=_check_update).start()
