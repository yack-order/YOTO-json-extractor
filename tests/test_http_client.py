import socket
import unittest
from unittest.mock import MagicMock, patch

import requests
import http_client as http

PUBLIC_DNS = [(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('93.184.216.34', 443))]


class HttpTests(unittest.TestCase):
    def setUp(self):
        self.dns = patch('http_client.socket.getaddrinfo', return_value=PUBLIC_DNS)
        self.dns.start()
        self.addCleanup(self.dns.stop)
        self.session = MagicMock()
        self.session.__enter__.return_value = self.session
        self.session_patch = patch('http_client.requests.Session', return_value=self.session)
        self.session_patch.start()
        self.addCleanup(self.session_patch.stop)

    def response(self, chunks=(b'abc', b''), headers=None, status=200):
        response = MagicMock(status_code=status, headers=headers or {}, encoding='utf-8')
        response.__enter__.return_value = response
        response.raw.read1.side_effect = chunks
        self.session.get.return_value = response
        return response

    def test_success_has_socket_limits_closes_response_and_disables_netrc(self):
        response = self.response()
        result = http.fetch_url('https://example.invalid/media')
        self.assertEqual(result.content, b'abc')
        self.assertEqual(result.text, 'abc')
        self.assertFalse(self.session.trust_env)
        args = self.session.get.call_args.kwargs
        self.assertFalse(args['allow_redirects'])
        self.assertEqual(args['timeout'], (5, 10))
        self.assertNotIn('Authorization', args['headers'])
        self.assertTrue(response.__exit__.called)

    def test_declared_and_streamed_oversized_responses_are_closed(self):
        for response in (self.response(headers={'Content-Length': '100'}), self.response(chunks=[b'12345'])):
            self.session.get.return_value = response
            with self.assertRaises(http.DownloadError):
                http.fetch_url('https://example.invalid/media', max_bytes=4)
            self.assertTrue(response.__exit__.called)

    def test_elapsed_deadline_and_socket_errors_are_sanitized(self):
        response = self.response()
        with patch('http_client.time.monotonic', side_effect=[0, 0, 0, 121]):
            with self.assertRaisesRegex(http.DownloadError, 'elapsed-time'):
                http.fetch_url('https://example.invalid/media')
        self.assertTrue(response.__exit__.called)
        self.session.get.side_effect = requests.Timeout('SYNTHETIC_SECRET_URL')
        with self.assertRaisesRegex(http.DownloadError, '^Download failed safely$'):
            http.fetch_url('https://example.invalid/media')

    def test_https_and_public_destination_checks(self):
        for url in ('http://example.invalid', 'file:///etc/passwd', 'https://user:pass@example.invalid', 'https://example.invalid:8443'):
            with self.subTest(url=url), self.assertRaises(http.DownloadError):
                http.fetch_url(url)
        with patch('http_client.socket.getaddrinfo', return_value=[(2, 1, 6, '', ('127.0.0.1', 443))]):
            with self.assertRaises(http.DownloadError):
                http.fetch_url('https://example.invalid')
        self.session.get.assert_not_called()

    def test_bearer_token_only_reaches_exact_yoto_card_api_and_never_redirects(self):
        for url in ('https://evil.invalid/card/ABCDE', 'https://api.yotoplay.com.evil.invalid/card/ABCDE',
                    'https://api.yotoplay.com/card/ABCDE?next=evil', 'https://api.yotoplay.com/other'):
            with self.assertRaises(http.DownloadError):
                http.fetch_url(url, 'SYNTHETIC_TOKEN')
        self.session.get.assert_not_called()
        response = self.response(status=302, headers={'Location': 'https://evil.invalid'})
        with self.assertRaisesRegex(http.DownloadError, 'Redirect rejected'):
            http.fetch_url('https://api.yotoplay.com/card/ABCDE', 'SYNTHETIC_TOKEN')
        self.assertEqual(self.session.get.call_count, 1)
        self.assertEqual(self.session.get.call_args.kwargs['headers']['Authorization'], 'Bearer SYNTHETIC_TOKEN')
        self.assertTrue(response.__exit__.called)

    def test_redirects_revalidate_scheme_destination_and_maximum_hops(self):
        self.response(status=302, headers={'Location': 'http://example.invalid'})
        with self.assertRaises(http.DownloadError):
            http.fetch_url('https://example.invalid')
        self.session.get.reset_mock()
        self.response(status=302, headers={'Location': '/again'})
        with self.assertRaisesRegex(http.DownloadError, 'Redirect rejected'):
            http.fetch_url('https://example.invalid')
        self.assertEqual(self.session.get.call_count, 4)

    def test_encoded_response_and_http_errors_fail_without_buffering(self):
        for response in (self.response(headers={'Content-Encoding': 'gzip'}), self.response(status=403)):
            self.session.get.return_value = response
            with self.assertRaises(http.DownloadError):
                http.fetch_url('https://example.invalid')
            response.raw.read1.assert_not_called()

    def test_card_identifier_does_not_accept_host_substrings_or_path_injection(self):
        self.assertEqual(http.card_id_from_url('https://yoto.io/ABCDE?s=synthetic'), 'ABCDE')
        for url in ('https://evil.invalid/yoto.io/ABCDE', 'https://yoto.io.evil.invalid/ABCDE',
                    'https://yoto.io/AB/DE', 'https://yoto.io/../ABCDE'):
            with self.assertRaises(http.DownloadError):
                http.card_id_from_url(url)


if __name__ == '__main__':
    unittest.main()
