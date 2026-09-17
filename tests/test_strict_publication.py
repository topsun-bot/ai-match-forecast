import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code"))
import analyst
from llm_router import LLMRouter


class StrictPublication(unittest.TestCase):
    def test_provider_error_never_uses_sample_matches(self):
        router = SimpleNamespace(mock=False)
        with patch.object(analyst, "_grounding_analyze_daily", side_effect=RuntimeError("provider failed")), \
                patch.object(analyst, "get_matches") as samples:
            with self.assertRaisesRegex(RuntimeError, "禁止回退样例"):
                analyst.analyze_daily("2026-09-17", router, strict=True)
        samples.assert_not_called()

    def test_strict_mode_rejects_mock(self):
        with self.assertRaises(ValueError):
            analyst.analyze_daily("2026-09-17", LLMRouter(mock=True), strict=True)
        with self.assertRaises(ValueError):
            analyst.analyze_daily("2026-09-17", SimpleNamespace(mock=False), mock_data=True, strict=True)

    def test_rest_day_returns_no_report_not_samples(self):
        router = SimpleNamespace(mock=False, chat_with_search=Mock(return_value={"text": "今日休赛\n", "citations": []}))
        with patch.object(analyst, "get_matches") as samples:
            self.assertEqual(analyst.analyze_daily("2026-09-17", router, strict=True), ([], []))
        samples.assert_not_called()

    def test_malformed_live_response_stops_publication(self):
        router = SimpleNamespace(mock=False, chat_with_search=Mock(return_value={"text": "unable to obtain schedule", "citations": []}))
        with self.assertRaisesRegex(RuntimeError, "禁止回退样例"):
            analyst.analyze_daily("2026-09-17", router, strict=True)

    def test_cli_cannot_publish_mock_in_strict_mode(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "reports"
            env = {**os.environ, "LLM_MOCK": "1"}
            result = subprocess.run([
                sys.executable, str(ROOT / "code/generate_report.py"),
                "--no-mock-data", "--strict-live", "--no-open", "--out", str(out)],
                env=env, capture_output=True, text=True, timeout=10)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("--strict-live", result.stderr)
            self.assertFalse(out.exists())


if __name__ == "__main__":
    unittest.main()
