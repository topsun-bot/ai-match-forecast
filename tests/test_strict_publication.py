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
    def valid_response(self):
        return "【赛事】测试杯\n【主队】甲队\n【客队】乙队\n【比分】2 - 1\n【胜负】主队胜\n【置信】68\n【推理】\n- 依据测试数据分析\n【球评】\n- 测试媒体：测试观点"

    def live_router(self, text, citations=None):
        return SimpleNamespace(mock=False, chat_with_search=Mock(return_value={
            "text": text, "citations": [{"uri": "https://example.com/source"}] if citations is None else citations}))

    def test_complete_live_response_is_accepted(self):
        results, citations = analyst.analyze_daily("2026-09-17", self.live_router(self.valid_response()), strict=True)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["analysis"]["prediction"]["home"], 2)
        self.assertEqual(len(citations), 1)

    def test_nonempty_truncated_response_is_rejected(self):
        for text in ["【主队】甲队\n【客队】乙队", self.valid_response().replace("【推理】\n- 依据测试数据分析", "")]:
            with self.subTest(text=text), self.assertRaisesRegex(RuntimeError, "禁止回退样例"):
                analyst.analyze_daily("2026-09-17", self.live_router(text), strict=True)

    def test_invalid_score_confidence_and_result_are_rejected(self):
        for old, new in [("2 - 1", "未知"), ("【置信】68", "【置信】168"), ("主队胜", "客队胜")]:
            with self.subTest(new=new), self.assertRaises(RuntimeError):
                analyst.analyze_daily("2026-09-17", self.live_router(self.valid_response().replace(old, new)), strict=True)

    def test_one_good_match_cannot_hide_a_truncated_match(self):
        text = self.valid_response() + "\n===\n【主队】丙队\n【客队】丁队"
        with self.assertRaises(RuntimeError):
            analyst.analyze_daily("2026-09-17", self.live_router(text), strict=True)

    def test_live_prediction_requires_traceable_source(self):
        for citations in [[], [{"uri": "javascript:alert(1)"}]]:
            with self.subTest(citations=citations), self.assertRaises(RuntimeError):
                analyst.analyze_daily("2026-09-17", self.live_router(self.valid_response(), citations), strict=True)

    def test_mixed_rest_day_and_match_is_rejected(self):
        with self.assertRaises(RuntimeError):
            analyst.analyze_daily("2026-09-17", self.live_router("今日休赛\n" + self.valid_response()), strict=True)

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
