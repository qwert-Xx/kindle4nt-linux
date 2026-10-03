# SPDX-License-Identifier: GPL-2.0-or-later
import hashlib
import importlib.util
import io
import pathlib
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('source_fetch', pathlib.Path(__file__).resolve().parents[1] / 'sources/fetch.py')
fetch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fetch)


class SourceCacheTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.cache = pathlib.Path(self.temp.name)
        self.item = {'file': 'source.tar', 'url': 'https://example.invalid/source.tar',
                     'sha256': hashlib.sha256(b'source').hexdigest()}

    def test_download_then_offline(self):
        with patch.object(fetch.urllib.request, 'urlopen', return_value=io.BytesIO(b'source')) as download:
            result = fetch.checked(self.cache, self.item)
            self.assertEqual(result.read_bytes(), b'source')
            self.assertEqual(fetch.checked(self.cache, self.item, offline=True), result)
            download.assert_called_once()

    def test_missing_offline(self):
        with self.assertRaises(FileNotFoundError):
            fetch.checked(self.cache, self.item, offline=True)

    def test_tampered_cache(self):
        (self.cache / self.item['file']).write_bytes(b'changed')
        with self.assertRaises(ValueError):
            fetch.checked(self.cache, self.item, offline=True)

    def test_bad_download_never_published(self):
        with patch.object(fetch.urllib.request, 'urlopen', return_value=io.BytesIO(b'changed')):
            with self.assertRaises(ValueError):
                fetch.checked(self.cache, self.item)
        self.assertEqual(list(self.cache.iterdir()), [])


if __name__ == '__main__':
    unittest.main()
