import base64
import hashlib
import io
import json
import types
import unittest
from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs, urlsplit

import login


class LoginTests(unittest.TestCase):
    def test_callback_requires_exact_destination_and_matching_unique_state(self):
        good = login.REDIRECT_URL + '?code=SYNTHETIC_CODE&state=expected'
        self.assertEqual(login.parse_callback(good, 'expected'), 'SYNTHETIC_CODE')
        bad = [good.replace('127.0.0.1', 'evil.invalid'),
               'https://evil.invalid/?next=' + good,
               good.replace(':3000', ':3001'), good.replace('/callback', '/callback/extra'),
               good.replace('http:', 'https:'), good.replace('state=expected', 'state=wrong'),
               good.replace('state=expected', 'state=%E2%98%83'), good + '&state=expected', good + '&code=extra', good + '#access_token=SYNTHETIC_TOKEN',
               good + '&access_token=SYNTHETIC_TOKEN', good.replace('code=SYNTHETIC_CODE', 'code='),
               login.REDIRECT_URL + '?error=access_denied&state=expected']
        for url in bad:
            with self.subTest(url=url), self.assertRaises(ValueError):
                login.parse_callback(url, 'expected')

    def test_authorization_uses_s256_pkce_and_read_only_scopes(self):
        verifier = 'synthetic-verifier'
        query = parse_qs(urlsplit(login.authorization_url('client', 'state', verifier)).query)
        expected = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b'=').decode()
        self.assertEqual(query['code_challenge'], [expected])
        self.assertEqual(query['code_challenge_method'], ['S256'])
        self.assertEqual(query['response_type'], ['code'])
        self.assertNotIn('offline_access', query['scope'][0])
        self.assertNotIn('profile', query['scope'][0])

    def test_exchange_limits_response_and_never_follows_redirects(self):
        response = MagicMock(status_code=200)
        response.__enter__.return_value = response
        response.iter_content.return_value = [json.dumps({'access_token': 'SYNTHETIC_TOKEN', 'token_type': 'Bearer', 'expires_in': 60}).encode()]
        with patch('login.requests.post', return_value=response) as post:
            self.assertEqual(login.exchange_code('client', 'code', 'verifier'), 'SYNTHETIC_TOKEN')
            self.assertFalse(post.call_args.kwargs['allow_redirects'])
            self.assertEqual(post.call_args.kwargs['timeout'], (10, 15))
            self.assertEqual(post.call_args.kwargs['data']['code_verifier'], 'verifier')
        response.iter_content.return_value = [b'x' * 65537]
        with patch('login.requests.post', return_value=response), self.assertRaisesRegex(ValueError, 'safely'):
            login.exchange_code('client', 'code', 'verifier')
        self.assertTrue(response.__exit__.called)

    def test_login_closes_listener_and_keeps_failures_free_of_secrets(self):
        server = MagicMock(code='SYNTHETIC_CODE')
        server.__enter__.return_value = server
        with patch.dict('os.environ', {'YOTO_CLIENT_ID': 'syntheticclient'}), \
             patch('login.callback_server', return_value=server), \
             patch('login.webbrowser.open', return_value=True), \
             patch('login.exchange_code', side_effect=ValueError('SYNTHETIC_TOKEN')), \
             patch('sys.stdout', new_callable=io.StringIO) as output:
            self.assertIsNone(login.get_access_token())
            self.assertNotIn('SYNTHETIC', output.getvalue())
        self.assertTrue(server.__exit__.called)

    def test_occupied_callback_port_fails_before_opening_browser(self):
        with patch.dict('os.environ', {'YOTO_CLIENT_ID': 'syntheticclient'}), \
             patch('login.callback_server', side_effect=OSError('occupied')), \
             patch('login.webbrowser.open') as browser, patch('sys.stdout', new_callable=io.StringIO):
            self.assertIsNone(login.get_access_token())
            browser.assert_not_called()


if __name__ == '__main__':
    unittest.main()
