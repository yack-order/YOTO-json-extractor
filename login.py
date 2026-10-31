"""Yoto Authorization Code + PKCE login; tokens remain in process memory."""
import base64
import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
import re
import secrets
import time
from urllib.parse import parse_qs, urlencode, urlsplit
import webbrowser

import requests

REDIRECT_URL = 'http://127.0.0.1:3000/callback'
AUTHORIZE_URL = 'https://login.yotoplay.com/authorize'
TOKEN_URL = 'https://login.yotoplay.com/oauth/token'
SCOPES = 'family:library:view user:content:view'
LOGIN_TIMEOUT = 120


def parse_callback(url, expected_state, redirect_uri=REDIRECT_URL):
    """Validate the entire callback and state before accepting a single-use code."""
    parsed, expected = urlsplit(url), urlsplit(redirect_uri)
    if (parsed.scheme, parsed.netloc, parsed.path) != (expected.scheme, expected.netloc, expected.path):
        raise ValueError('Unexpected callback destination')
    if parsed.fragment or parsed.username or parsed.password or len(url) > 8192:
        raise ValueError('Invalid callback')
    params = parse_qs(parsed.query, keep_blank_values=True, max_num_fields=10)
    if any(len(values) != 1 for values in params.values()):
        raise ValueError('Duplicate callback parameters')
    state = params.get('state', [''])[0]
    if not state or not state.isascii() or not secrets.compare_digest(state, expected_state):
        raise ValueError('Login state mismatch')
    if 'error' in params:
        raise ValueError('Authorization was declined')
    code = params.get('code', [''])[0]
    if not code or re.search(r'\s|[\x00-\x1f\x7f]', code) or 'access_token' in params or 'id_token' in params:
        raise ValueError('Invalid authorization response')
    return code


def authorization_url(client_id, state, verifier):
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode('ascii')).digest()).rstrip(b'=').decode('ascii')
    return AUTHORIZE_URL + '?' + urlencode({
        'client_id': client_id, 'response_type': 'code', 'redirect_uri': REDIRECT_URL,
        'audience': 'https://api.yotoplay.com', 'scope': SCOPES, 'state': state,
        'code_challenge': challenge, 'code_challenge_method': 'S256',
    })


def exchange_code(client_id, code, verifier):
    try:
        with requests.Session() as session:
            session.trust_env = False
            with session.post(TOKEN_URL, data={
                'grant_type': 'authorization_code', 'client_id': client_id,
                'code': code, 'code_verifier': verifier, 'redirect_uri': REDIRECT_URL,
            }, timeout=(10, 15), allow_redirects=False, stream=True) as response:
                if response.status_code != 200:
                    raise ValueError('Token exchange failed')
                body = bytearray()
                started = time.monotonic()
                for chunk in response.iter_content(1):
                    if time.monotonic() - started > 30 or len(body) + len(chunk) > 65536:
                        raise ValueError('Token response exceeded limits')
                    body.extend(chunk)
                data = json.loads(body)
        token = data.get('access_token')
        if (not isinstance(token, str) or not token or re.search(r'\s|[\x00-\x1f\x7f]', token)
                or data.get('token_type', '').lower() != 'bearer'
                or not isinstance(data.get('expires_in'), int) or data['expires_in'] <= 0):
            raise ValueError('Invalid token response')
        return token
    except (requests.RequestException, ValueError, TypeError, AttributeError):
        # Never expose provider error bodies, URLs, code, verifier or tokens.
        raise ValueError('Token exchange failed safely') from None


class CallbackServer(HTTPServer):
    def get_request(self):
        connection, address = super().get_request()
        connection.settimeout(1)
        return connection, address


def callback_server(state):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass  # The default access logger includes the credential-bearing URL.

        def do_GET(self):
            try:
                if self.headers.get('Host') != '127.0.0.1:3000' or not self.path.startswith('/callback?'):
                    raise ValueError('Unexpected callback request')
                code = parse_callback('http://127.0.0.1:3000' + self.path, state)
                self.server.code = code
                status = 200
            except ValueError:
                status = 400
            self.send_response(status)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Referrer-Policy', 'no-referrer')
            self.send_header('Connection', 'close')
            self.end_headers()
            try:
                self.wfile.write(b'Login received. Return to the app.' if status == 200 else b'Login callback rejected.')
            except OSError:
                pass

    server = CallbackServer(('127.0.0.1', 3000), Handler)
    server.code = None
    server.timeout = 0.5
    return server


def get_access_token():
    client_id = os.environ.get('YOTO_CLIENT_ID', '').strip()
    if not client_id or not re.fullmatch(r'[A-Za-z0-9_-]{8,128}', client_id):
        print('Set YOTO_CLIENT_ID to your registered Yoto public client ID before login.')
        return None
    state, verifier = secrets.token_urlsafe(32), secrets.token_urlsafe(64)
    try:
        # Bind before opening the browser; an occupied callback port fails closed.
        with callback_server(state) as server:
            if not webbrowser.open(authorization_url(client_id, state, verifier)):
                print('Could not open the login browser.')
                return None
            deadline = time.monotonic() + LOGIN_TIMEOUT
            while server.code is None and time.monotonic() < deadline:
                server.handle_request()
            if server.code is None:
                print('Login timed out or was declined.')
                return None
            return exchange_code(client_id, server.code, verifier)
    except (OSError, ValueError, webbrowser.Error):
        print('Login failed safely. Check client registration and callback port availability.')
        return None
