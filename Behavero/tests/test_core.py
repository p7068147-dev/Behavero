import tempfile
import unittest
from pathlib import Path
from behavero.core import compare_snapshots, snapshot_tree
from behavero.storage import load_json, save_json

class SnapshotTests(unittest.TestCase):
    def test_created_deleted_modified(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "changed.txt").write_text("before", encoding="utf-8")
            (root / "deleted.txt").write_text("remove", encoding="utf-8")
            before = snapshot_tree(root)
            (root / "changed.txt").write_text("after!", encoding="utf-8")
            (root / "deleted.txt").unlink()
            (root / "created.txt").write_text("new", encoding="utf-8")
            report = compare_snapshots(before, snapshot_tree(root))
            self.assertEqual(report["summary"]["created"], 1)
            self.assertEqual(report["summary"]["deleted"], 1)
            self.assertEqual(report["summary"]["modified"], 1)

    def test_hash_detects_same_size_change(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            p = root / "item"
            p.write_text("abc", encoding="utf-8")
            before = snapshot_tree(root)
            p.write_text("xyz", encoding="utf-8")
            report = compare_snapshots(before, snapshot_tree(root))
            self.assertIn("sha256", report["modified"][0]["changed_fields"])

    def test_rejects_bad_schema(self):
        with self.assertRaises(ValueError):
            compare_snapshots({"schema_version": 99, "entries": {}},
                              {"schema_version": 1, "entries": {}})

    def test_json_round_trip(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "snapshot.json"
            save_json({"schema_version": 1}, path)
            self.assertEqual(load_json(path), {"schema_version": 1})

if __name__ == "__main__":
    unittest.main()
