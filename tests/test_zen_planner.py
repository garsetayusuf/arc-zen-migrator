"""Deterministic planning and selection tests."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from arc_zen_migrator.zen2arc.planner import plan_zen_to_arc
from arc_zen_migrator.zen2arc.reader import Inventory, Space

def tab(url="https://example.org", pinned=False):
    return {"url": url, "title": "Example", "pinned": pinned, "essential": False, "folder": None}

class PlannerTests(unittest.TestCase):
    def setUp(self):
        self.inventory = Inventory([Space("a", "Work", [tab(), tab()]),
                                    Space("b", "Personal", [tab()])], [tab()], [])

    def test_deterministic_dedup_scoped_by_space(self):
        a = plan_zen_to_arc(self.inventory)
        b = plan_zen_to_arc(self.inventory)
        self.assertEqual(a, b)
        self.assertEqual(len(a.tabs), 3)
        self.assertEqual(a.duplicate_count, 1)
        self.assertEqual(a.status, "preview-only")

    def test_empty_selection_selects_none(self):
        result = plan_zen_to_arc(self.inventory, selected_spaces=set())
        self.assertEqual(result.tabs, ())
        self.assertEqual(result.excluded_count, 4)

    def test_space_selection(self):
        result = plan_zen_to_arc(self.inventory, selected_spaces={"b"})
        self.assertEqual(len(result.tabs), 1)
        self.assertEqual(result.tabs[0].source_space, "b")

    def test_pinned_status_keeps_distinct_tabs(self):
        inventory = Inventory([Space("a", "Work", [tab(), tab(pinned=True)])], [], [])
        self.assertEqual(len(plan_zen_to_arc(inventory).tabs), 2)

if __name__ == "__main__":
    unittest.main()
