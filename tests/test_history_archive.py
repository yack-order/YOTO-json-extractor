import hashlib
import json
from pathlib import Path
import unittest


class HistoryArchiveTests(unittest.TestCase):
    def test_provenance_snapshot_is_complete_and_matches_its_checksums(self):
        root = Path(__file__).resolve().parents[1] / 'history'
        for line in (root / 'checksums.sha256').read_text().splitlines():
            expected, name = line.split('  ', 1)
            self.assertEqual(hashlib.sha256((root / name).read_bytes()).hexdigest(), expected)
        snapshot = json.loads((root / 'legacy-github-metadata.json').read_text())
        repository = snapshot['repository']
        for kind in ('issues', 'pullRequests'):
            connection = repository[kind]
            self.assertEqual(connection['totalCount'], len(connection['nodes']))
            self.assertFalse(connection['pageInfo']['hasNextPage'])
            self.assertEqual(len({n['number'] for n in connection['nodes']}), connection['totalCount'])
            for node in connection['nodes']:
                self.assertTrue(node['url'].startswith('https://github.com/yack-order/YOTO-json-extractor-v2/'))
        def assert_complete(value):
            if isinstance(value, dict):
                if 'hasNextPage' in value:
                    self.assertFalse(value['hasNextPage'])
                for item in value.values():
                    assert_complete(item)
            elif isinstance(value, list):
                for item in value:
                    assert_complete(item)
        assert_complete(repository)
        self.assertEqual(repository['issues']['totalCount'], 7)
        self.assertEqual(repository['pullRequests']['totalCount'], 8)
