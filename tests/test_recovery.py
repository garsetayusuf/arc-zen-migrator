"""Recovery and privacy regression tests."""
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from arc_zen_migrator.recovery import create_backup, verify_backup, restore_backup, checksum
from arc_zen_migrator.zen2arc.report import summary
from arc_zen_migrator.zen2arc.reader import Space, Inventory

class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / "profile" / "test.db"
        self.source.parent.mkdir()
        self.source.write_bytes(b"before")

    def backup(self):
        return create_backup(self.source, self.root / "backups")

    def test_backup_restore(self):
        backup = self.backup()
        self.assertEqual(verify_backup(backup)["sha256"], checksum(self.source))
        self.source.write_bytes(b"after")
        restore_backup(backup, self.source, expected_sha256=checksum(self.source))
        self.assertEqual(self.source.read_bytes(), b"before")

    def test_refuses_unexpected_overwrite(self):
        backup = self.backup()
        self.source.write_bytes(b"changed")
        with self.assertRaises(ValueError):
            restore_backup(backup, self.source)
        self.assertEqual(self.source.read_bytes(), b"changed")

    def test_detects_corruption(self):
        backup = self.backup()
        (backup / "payload.bin").write_bytes(b"tampered")
        with self.assertRaises(ValueError):
            verify_backup(backup)

    def test_source_unchanged(self):
        self.backup()
        self.assertEqual(self.source.read_bytes(), b"before")

    def test_report_excludes_sensitive_urls_and_titles(self):
        inventory = Inventory([Space("id", "Private", tabs=[
            {"url": "https://secret.example/token", "title": "Sensitive",
             "pinned": True, "essential": False}])], [], [])
        output = str(summary(inventory))
        for sensitive in ("secret.example", "Sensitive", "Private"):
            self.assertNotIn(sensitive, output)

if __name__ == "__main__":
    unittest.main()
