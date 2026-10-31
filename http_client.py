"""Bounded HTTPS downloads with no background request threads."""
import ipaddress
import re
import socket
import time
from urllib.parse import urljoin, urlsplit

import requests

METADATA_LIMIT = 8 * 1024 * 1024
IMAGE_LIMIT = 16 * 1024 * 1024
MEDIA_LIMIT = 128 * 1024 * 1024
DOWNLOAD_SECONDS = 120


class DownloadError(ValueError):
    pass


def normalize_url(url):
    value = str(url).strip()
    if value.startswith('//'):
        value = 'https:' + value
    elif '://' not in value:
        value = 'https://' + value
    try:
        parsed = urlsplit(value)
        if (parsed.scheme.lower() != 'https' or not parsed.hostname or parsed.username or parsed.password
                or parsed.port not in (None, 443) or re.search(r'[\s\x00-\x1f\x7f\\]', value)):
            raise ValueError
    except ValueError:
        raise DownloadError('Only credential-free HTTPS URLs on port 443 are supported') from None
    return 'https://' + value.split('://', 1)[1]


def card_id_from_url(url):
    parsed = urlsplit(normalize_url(url))
    if parsed.hostname != 'yoto.io' or not re.fullmatch(r'/[A-Za-z0-9]{5}/?', parsed.path):
        raise DownloadError('Expected a five-character card ID on yoto.io')
    return parsed.path.strip('/')


def validate_destination(url, access_token):
    parsed = urlsplit(url)
    if access_token and (parsed.hostname != 'api.yotoplay.com'
                         or not re.fullmatch(r'/card/[A-Za-z0-9]{5}', parsed.path)
                         or parsed.query or parsed.fragment):
        raise DownloadError('Authenticated requests are restricted to the Yoto card API')
    host = parsed.hostname
    if host == 'localhost' or host.endswith(('.localhost', '.local', '.internal')):
        raise DownloadError('Local network destinations are not supported')
    addresses = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(row[4][0].split('%')[0]).is_global for row in addresses):
        raise DownloadError('Non-public network destinations are not supported')


def fetch_url(url, access_token=None, *, max_bytes=MEDIA_LIMIT, max_seconds=DOWNLOAD_SECONDS):
    """Close every socket response; check elapsed time between bounded reads.

    Socket operations have 5s connect / 10s read inactivity timeouts. The elapsed
    deadline is checked between reads, so a blocked read can add up to 10s.
    No request thread survives a failure. DNS checks are defense in depth, not
    a DNS-rebinding security boundary for running this as a public service.
    """
    started = time.monotonic()
    try:
        current = normalize_url(url)
        with requests.Session() as session:
            session.trust_env = False  # no implicit .netrc credentials or environment proxies
            for redirects in range(4):
                validate_destination(current, access_token)
                remaining = max_seconds - (time.monotonic() - started)
                if remaining <= 0:
                    raise DownloadError('Download exceeded elapsed-time limit')
                headers = {'Accept-Encoding': 'identity'}
                if access_token:
                    headers['Authorization'] = f'Bearer {access_token}'
                with session.get(current, headers=headers, stream=True, allow_redirects=False,
                                 timeout=(min(5, remaining), min(10, remaining))) as response:
                    if response.status_code in (301, 302, 303, 307, 308):
                        if access_token or redirects == 3 or not response.headers.get('Location'):
                            raise DownloadError('Redirect rejected')
                        current = normalize_url(urljoin(current, response.headers['Location']))
                        continue
                    if response.status_code != 200:
                        raise DownloadError('Server did not return a successful download')
                    if response.headers.get('Content-Encoding', 'identity').lower() not in ('identity', ''):
                        raise DownloadError('Encoded responses are not supported')
                    length = response.headers.get('Content-Length')
                    if length is not None and (int(length) < 0 or int(length) > max_bytes):
                        raise DownloadError('Download exceeds size limit')
                    body = bytearray()
                    while True:
                        if time.monotonic() - started > max_seconds:
                            raise DownloadError('Download exceeded elapsed-time limit')
                        chunk = response.raw.read1(min(65536, max_bytes - len(body) + 1), decode_content=False)
                        if time.monotonic() - started > max_seconds:
                            raise DownloadError('Download exceeded elapsed-time limit')
                        if not chunk:
                            break
                        if len(body) + len(chunk) > max_bytes:
                            raise DownloadError('Download exceeds size limit')
                        body.extend(chunk)
                    result = requests.Response()
                    result.status_code = response.status_code
                    result.headers = response.headers.copy()
                    result.encoding = response.encoding or 'utf-8'
                    result._content = bytes(body)
                    return result
    except DownloadError:
        raise
    except Exception:
        # Provider URLs, request headers and error bodies must not escape to logs.
        raise DownloadError('Download failed safely') from None
