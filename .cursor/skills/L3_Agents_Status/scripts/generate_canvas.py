"""
L3-Agents Status Canvas Generator
Usage: python generate_canvas.py --data <path-to-data.json> [--output <path.canvas.tsx>]

Produces a Cursor Canvas (.canvas.tsx) that mirrors the PPTX table view.
Reads the same JSON file as generate_pptx.py so both can run in parallel.
"""

import argparse
import json
import os
import sys
from datetime import date, datetime

DEFAULT_CANVAS = (
    r"C:\Users\yhalperin\.cursor\projects"
    r"\c-Users-yhalperin-source\canvases\l3-agents-status.canvas.tsx"
)


def _fmt_eta(finish_date: str | None) -> str:
    if not finish_date:
        return "—"
    try:
        d = datetime.strptime(finish_date, "%Y-%m-%d").date()
        # strftime("%b %d") gives "Oct 05"; strip the leading zero manually
        return d.strftime("%b ") + str(d.day)
    except Exception:
        return str(finish_date)[:10]


def _fmt_tis(days: int | None) -> str:
    if days is None:
        return ""
    if days == 0:
        return "today"
    if days < 7:
        return f"{days}d"
    weeks, rem = divmod(days, 7)
    return f"{weeks}w {rem}d" if rem else f"{weeks}w"


def main():
    parser = argparse.ArgumentParser(description="Generate L3-Agents Cursor Canvas")
    parser.add_argument("--data",   required=True, help="Path to JSON data file")
    parser.add_argument("--output", default=DEFAULT_CANVAS, help="Destination .canvas.tsx")
    args = parser.parse_args()

    with open(args.data, "r", encoding="utf-8") as f:
        data = json.load(f)

    rows   = data["rows"]
    today  = date.today().strftime("%Y-%m-%d")

    canvas_rows = []
    for r in rows:
        theme_parts = r["theme"].split("\n")
        canvas_rows.append({
            "agent":         r["agent"].replace("\n", " "),
            "themeMain":     theme_parts[0],
            "themeId":       theme_parts[1] if len(theme_parts) > 1 else "",
            "businessValue": r["business_value"],
            "impact":        r["impact"],
            "status":        r["status"],
            "timeInStatus":  _fmt_tis(r.get("time_in_status_days")),
            "pi":            r.get("pi", "—"),
            "eta":           _fmt_eta(r.get("finish_date")),
            "health":        r.get("health", "On Track"),
            "tone": {
                "On Track":  "success",
                "At Risk":   "warning",
                "Off Track": "danger",
            }.get(r.get("health", "On Track"), "neutral"),
        })

    rows_json = json.dumps(canvas_rows, ensure_ascii=False, indent=2)

    n_on    = sum(1 for r in rows if r.get("health") == "On Track")
    n_risk  = sum(1 for r in rows if r.get("health") == "At Risk")
    n_off   = sum(1 for r in rows if r.get("health") == "Off Track")

    tsx = CANVAS_TEMPLATE.replace("__DATE__", today).replace("__ROWS_JSON__", rows_json)

    out = os.path.abspath(args.output)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(tsx)

    print(out)
    print(
        f"Canvas: {len(rows)} rows  "
        f"On Track {n_on} / At Risk {n_risk} / Off Track {n_off}",
        file=sys.stderr,
    )


# ── Canvas TSX template ────────────────────────────────────────────────────────
# Uses __DATE__ and __ROWS_JSON__ as placeholders replaced at render time.
# Keep braces intact — this is NOT an f-string.

