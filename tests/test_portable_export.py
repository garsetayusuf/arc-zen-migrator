"""Portable export tests: hierarchy, HTML escaping, and safe writes."""
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from arc_zen_migrator.zen2arc.planner import MigrationPlan, PlannedTab
from arc_zen_migrator.zen2arc.export import render_bookmarks, export_bookmarks

class ExportTests(unittest.TestCase):
    def setUp(self):
        self.plan = MigrationPlan((
            PlannedTab("work", "https://example.org/?a=1&b=2", "<Important>", True, False, "Docs", "1"),
            PlannedTab("work", "https://safe.example", "Essential", False, True, None, "2"),
            PlannedTab("", "about:config", "Excluded", False, False, None, "3"),
        ), 0, 0)

    def test_html_escape_and_hierarchy(self):
        html = render_bookmarks(self.plan, space_names={"work": "My Work"})
        self.assertIn("My Work", html)
        self.assertIn("Pinned", html)
        self.assertIn("Essentials", html)
        self.assertIn("Docs", html)
        self.assertIn("&lt;Important&gt;", html)
        self.assertIn("a=1&amp;b=2", html)
        self.assertNotIn("about:config", html)

    def test_refuse_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bookmarks.html"
            export_bookmarks(self.plan, path)
            before = path.read_bytes()
            with self.assertRaises(FileExistsError):
                export_bookmarks(self.plan, path)
            self.assertEqual(before, path.read_bytes())

    def test_deterministic_rendering(self):
        self.assertEqual(render_bookmarks(self.plan), render_bookmarks(self.plan))

if __name__ == "__main__":
    unittest.main()
