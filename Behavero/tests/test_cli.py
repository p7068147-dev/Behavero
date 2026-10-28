import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

class CliTests(unittest.TestCase):
    def test_run_records_created_file(self):
        project = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as folder:
            lab = Path(folder) / "lab"
            lab.mkdir()
            report_path = Path(folder) / "report.json"
            code = "from pathlib import Path; Path('demo.txt').write_text('hello', encoding='utf-8')"
            result = subprocess.run(
                [sys.executable, "-S", "-m", "behavero", "run",
                 "--output", str(report_path), str(lab), "--", sys.executable, "-c", code],
                cwd=project, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(report["summary"]["created"], 1)
            self.assertEqual(report["created"][0]["path"], "demo.txt")
            self.assertEqual(report["execution"]["exit_code"], 0)

if __name__ == "__main__":
    unittest.main()
