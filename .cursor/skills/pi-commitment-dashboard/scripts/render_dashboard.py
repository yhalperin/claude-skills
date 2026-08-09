"""
Render a pi-commitment-dashboard HTML file from a themes JSON snapshot.

Injects the themes array into assets/template.html placeholders and writes
a standalone HTML file. See ../DATA_SCHEMA.md for the expected JSON shape.

Usage:
    python render_dashboard.py --themes themes.json --pi 27-Q1 [options]

Options:
    --themes PATH      Required. Path to the transformed themes JSON array.
    --pi TEXT          Required. Target PI label, e.g. "27-Q1".
    --fetched-at TEXT  Actual Jira pull date/time, e.g. "2026-08-06 10:30".
                       Shown as "Jira Data as of" in header. Falls back to
                       --themes file-mtime (with warning) if omitted.
    --division TEXT    Division to open on load: "All" (default) or a name.
    --out PATH         Output HTML path. Defaults to timestamped file under
                       DEFAULT_OUTPUT_DIR.
    --no-open          Do not open the result in a browser.
"""

import argparse
import datetime
import json
import re
import sys
import webbrowser
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATE_PATH = SCRIPT_DIR.parent / "assets" / "template.html"
DEFAULT_OUTPUT_DIR = Path(r"C:\Users\yhalperin\Documents\PI_Commitment_Boards")


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def json_embed(value) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).replace(
        "</", "<\\/"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Render PI Commitment Dashboard HTML")
    parser.add_argument("--themes", required=True, help="Path to themes JSON array")
    parser.add_argument("--pi", required=True, help='Target PI label, e.g. "27-Q1"')
    parser.add_argument("--fetched-at", dest="fetched_at", default=None)
    parser.add_argument("--division-totals", dest="division_totals", default=None,
                        help="Path to JSON object mapping division name -> total theme count")
    parser.add_argument("--status-themes", dest="status_themes", default=None,
                        help="Path to JSON array of {id, divisions, status} for Planned/In Progress themes")
    parser.add_argument("--division", default="All")
    parser.add_argument("--out", default=None)
    parser.add_argument("--no-open", action="store_true")
    args = parser.parse_args()

    themes_path = Path(args.themes)
    if not themes_path.exists():
        print(f"ERROR: themes file not found: {themes_path}", file=sys.stderr)
        return 1
    if not TEMPLATE_PATH.exists():
        print(f"ERROR: template not found: {TEMPLATE_PATH}", file=sys.stderr)
        return 1

    try:
        themes = json.loads(themes_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"ERROR: invalid JSON in themes file: {exc}", file=sys.stderr)
        return 1
    if not isinstance(themes, list) or len(themes) == 0:
        print("ERROR: themes file must be a non-empty JSON array", file=sys.stderr)
        return 1

    status_themes = []
    if args.status_themes:
        st_path = Path(args.status_themes)
        if not st_path.exists():
            print(f"ERROR: status-themes file not found: {st_path}", file=sys.stderr)
            return 1
        try:
            status_themes = json.loads(st_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(f"ERROR: invalid JSON in status-themes file: {exc}", file=sys.stderr)
            return 1

    division_totals = {}
    if args.division_totals:
        dt_path = Path(args.division_totals)
        if not dt_path.exists():
            print(f"ERROR: division-totals file not found: {dt_path}", file=sys.stderr)
            return 1
        try:
            division_totals = json.loads(dt_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(f"ERROR: invalid JSON in division-totals file: {exc}", file=sys.stderr)
            return 1

    rendered_ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    if args.fetched_at:
        jira_fetch_ts = args.fetched_at
    else:
        mtime = datetime.datetime.fromtimestamp(themes_path.stat().st_mtime)
        jira_fetch_ts = mtime.strftime("%Y-%m-%d %H:%M")
        print(
            f"WARNING: --fetched-at not provided; using themes file mtime: {jira_fetch_ts}",
            file=sys.stderr,
        )

    template = TEMPLATE_PATH.read_text(encoding="utf-8")

    output = template
    output = output.replace("__THEMES_JSON__", json_embed(themes))
    output = output.replace("__DIVISION_TOTALS_JSON__", json_embed(division_totals))
    output = output.replace("__STATUS_THEMES_JSON__", json_embed(status_themes))
    output = output.replace("__TARGET_PI__", json_embed(args.pi))
    output = output.replace("__JIRA_FETCH_TS__", json_embed(jira_fetch_ts))
    output = output.replace("__SNAPSHOT_TS__", json_embed(rendered_ts))
    output = output.replace("__INITIAL_DIVISION__", json_embed(args.division))

    if args.out:
        out_path = Path(args.out)
    else:
        DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        ts_slug = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        pi_slug = slugify(args.pi)
        filename = f"pi_commitment_{pi_slug}_{ts_slug}.html"
        out_path = DEFAULT_OUTPUT_DIR / filename

    out_path.write_text(output, encoding="utf-8")
    print(f"Dashboard written to: {out_path}")

    if not args.no_open:
        webbrowser.open(out_path.as_uri())
        print("Opened in browser.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
