"""Offline contracts for parsing, rendering, routing and publication."""
import copy
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code"))
import analyst
import data_provider
import llm_router
import publish_site
import render


class ReportContracts(unittest.TestCase):
    def setUp(self):
        self.network = patch("urllib.request.urlopen", side_effect=AssertionError("offline test attempted network"))
        self.network.start()
        self.addCleanup(self.network.stop)

    def test_mock_router_ignores_present_credentials(self):
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-only-not-a-credential"}):
            router = llm_router.LLMRouter("gemini-2.5-pro", mock=True)
            results, citations = analyst.analyze_daily("2026-09-17", router, mock_data=True)
        self.assertGreater(len(results), 0)
        self.assertEqual(citations, [])
        for result in results:
            self.assertIn("prediction", result["analysis"])

    def test_unknown_model_is_rejected(self):
        with self.assertRaises(ValueError):
            llm_router.LLMRouter("not-a-model", mock=True)

    def test_mock_match_selection_is_exact(self):
        matches = data_provider.get_matches(mock=True)
        selected = data_provider.get_matches(mock=True, match_id=matches[0]["id"])
        self.assertEqual([m["id"] for m in selected], [matches[0]["id"]])
        self.assertEqual(data_provider.get_matches(mock=True, match_id="missing"), [])

    def test_parse_provider_output(self):
        text = "【赛事】测试杯\n【主队】甲队\n【客队】乙队\n【比分】2 - 1\n【置信】68\n【推理】\n- 第一条\n- 第二条\n【球评】\n- 媒体：观点"
        result = analyst._parse_daily(text, "2026-09-17")[0]
        self.assertEqual(result["match"]["date"], "2026-09-17")
        self.assertEqual(result["analysis"]["prediction"]["home"], 2)
        self.assertEqual(result["analysis"]["prediction"]["away"], 1)
        self.assertEqual(result["analysis"]["prediction"]["confidence"], .68)
        self.assertEqual(result["analysis"]["reasoning"]["chain"], ["第一条", "第二条"])

    def test_rest_day_and_malformed_blocks_are_not_matches(self):
        for text in ["", "今日休赛", "【赛事】缺少双方队名", "not structured"]:
            with self.subTest(text=text):
                self.assertEqual(analyst._parse_daily(text, "2026-09-17"), [])

    def test_render_escapes_untrusted_fields(self):
        match = copy.deepcopy(data_provider.get_matches(mock=True)[0])
        analysis = analyst._mock_analyze(match)
        attack = '<script>alert("test")</script>'
        match["home"]["name"] = attack
        analysis["prediction"]["home"] = attack
        analysis["reasoning"]["data_insight"] = attack
        output = render.render_report(attack, attack, attack, "mock", 1,
                                      [{"match": match, "analysis": analysis}])
        self.assertNotIn(attack, output)
        self.assertIn("&lt;script&gt;", output)
        for marker in ["{{DATE}}", "{{MATCHES}}", "{{CITATIONS}}"]:
            self.assertNotIn(marker, output)

    def test_citations_only_allow_http_sources(self):
        citations = [{"uri": uri, "title": '<b>source</b>'} for uri in
                     ["javascript:alert(1)", "data:text/html,test", "file:///tmp/test",
                      "//example.com", "https:///missing-host", "https://example.com/source"]]
        output = render._render_citations(citations)
        self.assertIn('href="https://example.com/source"', output)
        self.assertIn("&lt;b&gt;source&lt;/b&gt;", output)
        self.assertEqual(output.count("<li>"), 1)

    def test_invalid_urls_do_not_crash_renderer(self):
        self.assertEqual(render._render_citations([{"uri": "https://[invalid"}, {"uri": None}]), "")


class PublicationIntegration(unittest.TestCase):
    def test_offline_cli_to_site_preserves_archive(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            reports, site = base / "reports", base / "site"
            site.mkdir()
            (site / "日报-2026-09-16.html").write_text("previous report", encoding="utf-8")
            env = os.environ.copy()
            env["LLM_MOCK"] = "1"
            run = subprocess.run([
                sys.executable, str(ROOT / "code/generate_report.py"),
                "--mock-data", "--mock-llm", "--no-open", "--date", "2026-09-17",
                "--out", str(reports)], env=env, capture_output=True, text=True, timeout=20)
            self.assertEqual(run.returncode, 0, run.stderr)
            generated = reports / "日报-2026-09-17.html"
            self.assertTrue(generated.is_file())
            self.assertIn("mock", run.stdout)
            for ignored in [".env", "source.py", "日报-2026-99-99.html", '日报-2026-09-17-bad.html']:
                (reports / ignored).write_text("not a publishable report", encoding="utf-8")
            publish = subprocess.run([
                sys.executable, str(ROOT / "code/publish_site.py"),
                "--reports-dir", str(reports), "--site-dir", str(site)],
                capture_output=True, text=True, timeout=20)
            self.assertEqual(publish.returncode, 0, publish.stderr)
            self.assertEqual(sorted(p.name for p in site.iterdir()),
                             [".nojekyll", "index.html", "日报-2026-09-16.html", "日报-2026-09-17.html"])
            index = (site / "index.html").read_text()
            self.assertLess(index.index("2026-09-17"), index.index("2026-09-16"))
            self.assertEqual((site / "日报-2026-09-16.html").read_text(), "previous report")
            self.assertEqual((site / generated.name).read_text(), generated.read_text())

    def test_missing_reports_directory_is_supported(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(publish_site._scan(Path(directory) / "missing"), [])


if __name__ == "__main__":
    unittest.main()
