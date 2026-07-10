from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_PROGRAMME_COUNT = 13_986
EXPECTED_ID_SHA256 = "a8791168c769d29740e6b305b09fb5a29039cc1654c569beca71da7ff4e4901d"
EXPECTED_SOURCE_COUNTS = {
    "cambridgePrograms.ts": 392,
    "edinburghPrograms.ts": 816,
    "imperialPrograms.ts": 248,
    "kclPrograms.ts": 477,
    "lbsPrograms.ts": 17,
    "lsePrograms.ts": 263,
    "manchesterPrograms.ts": 934,
    "oxfordPrograms.ts": 459,
    "singaporePrograms.ts": 617,
    "uclPrograms.ts": 1_137,
    "usPrograms.ts": 8_179,
    "warwickPrograms.ts": 447,
}
BUILDERS = [
    "build_cambridge_catalogue.py",
    "build_edinburgh_catalogue.py",
    "build_imperial_catalogue.py",
    "build_kcl_catalogue.py",
    "build_lse_catalogue.py",
    "build_manchester_catalogue.py",
    "build_ucl_catalogue.py",
    "build_us_singapore_catalogues.py",
    "build_warwick_catalogue.py",
    "build_oxford_catalogue.mjs",
]


class CatalogueTests(unittest.TestCase):
    def test_catalogue_validator_and_preserved_identity_lock(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "validate_catalogues.py"), "--json"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
        )
        report = json.loads(proc.stdout)
        self.assertEqual(report["programme_count"], EXPECTED_PROGRAMME_COUNT)
        self.assertEqual(report["programme_id_sha256"], EXPECTED_ID_SHA256)
        self.assertEqual(report["by_degree"], {"Postgraduate": 7_766, "Undergraduate": 6_220})
        self.assertEqual(report["by_migration_source"], EXPECTED_SOURCE_COUNTS)

    def test_all_builders_target_plugin_owned_catalogues(self) -> None:
        for filename in BUILDERS:
            body = (ROOT / "scripts" / filename).read_text(encoding="utf-8")
            self.assertNotIn("web/src/data", body, filename)
            self.assertNotRegex(body, r'"web"\s*/\s*"src"\s*/\s*"data"', filename)
            self.assertIn("catalogue", body.lower(), filename)

    def test_lbs_is_an_explicit_non_builder_conversion(self) -> None:
        lbs = json.loads((ROOT / "catalogues" / "institutions" / "lbs.json").read_text(encoding="utf-8"))
        self.assertEqual(lbs["catalogue_provenance"]["migration_source"], "lbsPrograms.ts")
        self.assertEqual(len(lbs["programmes"]), 17)
        self.assertFalse((ROOT / "scripts" / "build_lbs_catalogue.py").exists())

    def test_detailed_placeholder_programs_file_is_not_a_source(self) -> None:
        index = json.loads((ROOT / "catalogues" / "index.json").read_text(encoding="utf-8"))
        sources = {entry["migration_source"] for entry in index["institutions"]}
        self.assertNotIn("programs.ts", sources)


if __name__ == "__main__":
    unittest.main()
