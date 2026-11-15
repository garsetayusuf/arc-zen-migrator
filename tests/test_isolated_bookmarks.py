"""Isolated Chromium bookmark import tests; never use a real Arc profile."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from arc_zen_migrator.zen2arc.reader import Inventory, Space
from arc_zen_migrator.zen2arc.planner import plan_zen_to_arc
from arc_zen_migrator.zen2arc.bookmarks import import_bookmarks, MARKER
from arc_zen_migrator.recovery import verify_backup

class IsolatedImportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.profile = self.root / "test-profile"
        self.profile.mkdir()
        self.file = self.profile / "Bookmarks"
        self.file.write_text(json.dumps({"roots": {"other": {"type": "folder", "children": []},
            "bookmark_bar": {"type": "folder", "children": []}}}))
        tab = {"url": "https://example.org", "title": "Example", "pinned": True,
               "essential": False, "folder": None}
        self.plan = plan_zen_to_arc(Inventory([Space("work", "Work", [tab])], [], []))
        self.backups = self.root / "backups"

    @patch("arc_zen_migrator.zen2arc.bookmarks.require_browsers_closed")
    def test_import_and_idempotency(self, guard):
        (self.profile / MARKER).touch()
        result = import_bookmarks(self.plan, self.profile, self.backups, confirm_isolated=True)
        self.assertEqual(result["imported"], 1)
        self.assertEqual(verify_backup(Path(result["backup"]))["format"], 1)
        second = import_bookmarks(self.plan, self.profile, self.backups, confirm_isolated=True)
        self.assertEqual(second["imported"], 0)
        self.assertEqual(len(json.loads(self.file.read_text())["roots"]["other"]["children"]), 1)

    @patch("arc_zen_migrator.zen2arc.bookmarks.require_browsers_closed")
    def test_refuse_missing_marker(self, guard):
        with self.assertRaises(PermissionError):
            import_bookmarks(self.plan, self.profile, self.backups, confirm_isolated=True)

    @patch("arc_zen_migrator.zen2arc.bookmarks.require_browsers_closed")
    def test_refuse_missing_confirmation(self, guard):
        (self.profile / MARKER).touch()
        with self.assertRaises(PermissionError):
            import_bookmarks(self.plan, self.profile, self.backups)

    @patch("arc_zen_migrator.zen2arc.bookmarks.require_browsers_closed")
    def test_live_arc_directory_is_rejected(self, guard):
        from unittest.mock import patch as mock_patch
        home = self.root / "fake-home"
        live = home / "Library" / "Application Support" / "Arc" / "Default"
        live.mkdir(parents=True)
        (live / MARKER).touch()
        (live / "Bookmarks").write_bytes(self.file.read_bytes())
        with mock_patch("arc_zen_migrator.zen2arc.bookmarks.Path.home", return_value=home):
            with self.assertRaises(PermissionError):
                import_bookmarks(self.plan, live, self.backups, confirm_isolated=True)

    @patch("arc_zen_migrator.zen2arc.bookmarks.require_browsers_closed")
    def test_source_plan_is_unchanged(self, guard):
        (self.profile / MARKER).touch()
        before = self.plan
        import_bookmarks(self.plan, self.profile, self.backups, confirm_isolated=True)
        self.assertEqual(self.plan, before)

if __name__ == "__main__":
    unittest.main()