CANVAS_TEMPLATE = """\
import {
  H1, Stack, Row, Grid, Stat, Table, Text, Divider, Callout,
} from "cursor/canvas";
import { useHostTheme } from "cursor/canvas";
import type { TableRowTone } from "cursor/canvas";

// ── Embedded data (auto-generated __DATE__) ────────────────────────────────────

const GENERATED_DATE = "__DATE__";

interface RowData {
  agent:         string;
  themeMain:     string;
  themeId:       string;
  businessValue: string;
  impact:        string;
  status:        string;
  timeInStatus:  string;
  pi:            string;
  eta:           string;
  health:        string;
  tone:          string;
}

const ROWS: RowData[] = __ROWS_JSON__;

// ── Status badge ───────────────────────────────────────────────────────────────

function StatusBadge({ status }: { status: string }) {
  const theme = useHostTheme();
  const color =
    status === "In Progress"           ? theme.category.blue
    : status === "HL Dev Discovery"    ? theme.category.gray
    : status === "HL Product Discovery"? theme.category.gray
    : status === "Planned"             ? theme.category.green
    : status === "Done"                ? theme.category.gray
    :                                   theme.category.gray;
  return (
    <Text size="small" weight="semibold" style={{ color }}>
      {status}
    </Text>
  );
}

// ── Health badge ───────────────────────────────────────────────────────────────

function HealthBadge({ health }: { health: string }) {
  const theme = useHostTheme();
  const color =
    health === "On Track"  ? theme.category.green
    : health === "At Risk" ? theme.category.yellow
    :                        theme.category.red;
  return (
    <Text size="small" weight="semibold" style={{ color }}>
      {health}
    </Text>
  );
}

// ── Canvas ─────────────────────────────────────────────────────────────────────

export default function L3AgentsStatus() {
  const onTrack  = ROWS.filter(r => r.health === "On Track").length;
  const atRisk   = ROWS.filter(r => r.health === "At Risk").length;
  const offTrack = ROWS.filter(r => r.health === "Off Track").length;

  const offTrackNames = ROWS
    .filter(r => r.health === "Off Track")
    .map(r => r.themeMain)
    .join(", ");

  const tableHeaders = [
    "Agent (Master Feature)",
    "Theme",
    "Business Value",
    "Impact",
    "Status",
    "Time in Status",
    "ETA",
    "Health",
  ];

  const tableRows = ROWS.map((r: RowData) => [
    <Text size="small" tone="secondary">{r.agent}</Text>,
    <Stack gap={2}>
      <Text size="small" weight="semibold">{r.themeMain}</Text>
      <Text size="small" tone="tertiary">{r.themeId}</Text>
    </Stack>,
    <Text size="small">{r.businessValue}</Text>,
    <Text size="small" tone="secondary">{r.impact}</Text>,
    <StatusBadge status={r.status} />,
    <Text size="small" tone="tertiary">{r.timeInStatus || "—"}</Text>,
    <Text size="small">{r.eta}</Text>,
    <HealthBadge health={r.health} />,
  ]);

  const rowTones = ROWS.map((r: RowData): TableRowTone | undefined =>
    r.tone === "success" ? "success"
    : r.tone === "warning" ? "warning"
    : r.tone === "danger"  ? "danger"
    : undefined
  );

  return (
    <Stack gap={24} style={{ padding: 24 }}>

      <Stack gap={4}>
        <H1>L3 Agents Progress</H1>
        <Text tone="secondary" size="small">
          Project IAI · label: L3-Agents · {GENERATED_DATE} · {ROWS.length} themes
        </Text>
      </Stack>

      <Grid columns={3} gap={12}>
        <Stat value={String(onTrack)}  label="On Track"  tone="success" />
        <Stat value={String(atRisk)}   label="At Risk"   tone="warning" />
        <Stat value={String(offTrack)} label="Off Track" tone={offTrack > 0 ? "danger" : undefined} />
      </Grid>

      {offTrack > 0 && (
        <Callout tone="danger" title="Themes off track">
          {offTrackNames}
        </Callout>
      )}

      <Divider />

      <Table
        headers={tableHeaders}
        rows={tableRows}
        rowTone={rowTones}
        striped
        stickyHeader
        framed
      />

    </Stack>
  );
}
"""

if __name__ == "__main__":
    main()
