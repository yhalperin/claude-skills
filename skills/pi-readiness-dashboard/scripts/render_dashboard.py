#!/usr/bin/env python3
"""Render a pi-readiness-dashboard HTML file from a themes JSON snapshot.

Injects the themes array + HR tree into assets/template.html's placeholders
and writes a standalone HTML file. See ../DATA_SCHEMA.md for the expected
JSON shape of --themes.

Usage:
    python render_dashboard.py --themes themes.json --pi 27-Q1 --jql-file jql.txt [options]

Options:
    --themes PATH      Required. Path to the transformed themes JSON array (see DATA_SCHEMA.md).
    --pi TEXT          Required. Target PI label as it appears in Jira, e.g. "27-Q1".
    --jql-file PATH     Path to a text file containing the exact JQL used to fetch the data
                        (shown in the snapshot footer). PREFER THIS on Windows/PowerShell,
                        where passing a JQL string with embedded double quotes via --jql is
                        unreliable due to shell/CRT argument-quoting rules.
    --jql TEXT         Alternative to --jql-file. The exact JQL string (only safe on shells
                        that don't mangle embedded double quotes).
    --hrtree PATH       Path to the Division->Group JSON map. Defaults to the bundled
                        ../assets/hr_tree.json (canonical HR org chart snapshot).
    --timeline PATH     Path to a fiscal-year PI timeline export (see DATA_SCHEMA.md for the
                        expected shape). If supplied, the specific programIncrement matching
                        --pi is extracted and rendered as a phase timeline at the head of the
                        board (Pre-Planning/Planning/Execution/Retrospective, with today's phase
                        highlighted). Defaults to the bundled ../assets/pi_timeline.json if
                        present. If that default is missing, or --pi isn't found in the file,
                        the timeline section is simply hidden - never an error.
    --division TEXT    Division scope used for the fetch. "All" (default) or a specific
                        canonical division name (e.g. "Secrets Manager"). This is a label only;
                        the dashboard's Division dropdown always shows whatever divisions are
                        actually present in --themes.
    --base-url TEXT     Jira base URL, defaults to https://ca-il-jira.il.cyber-ark.com:8443
    --out PATH          Output HTML path. Defaults to a name derived from --pi/--division
                        next to the themes file.
    --no-open           Do not open the result in a browser.
"""
import argparse
import datetime
import json
import sys
import webbrowser
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATE_PATH = SCRIPT_DIR.parent / "assets" / "template.html"
DEFAULT_HRTREE_PATH = SCRIPT_DIR.parent / "assets" / "hr_tree.json"
DEFAULT_TIMELINE_PATH = SCRIPT_DIR.parent / "assets" / "pi_timeline.json"
DEFAULT_BASE_URL = "https://ca-il-jira.il.cyber-ark.com:8443"


def slugify(text: str) -> str:
    slug = "".join(c.lower() if c.isalnum() else "-" for c in text).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug or "dashboard"


