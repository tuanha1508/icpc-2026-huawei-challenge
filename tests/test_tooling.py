from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ToolingTest(unittest.TestCase):
    def test_material_inventory_is_sorted_hashed_and_self_excluding(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            materials = Path(temporary_directory) / "materials"
            (materials / "nested").mkdir(parents=True)
            (materials / "z.txt").write_bytes(b"last\n")
            (materials / "nested" / "a.bin").write_bytes(b"first\x00")
            inventory_path = materials / "inventory.json"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "tools" / "inventory_materials.py"),
                    "--root",
                    str(materials),
                    "--output",
                    str(inventory_path),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
            self.assertEqual(
                [entry["path"] for entry in inventory["files"]],
                ["nested/a.bin", "z.txt"],
            )
            self.assertEqual(
                inventory["files"][0]["sha256"],
                hashlib.sha256(b"first\x00").hexdigest(),
            )
            self.assertNotIn("inventory.json", [entry["path"] for entry in inventory["files"]])

    def test_case_split_is_deterministic_and_duplicate_safe(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary = Path(temporary_directory)
            inputs = temporary / "cases"
            inputs.mkdir()
            (inputs / "a.in").write_bytes(b"duplicate\n")
            (inputs / "b.in").write_bytes(b"different-b\n")
            (inputs / "c.in").write_bytes(b"duplicate\n")
            (inputs / "d.in").write_bytes(b"different-d\n")
            first = temporary / "first.json"
            second = temporary / "second.json"
            command = [
                sys.executable,
                str(ROOT / "tools" / "split_cases.py"),
                "--inputs",
                str(inputs),
                "--seed",
                "fixed-test-seed",
                "--heldout-percent",
                "25",
            ]
            for output in (first, second):
                completed = subprocess.run(
                    [*command, "--output", str(output)],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            manifest = json.loads(first.read_text(encoding="utf-8"))
            split = {case["path"]: case["split"] for case in manifest["cases"]}
            self.assertEqual(split["a.in"], split["c.in"])
            self.assertGreater(manifest["counts"]["tuning"], 0)
            self.assertGreater(manifest["counts"]["heldout"], 0)

    def test_preflight_has_machine_readable_success_report(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(ROOT / "tools" / "preflight.py"),
                "--root",
                str(ROOT),
                "--min-free-gib",
                "0",
                "--warn-free-gib",
                "0",
                "--json",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        report = json.loads(completed.stdout)
        statuses = {check["name"]: check["status"] for check in report["checks"]}
        self.assertEqual(statuses["workspace"], "ok")
        self.assertEqual(statuses["tool:c++"], "ok")

    def test_flattened_solver_compiles(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary = Path(temporary_directory)
            flattened = temporary / "submission.cpp"
            executable = temporary / "submission"
            flatten = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "tools" / "flatten_cpp.py"),
                    "--source",
                    str(ROOT / "src" / "main.cpp"),
                    "--include-dir",
                    str(ROOT / "include"),
                    "--output",
                    str(flattened),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(flatten.returncode, 0, flatten.stderr)
            self.assertNotIn('#include "foundation.hpp"', flattened.read_text())
            compile_result = subprocess.run(
                ["c++", "-std=c++20", str(flattened), "-o", str(executable)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(compile_result.returncode, 0, compile_result.stderr)

    def test_historical_submission_flattens_compiles_and_runs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary = Path(temporary_directory)
            flattened = temporary / "xr_submission.cpp"
            executable = temporary / "xr_submission"
            flatten = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "tools" / "flatten_cpp.py"),
                    "--source",
                    str(ROOT / "practice" / "xr2023" / "submission_entry.cpp"),
                    "--include-dir",
                    str(ROOT / "practice" / "xr2023" / "include"),
                    "--output",
                    str(flattened),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(flatten.returncode, 0, flatten.stderr)
            compile_result = subprocess.run(
                ["c++", "-std=c++20", "-O2", str(flattened), "-o", str(executable)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(compile_result.returncode, 0, compile_result.stderr)
            sample = (ROOT / "practice" / "xr2023" / "data" / "sample.in").read_text()
            run = subprocess.run(
                [str(executable)],
                input=sample,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(run.returncode, 0, run.stderr)
            values = [float(token) for token in run.stdout.split()]
            self.assertEqual(len(values), 8)
            self.assertTrue(all(value >= 0.0 for value in values))

    def test_sweep_expands_grid_deterministically(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary = Path(temporary_directory)
            inputs = temporary / "inputs"
            inputs.mkdir()
            (inputs / "b.txt").write_text("b\n", encoding="utf-8")
            (inputs / "a.txt").write_text("a\n", encoding="utf-8")
            config = temporary / "sweep.json"
            config.write_text(
                json.dumps(
                    {
                        "command": ["/bin/echo", "{alpha}", "{beta}"],
                        "grid": {"beta": [3], "alpha": [1, 2]},
                    }
                ),
                encoding="utf-8",
            )
            log = temporary / "sweep.csv"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "tools" / "sweep.py"),
                    "--config",
                    str(config),
                    "--inputs",
                    str(inputs),
                    "--outputs",
                    str(temporary / "outputs"),
                    "--log",
                    str(log),
                    "--jobs",
                    "2",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            with log.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 4)
            self.assertEqual(
                [(row["candidate"], row["case"]) for row in rows],
                [
                    ("candidate-0000", "a.txt"),
                    ("candidate-0000", "b.txt"),
                    ("candidate-0001", "a.txt"),
                    ("candidate-0001", "b.txt"),
                ],
            )

    def test_packager_writes_hash_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_dir = Path(temporary_directory) / "packages"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "tools" / "package_submission.py"),
                    "--source",
                    str(ROOT / "src" / "main.cpp"),
                    "--include-dir",
                    str(ROOT / "include"),
                    "--output-dir",
                    str(output_dir),
                    "--label",
                    "smoke test",
                    "--parameters",
                    '{"seed":7}',
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            packages = list(output_dir.iterdir())
            self.assertEqual(len(packages), 1)
            manifest = json.loads((packages[0] / "manifest.json").read_text())
            self.assertEqual(manifest["parameters"], {"seed": 7})
            self.assertEqual(len(manifest["sha256"]), 64)
            self.assertTrue((packages[0] / "submission.cpp").is_file())

    def test_rank_sweep_requires_explicit_aggregation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            log = Path(temporary_directory) / "sweep.csv"
            fieldnames = [
                "timestamp_utc",
                "candidate",
                "parameters_json",
                "case",
                "wall_ms",
                "exit_code",
                "timed_out",
                "output_bytes",
                "output_sha256",
                "score",
                "scorer_exit_code",
            ]
            with log.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=fieldnames)
                writer.writeheader()
                for candidate, parameters, scores in [
                    ("candidate-0000", '{"x":1}', [3, 4]),
                    ("candidate-0001", '{"x":2}', [8, 1]),
                ]:
                    for index, score in enumerate(scores):
                        writer.writerow(
                            {
                                "timestamp_utc": "",
                                "candidate": candidate,
                                "parameters_json": parameters,
                                "case": f"{index}.txt",
                                "wall_ms": "1",
                                "exit_code": "0",
                                "timed_out": "0",
                                "output_bytes": "0",
                                "output_sha256": "",
                                "score": str(score),
                                "scorer_exit_code": "0",
                            }
                        )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "tools" / "rank_sweep.py"),
                    "--log",
                    str(log),
                    "--aggregate",
                    "sum",
                    "--direction",
                    "maximize",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("1\tcandidate-0001\t9", completed.stdout)
            self.assertIn("2\tcandidate-0000\t7", completed.stdout)


if __name__ == "__main__":
    unittest.main()
