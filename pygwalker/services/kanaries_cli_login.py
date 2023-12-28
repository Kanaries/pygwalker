from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any
from urllib.parse import urlparse, parse_qs, quote
from threading import Thread, Lock
import socket
import webbrowser

from pygwalker.services.config import set_config

AUTH_HOST = "https://kanaries.net"
auth_info = {}
wait_lock = Lock()


class TextStyle:
    RESET = '\033[0m'
    GREEN = '\033[32m'
    RED = '\033[31m'
    UNDERLINE = '\033[4m'


class _CallbackHandler(BaseHTTPRequestHandler):
    """A simple HTTP request handler to process the callback from the OAuth server"""

    def log_message(self, _, *args: Any) -> None:
        pass

    def do_GET(self):
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)
        api_key = query_params.get('apiKey', [''])[0]
        user_name = query_params.get('username', [''])[0]
        workspace_name = query_params.get('workspaceName', [''])[0]
        auth_as = quote(f"workspace: {workspace_name}, user: {user_name}")

        if api_key:
            set_config({"kanaries_token": api_key})
            self.send_response(302)
            self.send_header('Location', f"{AUTH_HOST}/home/cli/success?authedAs={auth_as}")
            self.end_headers()
            auth_info["user_name"] = user_name
            auth_info["workspace_name"] = workspace_name
            wait_lock.release()
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(bytes("auth error, please re-auth", "utf-8"))


def _find_free_port() -> int:
    """Find a free port on localhost"""
    temp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    temp_socket.bind(('localhost', 0))
    _, port = temp_socket.getsockname()
    temp_socket.close()
    return port


def _run_callback_server(port: int):
    server_address = ('localhost', port)
    httpd = HTTPServer(server_address, _CallbackHandler)
    httpd.serve_forever()


def kanaries_login():
    wait_lock.acquire()

    port = _find_free_port()
    callback_server = Thread(target=_run_callback_server, args=(port,), daemon=True)
    callback_server.start()

    callback_url = f'http://localhost:{port}'
    auth_url = f"{AUTH_HOST}/home/cli?redirect_url={quote(callback_url)}"

    print(f'Please visit {TextStyle.GREEN}{auth_url}{TextStyle.RESET} to log in.')
    print('Waiting for authorization...')
    webbrowser.open_new(auth_url)

    wait_flag = wait_lock.acquire(blocking=True, timeout=300)
    if not wait_flag:
        print(f'{TextStyle.RED}Authorization timeout.{TextStyle.RESET}')
        return

    print((
        f'{TextStyle.GREEN}Authorization success and kanaries token is configured!{TextStyle.RESET}\n'
        f'user: {TextStyle.UNDERLINE}{auth_info["user_name"]}{TextStyle.RESET}\n'
        f'workspace: {TextStyle.UNDERLINE}{auth_info["workspace_name"]}{TextStyle.RESET}'
    ))
