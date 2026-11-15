"""Synthetic Mozilla LZ4 session tests; no real browser data."""
import json
import struct
import sys
import tempfile
import unittest
from pathlib import Path
import lz4.block
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from arc_zen_migrator.zen2arc.reader import inspect_zen, read_mozlz4

class ZenSessionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.profile = Path(self.tmp.name)

    def session(self, name, payload):
        raw = json.dumps(payload).encode()
        (self.profile / name).write_bytes(b"mozLz40\x00" + struct.pack("<I", len(raw)) + lz4.block.compress(raw, store_size=False))

    def test_spaces_and_pinned_tabs(self):
        self.session("zen-sessions.jsonlz4", {
            "windows": [{"spaces": [{"uuid": "work", "name": "Work"}],
                         "tabs": [{"zenWorkspace": "work", "pinned": True,
                                   "zenEssential": True, "entries": [{"url": "https://example.org"}],
                                   "index": 1},
                                  {"entries": [{"url": "file:///private"}], "index": 1}]}]})
        inv = inspect_zen(self.profile)
        self.assertEqual(len(inv.spaces), 1)
        self.assertEqual(inv.tab_count, 1)
        self.assertEqual(inv.pinned_count, 1)
        self.assertEqual(inv.essential_count, 1)
        self.assertTrue(inv.warnings)

    def test_bad_signature(self):
        (self.profile / "zen-sessions.jsonlz4").write_bytes(b"wrong")
        with self.assertRaises(ValueError):
            read_mozlz4(self.profile / "zen-sessions.jsonlz4")

    def test_truncated_payload(self):
        (self.profile / "zen-sessions.jsonlz4").write_bytes(b"mozLz40\x00" + struct.pack("<I", 10) + b"bad")
        with self.assertRaises((ValueError, lz4.block.LZ4BlockError)):
            read_mozlz4(self.profile / "zen-sessions.jsonlz4")

if __name__ == "__main__":
    unittest.main()
