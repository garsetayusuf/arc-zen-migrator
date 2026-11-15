"""Reverse CLI argument safety tests without browser profiles."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from arc_zen_migrator.zen2arc.cli import main
from arc_zen_migrator.zen2arc.reader import Inventory, Space

class ReverseCliTests(unittest.TestCase):
    def setUp(self):
        self.inv = Inventory([Space("work", "Work", [{
            "url": "https://example.org", "title": "Example",
            "pinned": True, "essential": False, "folder": None}])], [], [])

    @patch("arc_zen_migrator.zen2arc.cli.inspect_zen")
    def test_preview(self, inspect):
        inspect.return_value = self.inv
        self.assertEqual(main(["--zen-profile", "fake", "--preview"]), 0)

    @patch("arc_zen_migrator.zen2arc.cli.inspect_zen")
    def test_empty_selection(self, inspect):
        inspect.return_value = self.inv
        self.assertEqual(main(["--zen-profile", "fake", "--space", "other"]), 0)

    @patch("arc_zen_migrator.zen2arc.cli.inspect_zen")
    def test_import_requires_backup_directory(self, inspect):
        inspect.return_value = self.inv
        with self.assertRaises(SystemExit) as error:
            main(["--zen-profile", "fake", "--test-bookmarks-profile", "test"])
        self.assertEqual(error.exception.code, 2)

if __name__ == "__main__":
    unittest.main()
