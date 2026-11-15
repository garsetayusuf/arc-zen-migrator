"""Safe fixture tests for the reverse inventory and feature gates."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from arc_zen_migrator.zen2arc.capabilities import require_verified, Status, ZEN_TO_ARC
from arc_zen_migrator.zen2arc.reader import Inventory, Space

class ReverseSafetyTests(unittest.TestCase):
    def test_cloudkit_writes_are_blocked(self):
        for category in ("spaces", "tabs", "pinned_tabs", "essentials", "folders", "cookies", "passwords"):
            with self.assertRaises(RuntimeError):
                require_verified(category)

    def test_inventory_counts(self):
        s = Space("1", "Work", tabs=[{"pinned": True, "essential": True},
                                        {"pinned": False, "essential": False}])
        inventory = Inventory([s], [], [])
        self.assertEqual(inventory.tab_count, 2)
        self.assertEqual(inventory.pinned_count, 1)
        self.assertEqual(inventory.essential_count, 1)

    def test_no_reverse_feature_claimed_verified(self):
        self.assertNotIn(Status.VERIFIED, ZEN_TO_ARC.values())

if __name__ == "__main__":
    unittest.main()