def json_embed(value) -> str:
    """Dumps JSON safely for embedding inside a <script> tag."""
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def main() -> int:
    parser = argparse.ArgumentParser(description="Render the PI Readiness Command Center dashboard HTML.")
    parser.add_argument("--themes", required=True, help="Path to the transformed themes JSON array.")
    parser.add_argument("--pi", required=True, help='Target PI label, e.g. "27-Q1".')
    parser.add_argument("--jql", default=None, help="The exact JQL used to fetch the data.")
    parser.add_argument("--jql-file", default=None, help="Path to a text file containing the JQL (avoids shell quoting issues on Windows/PowerShell - prefer this over --jql).")
    parser.add_argument("--hrtree", default=str(DEFAULT_HRTREE_PATH), help="Path to Division->Group JSON map.")
    parser.add_argument("--timeline", default=str(DEFAULT_TIMELINE_PATH), help="Path to a fiscal-year PI timeline export JSON. Defaults to the bundled ../assets/pi_timeline.json.")
    parser.add_argument("--division", default="All", help='Division scope label: "All" or a specific division name.')
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Jira base URL.")
    parser.add_argument("--out", default=None, help="Output HTML path.")
    parser.add_argument("--no-open", action="store_true", help="Do not open the result in a browser.")
    args = parser.parse_args()

    if not args.jql and not args.jql_file:
        print("One of --jql or --jql-file is required.", file=sys.stderr)
        return 1
    jql = Path(args.jql_file).read_text(encoding="utf-8").strip() if args.jql_file else args.jql

    themes_path = Path(args.themes)
    hrtree_path = Path(args.hrtree)

    if not themes_path.exists():
        print(f"Themes file not found: {themes_path}", file=sys.stderr)
        return 1
    if not hrtree_path.exists():
        print(f"HR tree file not found: {hrtree_path}", file=sys.stderr)
        return 1
    if not TEMPLATE_PATH.exists():
        print(f"Template not found: {TEMPLATE_PATH}", file=sys.stderr)
        return 1

    try:
        themes = json.loads(themes_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"Invalid JSON in {themes_path}: {exc}", file=sys.stderr)
        return 1
    if not isinstance(themes, list) or not themes:
        print("Themes file must be a non-empty JSON array; aborting.", file=sys.stderr)
        return 1

    hr_tree = json.loads(hrtree_path.read_text(encoding="utf-8"))

    pi_timeline = None
    if args.timeline:
        timeline_path = Path(args.timeline)
        if not timeline_path.exists():
            print(f"Timeline file not found: {timeline_path} (continuing without a timeline)", file=sys.stderr)
        else:
            timeline_data = json.loads(timeline_path.read_text(encoding="utf-8"))
            for fy in timeline_data.get("fiscalYears", []):
                for pi in fy.get("programIncrements", []):
                    if pi.get("name") == args.pi:
                        pi_timeline = pi
                        break
                if pi_timeline:
                    break
            if not pi_timeline:
                print(f"Note: PI '{args.pi}' not found in {timeline_path.name}; timeline section will be hidden.", file=sys.stderr)

    known_statuses = {"Ready for Implementation", "Planned", "In Progress", "Open", "HL Product Discovery", "HL Dev Discovery"}
    unknown = sorted({t.get("status") for t in themes if t.get("status") not in known_statuses})
    if unknown:
        print(f"Note: {len(unknown)} status value(s) not in STATUS_META yet, will render with the neutral fallback color: {unknown}", file=sys.stderr)

    snapshot_ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    if args.division and args.division != "All":
        scope_badge_html = (
            '<span class="bg-slate-800 text-slate-300 border border-slate-700 text-xs px-2.5 py-1 '
            'rounded-full font-semibold uppercase tracking-wider">Division: '
            f'{args.division}</span>'
        )
        scope_note_html = f', scoped to the <strong class="text-slate-200">{args.division}</strong> division'
    else:
        scope_badge_html = ""
        scope_note_html = ""

    if args.out:
        out_path = Path(args.out)
    else:
        slug = f"pi_readiness_{slugify(args.pi)}_{slugify(args.division)}"
        out_path = themes_path.parent / f"{slug}.html"

    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    html = (
        template
        .replace("__TARGET_PI__", args.pi)
        .replace("__SNAPSHOT_TS__", snapshot_ts)
        .replace("__TOTAL_COUNT__", str(len(themes)))
        .replace("__JQL_JSON__", json.dumps(jql))
        .replace("__JIRA_BASE_URL__", args.base_url)
        .replace("__SCOPE_BADGE_HTML__", scope_badge_html)
        .replace("__SCOPE_NOTE_HTML__", scope_note_html)
        .replace("__HRTREE_JSON__", json_embed(hr_tree))
        .replace("__THEMES_JSON__", json_embed(themes))
        .replace("__PI_TIMELINE_JSON__", json_embed(pi_timeline))
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    print(f"Dashboard written to: {out_path}")
    print(f"Themes included: {len(themes)} | PI: {args.pi} | Division scope: {args.division}")
    print(f"PI Timeline: {'included (' + pi_timeline['start'] + ' to ' + pi_timeline['end'] + ')' if pi_timeline else 'not included'}")

    if not args.no_open:
        webbrowser.open(out_path.resolve().as_uri())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
