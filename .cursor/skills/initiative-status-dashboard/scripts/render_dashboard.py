#!/usr/bin/env python3
"""Render an initiative-status-dashboard HTML file from a JSON data file.

Injects the JSON at assets/template.html's __INITIATIVE_DATA_JSON__ placeholder
and writes a standalone HTML file. See ../DATA_SCHEMA.md for the expected
JSON shape.

Unlike a timestamped-output pattern, this defaults to a STABLE output filename
(derived from the initiative keys, no timestamp) so that regenerating the same
dashboard reuses the same path/bookmark across status updates.

Usage:
    python render_dashboard.py --data initiative_data.json [--out output.html] [--no-open]
"""
import argparse
import json
import sys
import webbrowser
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATE_PATH = SCRIPT_DIR.parent / "assets" / "template.html"
PLACEHOLDER = "__INITIATIVE_DATA_JSON__"


def slugify(text: str) -> str:
    slug = "".join(c.lower() if c.isalnum() else "-" for c in text).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug or "initiative"


def main() -> int:
    parser = argparse.ArgumentParser(description="Render the initiative status dashboard HTML.")
    parser.add_argument("--data", required=True, help="Path to the initiative data JSON file.")
    parser.add_argument("--out", default=None, help="Output HTML path. Defaults to a stable filename next to the data file, derived from the initiative keys.")
    parser.add_argument("--no-open", action="store_true", help="Do not open the result in a browser.")
    args = parser.parse_args()

    data_path = Path(args.data)
    if not data_path.exists():
        print(f"Data file not found: {data_path}", file=sys.stderr)
        return 1

    if not TEMPLATE_PATH.exists():
        print(f"Template not found: {TEMPLATE_PATH}", file=sys.stderr)
        return 1

    try:
        data = json.loads(data_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"Invalid JSON in {data_path}: {exc}", file=sys.stderr)
        return 1

    initiatives = data.get("initiatives") or {}
    if not initiatives:
        print("Data file has no entries under 'initiatives'; aborting.", file=sys.stderr)
        return 1

    if args.out:
        out_path = Path(args.out)
    else:
        slug = "_".join(slugify(k) for k in initiatives.keys())
        out_path = data_path.parent / f"dashboard_{slug}.html"

    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    if PLACEHOLDER not in template:
        print("Template is missing the data placeholder; aborting.", file=sys.stderr)
        return 1

    # Escape "</" so the embedded JSON can't prematurely close the <script> tag.
    json_text = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    html = template.replace(PLACEHOLDER, json_text)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    print(f"Dashboard written to: {out_path}")
    print(f"Initiatives included: {', '.join(initiatives.keys())}")

    if not args.no_open:
        webbrowser.open(out_path.resolve().as_uri())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
