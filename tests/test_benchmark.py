from __future__ import annotations

import csv
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class BenchmarkTest(unittest.TestCase):
    def test_runner_records_output_and_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary = Path(temporary_directory)
            inputs = temporary / "inputs"
            outputs = temporary / "outputs"
            log = temporary / "runs.csv"
            inputs.mkdir()
            (inputs / "case.txt").write_text("hello\n", encoding="utf-8")

            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "tools" / "benchmark.py"),
                    "--solver",
                    "/bin/cat",
                    "--inputs",
                    str(inputs),
                    "--outputs",
                    str(outputs),
                    "--runs",
                    "2",
                    "--log",
                    str(log),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(
                (outputs / "case.txt.run-1.out").read_text(encoding="utf-8"),
                "hello\n",
            )
            with log.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["output_bytes"], "6")
            self.assertEqual(len(rows[0]["output_sha256"]), 64)


if __name__ == "__main__":
    unittest.main()

