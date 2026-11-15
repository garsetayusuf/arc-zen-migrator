"""Browser guard tests with isolated fake process metadata."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from arc_zen_migrator.browser_guard import require_browsers_closed
from arc_zen_migrator.recovery_cli import main

class BrowserGuardTests(unittest.TestCase):
    def test_refuses_open_browser(self):
        with patch("arc_zen_migrator.browser_guard.running_browsers", return_value=["Arc"]):
            with self.assertRaises(RuntimeError):
                require_browsers_closed()

    def test_allows_closed_browsers(self):
        with patch("arc_zen_migrator.browser_guard.running_browsers", return_value=[]):
            require_browsers_closed()

    def test_cli_requires_command(self):
        with self.assertRaises(SystemExit) as error:
            main([])
        self.assertEqual(error.exception.code, 2)

if __name__ == "__main__":
    unittest.main()
