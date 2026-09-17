#!/usr/bin/env python3
"""Build a Pages artifact from HTML archives only, never from the source tree."""
import argparse
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code"))
import publish_site


def build(output, archive=None, reports=None):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    # Existing source archives seed the first run; the report branch retains
    # history thereafter. Fresh generated reports take precedence over both.
    for source in [ROOT, archive, reports]:
        if source is None:
            continue
        for _, filename in publish_site._scan(source):
            shutil.copy2(Path(source) / filename, output / filename)
    reports_in_site = publish_site._scan(output)
    (output / ".nojekyll").touch()
    (output / "index.html").write_text(publish_site._index_html(reports_in_site), encoding="utf-8")
    print(f"Built {len(reports_in_site)} reports in {output}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    parser.add_argument("--archive")
    parser.add_argument("--reports", default=str(ROOT / "code/reports"))
    args = parser.parse_args()
    build(args.out, args.archive, args.reports)


if __name__ == "__main__":
    main()
