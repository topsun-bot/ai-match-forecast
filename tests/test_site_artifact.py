from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_site


class SiteArtifact(unittest.TestCase):
    def test_only_report_html_is_published_and_history_is_kept(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source, history, reports = base / "source", base / "history", base / "reports"
            for folder in [source, history, reports]:
                folder.mkdir()
                (folder / "secret.py").write_text("must not publish")
                (folder / ".env").write_text("must not publish")
            (source / "日报-2026-09-15.html").write_text("old")
            (history / "日报-2026-09-16.html").write_text("archived")
            (reports / "日报-2026-09-17.html").write_text("new")
            (reports / "日报-2026-09-18.html").symlink_to(source / ".env")
            output = base / "site"
            with patch.object(build_site, "ROOT", source):
                build_site.build(output, history, reports)
            self.assertEqual(sorted(p.name for p in output.iterdir()),
                             [".nojekyll", "index.html", "日报-2026-09-15.html",
                              "日报-2026-09-16.html", "日报-2026-09-17.html"])
            index = (output / "index.html").read_text()
            self.assertLess(index.index("2026-09-17"), index.index("2026-09-16"))
            self.assertLess(index.index("2026-09-16"), index.index("2026-09-15"))

    def test_existing_output_is_not_silently_reused(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(FileExistsError):
                build_site.build(directory)


if __name__ == "__main__":
    unittest.main()
