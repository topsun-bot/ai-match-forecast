import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from check_ci_gate import failures


class RequiredChecks(unittest.TestCase):
    def results(self):
        return {name: {"result": "success"} for name in ("lint", "tests", "dependency_review")}

    def test_successful_pr(self):
        self.assertEqual(failures("pull_request", self.results()), [])

    def test_every_non_success_state_blocks_required_pr_jobs(self):
        for name in self.results():
            for result in ["failure", "skipped", "cancelled", "neutral", "pending", None]:
                with self.subTest(name=name, result=result):
                    values = self.results()
                    values[name]["result"] = result
                    self.assertTrue(failures("pull_request", values))

    def test_missing_required_evidence_blocks(self):
        for name in self.results():
            values = self.results()
            del values[name]
            self.assertTrue(failures("pull_request", values))

    def test_non_pr_only_dependency_diff_can_be_not_applicable(self):
        values = self.results()
        values["dependency_review"]["result"] = "skipped"
        self.assertEqual(failures("push", values), [])
        self.assertEqual(failures("workflow_dispatch", values), [])
        values["tests"]["result"] = "skipped"
        self.assertTrue(failures("push", values))

    def test_unknown_event_does_not_reduce_requirements(self):
        self.assertTrue(failures("unknown", self.results()))

    def test_command_exits_nonzero_on_failed_or_invalid_evidence(self):
        for payload in ["not json", "[]", json.dumps({"tests": {"result": "failure"}})]:
            with self.subTest(payload=payload):
                env = {**os.environ, "GITHUB_EVENT_NAME": "pull_request", "NEEDS_JSON": payload}
                result = subprocess.run([sys.executable, str(ROOT / "scripts/check_ci_gate.py")],
                                        env=env, capture_output=True, timeout=10)
                self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
