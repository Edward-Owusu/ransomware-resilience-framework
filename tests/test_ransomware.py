import json
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ransomware_ready import assess, load_practices, load_systems, parse_practices, parse_systems  # noqa: E402
from ransomware_ready.cli import main  # noqa: E402
from ransomware_ready.engine import DataError  # noqa: E402
from ransomware_ready.reporting import WRITERS, gauge_svg  # noqa: E402

AS_OF = date(2026, 10, 6)
S = ROOT / "samples"
H = ("system,criticality,rto_hours,rpo_hours,backup_type,backup_frequency_hours,offline_or_immutable,backup_encrypted,"
     "separate_backup_credentials,backup_monitored,last_restore_test_date,restore_time_hours,restore_time_measured,depends_on")
GOOD = "true,true,true,true,2026-06-01"


def run(*rows, practices=None):
    return assess(parse_systems(H + "\n" + "\n".join(rows)), practices, "T", as_of=AS_OF)


def ids(result, name):
    return {f.check_id for s in result.systems if s.system == name for f in s.findings}


class TestParsing(unittest.TestCase):
    def test_rejects_bad_input(self):
        with self.assertRaisesRegex(DataError, "missing required"):
            parse_systems("system,criticality\nA,high\n")
        with self.assertRaisesRegex(DataError, "backup_type"):
            parse_systems(H + "\nA,high,8,24,tape,24," + GOOD + ",4,true,")
        with self.assertRaisesRegex(DataError, "not in the file"):
            parse_systems(H + "\nA,high,8,24,image,24," + GOOD + ",4,true,Ghost")
        with self.assertRaisesRegex(DataError, "number of hours"):
            parse_systems(H + "\nA,high,eight,24,image,24," + GOOD + ",4,true,")
        with self.assertRaisesRegex(DataError, "Unknown practice"):
            parse_practices('{"practices": {"P-99": "yes"}}')

    def test_circular_dependency(self):
        with self.assertRaisesRegex(DataError, "Circular"):
            run("A,high,8,24,image,24," + GOOD + ",2,true,B", "B,high,8,24,image,24," + GOOD + ",2,true,A")


class TestChecks(unittest.TestCase):
    def test_well_protected_system_has_no_findings(self):
        r = run("A,critical,8,24,image,24," + GOOD + ",4,true,")
        self.assertEqual(ids(r, "A"), set())
        self.assertEqual(r.systems[0].score, 100)

    def test_no_backup(self):
        r = run("A,high,8,24,none,,,,,,,,,")
        self.assertEqual(ids(r, "A"), {"RR-01"})
        self.assertIsNone(r.systems[0].effective_recovery_hours)
        self.assertEqual(r.counts()["miss_rto"], 1)

    def test_online_only_backup(self):
        r = run("A,high,8,24,image,24,false,true,true,true,2026-06-01,4,true,")
        self.assertIn("RR-02", ids(r, "A"))

    def test_rpo_and_untested_restore(self):
        r = run("A,high,8,4,image,24,true,true,true,true,,4,false,")
        self.assertTrue({"RR-03", "RR-05", "RR-06"} <= ids(r, "A"))

    def test_dependency_pushes_recovery_past_target(self):
        r = run("AD,critical,24,24,image,24," + GOOD + ",10,true,",
                "ERP,critical,16,24,image,24," + GOOD + ",8,true,AD")
        erp = next(s for s in r.systems if s.system == "ERP")
        self.assertEqual(erp.effective_recovery_hours, 18)
        self.assertEqual(erp.blocking_dependency, "AD")
        self.assertIn("RR-04", ids(r, "ERP"))
        self.assertIn("waiting for AD", erp.findings[0].detail)

    def test_dependency_without_backup_blocks_recovery(self):
        r = run("AD,critical,24,24,none,,,,,,,,,", "ERP,critical,16,24,image,24," + GOOD + ",8,true,AD")
        erp = next(s for s in r.systems if s.system == "ERP")
        self.assertIsNone(erp.effective_recovery_hours)
        self.assertIn("RR-04", ids(r, "ERP"))

    def test_saas_is_not_flagged_for_shared_credentials(self):
        r = run("M365,high,8,24,saas,24,true,true,,true,2026-06-01,4,true,")
        self.assertNotIn("RR-07", ids(r, "M365"))


class TestScoring(unittest.TestCase):
    def test_practices_change_readiness(self):
        row = "A,critical,8,24,image,24," + GOOD + ",4,true,"
        none = run(row)
        allp = run(row, practices={"practices": {f"P-{i:02d}": "yes" for i in range(1, 11)}})
        self.assertEqual(none.practice_score, 0)
        self.assertEqual(allp.practice_score, 100)
        self.assertEqual(allp.readiness, 100)
        self.assertGreater(allp.readiness, none.readiness)

    def test_samples(self):
        weak = assess(load_systems(S / "riverbend_components_systems.csv"),
                      load_practices(S / "riverbend_components_practices.json"), as_of=AS_OF)
        strong = assess(load_systems(S / "northfield_cold_logistics_systems.csv"),
                        load_practices(S / "northfield_cold_logistics_practices.json"), as_of=AS_OF)
        self.assertIn(weak.band, ("Vulnerable", "Highly vulnerable"))
        self.assertEqual(strong.band, "Resilient")
        self.assertEqual(strong.counts()["miss_rto"], 0)


class TestOutput(unittest.TestCase):
    def test_writers_gauge_and_escaping(self):
        r = assess(load_systems(S / "riverbend_components_systems.csv"), {"practices": {}}, "<script>x</script>", as_of=AS_OF)
        for fmt, w in WRITERS.items():
            self.assertTrue(w(r).strip(), fmt)
        self.assertNotIn("<script>x</script>", WRITERS["html"](r))
        json.loads(WRITERS["json"](r))
        self.assertIn("<svg", gauge_svg(42, "Vulnerable"))

    def test_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            weak = [str(S / "riverbend_components_systems.csv"), "--practices", str(S / "riverbend_components_practices.json")]
            strong = [str(S / "northfield_cold_logistics_systems.csv"), "--practices",
                      str(S / "northfield_cold_logistics_practices.json")]
            self.assertEqual(main(weak + ["--as-of", "2026-10-06", "--out", tmp, "--fail-below", "60"]), 2)
            self.assertEqual(main(strong + ["--as-of", "2026-10-06", "--out", tmp, "--fail-below", "60"]), 0)
            bad = Path(tmp) / "bad.csv"
            bad.write_text("x\n1\n", encoding="utf-8")
            self.assertEqual(main([str(bad), "--out", tmp]), 1)


if __name__ == "__main__":
    unittest.main()
