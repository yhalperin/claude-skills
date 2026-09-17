# Metric Calculation Formulas (PowerShell)

## Setup: parse raw Jira pages into a `$themes` array

```powershell
# $pages = array of ConvertFrom-Json results from jira_search (Pass A or B)
$all = $pages | ForEach-Object { $_.issues } | Where-Object { $_ }

# Deduplicate by key (paginated results can overlap)
$seenKeys = @{}; $unique = @()
foreach ($i in $all) {
    if (-not $seenKeys.ContainsKey($i.key)) { $seenKeys[$i.key] = $true; $unique += $i }
}

$themes = foreach ($i in $unique) {
    $sw  = $i.fields.customfield_12258  # StartWork
    $fw  = $i.fields.customfield_12259  # FinishWork
    $pis = @($i.fields.customfield_14422 | ForEach-Object { $_.value }) | Where-Object { $_ }
    $grp = if ($i.fields.customfield_22720 -and $i.fields.customfield_22720.Count -gt 0) {
               $i.fields.customfield_22720[0].value   # Primary group (first entry)
           } else { "Unknown" }
    $ct  = $null
    if ($sw -and $fw) {
        $ct = ([datetime]$fw - [datetime]$sw).Days
        if ($ct -lt 0) { $ct = $null }   # exclude data errors
    }
    [PSCustomObject]@{
        Key       = $i.key
        StatusCat = $i.fields.status.statusCategory.name  # "Done" | "In Progress" | "To Do"
        Project   = $i.fields.project.key
        Group     = $grp
        PIs       = $pis -join ","
        PICount   = $pis.Count
        StartWork = if ($sw) { [datetime]$sw } else { $null }
        FinishWork= if ($fw) { [datetime]$fw } else { $null }
        CycleDays = $ct
        IsDone    = ($i.fields.status.statusCategory.name -eq "Done")
    }
}
```

---

## PI window definitions

Load from `C:\Users\yhalperin\source\pi-timeline-fy2027.json`.
Then apply user-confirmed overrides for fiscal year 2026:

```powershell
$piTimeline = Get-Content "C:\Users\yhalperin\source\pi-timeline-fy2027.json" -Raw | ConvertFrom-Json

# Build base windows from JSON (structure varies — read and adapt to actual JSON shape)
$piWindows = @{}
foreach ($pi in $piTimeline.PSObject.Properties) {
    $piWindows[$pi.Name] = @{
        Start = [datetime]$pi.Value.start
        End   = [datetime]$pi.Value.end
    }
}

# Override / add the known fiscal-2026 PIs with user-confirmed dates
$piWindows["26-Q1"] = @{ Start = [datetime]"2026-01-13"; End = [datetime]"2026-04-11" }
$piWindows["26-Q2"] = @{ Start = [datetime]"2026-04-12"; End = [datetime]"2026-08-01" }
# 27-Q1 and 27-Q2 come from the JSON file above
```

Throughput (c7) maps each Done theme's **FinishWork** date to a PI window — not the PlannedPI field value.

---

## Metric 1 & 2 — Velocity + Throughput Trend (FinishWork-date-based)

```powershell
function Get-PI($date, $windows) {
    foreach ($pi in $windows.Keys) {
        if ($date -ge $windows[$pi].Start -and $date -le $windows[$pi].End) {
            return $pi
        }
    }
    return $null
}

$throughput = foreach ($pi in ($piWindows.Keys | Sort-Object)) {
    $w   = $piWindows[$pi]
    $fin = ($themes | Where-Object {
        $_.IsDone -and $_.FinishWork -ne $null -and
        $_.FinishWork -ge $w.Start -and $_.FinishWork -le $w.End
    }).Count
    [PSCustomObject]@{ PI = $pi; Done = $fin }
}

# Velocity = avg across all measured PI windows
$avgVelocity = [math]::Round(($throughput.Done | Measure-Object -Average).Average, 0)

# Throughput trend pct: compare last completed PI to first
$ordered = $throughput | Sort-Object PI
$first   = $ordered[0].Done
$last    = $ordered[-1].Done
$trendPct = if ($first -gt 0) { [math]::Round(100 * ($last - $first) / $first) } else { 0 }
```

---

## Metric 3 — Avg Cycle Time

> P90 has been removed — only Avg and Median are reported.

```powershell
$withCycle   = $themes | Where-Object { $_.IsDone -and $_.CycleDays -ne $null }
$cycleSorted = $withCycle.CycleDays | Sort-Object
$avgCycle    = [math]::Round(($cycleSorted | Measure-Object -Average).Average, 0)
$medCycle    = $cycleSorted[[int]($cycleSorted.Count / 2)]
```

---

## Metric 4 — Carryover Rate

```powershell
$totalThemes   = $themes.Count
$multiPIThemes = ($themes | Where-Object { $_.PICount -gt 1 }).Count
$carryoverPct  = [math]::Round(100 * $multiPIThemes / $totalThemes)
```

---

## Metric 5 — Single-PI Success Rate

```powershell
$doneThemes      = $themes | Where-Object IsDone
$singlePIDone    = ($doneThemes | Where-Object { $_.PICount -eq 1 }).Count
$singlePISuccPct = [math]::Round(100 * $singlePIDone / $doneThemes.Count)
```

---

## Metric 6 — Theme Fit Rate

```powershell
$PI_DAYS    = 91
$fitCount   = ($withCycle | Where-Object { $_.CycleDays -le $PI_DAYS }).Count
$fitRatePct = [math]::Round(100 * $fitCount / $withCycle.Count)
```

---

## Per-group cycle stats + velocity recommendation

Groups come from `$themes.Group` (mapped from `customfield_22720`).

> **Do NOT use project.key for group breakdown** — always use the Groups field.

```powershell
$completedPIs = @("26-Q1","26-Q2")   # PIs fully elapsed; remove active ones

$groupStats = foreach ($grp in ($themes | Select-Object -ExpandProperty Group | Sort-Object -Unique)) {
    $grpThemes  = $themes | Where-Object { $_.Group -eq $grp }
    $grpWithCyc = $grpThemes | Where-Object { $_.IsDone -and $_.CycleDays -ne $null }
    $ds  = $grpWithCyc.CycleDays | Sort-Object
    $n   = $ds.Count
    $avg = if ($n -gt 0) { [math]::Round(($ds | Measure-Object -Average).Average, 0) } else { 0 }
    $med = if ($n -gt 0) { $ds[[int]($n / 2)] } else { 0 }

    # Historical throughput: avg done per completed PI (FinishWork-date-based)
    $hist = foreach ($pi in $completedPIs) {
        $w = $piWindows[$pi]
        ($grpThemes | Where-Object {
            $_.IsDone -and $_.FinishWork -ne $null -and
            $_.FinishWork -ge $w.Start -and $_.FinishWork -le $w.End
        }).Count
    }
    $histAvg = if ($hist.Count -gt 0) {
        [math]::Round(($hist | Measure-Object -Average).Average, 1)
    } else { 0 }

    [PSCustomObject]@{
        Group          = $grp
        N              = $n
        AvgCycle       = $avg
        MedCycle       = $med
        HistThroughput = $histAvg
        VelLow         = [math]::Floor($histAvg * 0.8)
        VelHigh        = [math]::Ceiling($histAvg * 1.2)
    }
}
```

---

## The 4-way delivery state split (for c3 and c5)

Use this for all "delivery pattern" charts — it is unambiguous:

| Category | Definition |
|----------|-----------|
| **Done — 1 PI** | Done AND PICount = 1 |
| **Done — Multi PI** | Done AND PICount > 1 |
| **In Progress** | StatusCat = "In Progress" (any PICount) |
| **Not Started** | StatusCat = "To Do" (any PICount) |

> **Never use "Single-PI In-Flight"** — it mixes themes planned for one PI but never finished,
> which is a data-hygiene signal, not a delivery state.

Chart label for c3: *"Themes per PI — Delivery State"*
Chart description: *"All themes whose primary PlannedPI is that quarter, split by current delivery state."*

```powershell
# Global breakdown
$done    = $themes | Where-Object { $_.IsDone }
$d1      = ($done | Where-Object { $_.PICount -eq 1 }).Count
$d2      = ($done | Where-Object { $_.PICount -eq 2 }).Count
$d3plus  = ($done | Where-Object { $_.PICount -ge 3 }).Count
$dTot    = $done.Count
$pct1    = [math]::Round(100 * $d1     / $dTot)
$pct2    = [math]::Round(100 * $d2     / $dTot)
$pct3    = [math]::Round(100 * $d3plus / $dTot)

# Per-PI breakdown (for c2 stacked bar chart)
$piList   = @("26-Q1","26-Q2","27-Q1","27-Q2")
$spanByPI = foreach ($pi in $piList) {
    $inPI = $done | Where-Object { ($_.PIs -split ",")[0].Trim() -eq $pi }
    [PSCustomObject]@{
        PI     = $pi
        One    = ($inPI | Where-Object { $_.PICount -eq 1 }).Count
        Two    = ($inPI | Where-Object { $_.PICount -eq 2 }).Count
        ThPlus = ($inPI | Where-Object { $_.PICount -ge 3 }).Count
    }
}

# Per-PI status (for c1 stacked bar chart)
$statusByPI = foreach ($pi in $piList) {
    $inPI = $themes | Where-Object { ($_.PIs -split ",") -contains $pi }
    [PSCustomObject]@{
        PI          = $pi
        Total       = $inPI.Count
        Done        = ($inPI | Where-Object { $_.IsDone }).Count
        InProgress  = ($inPI | Where-Object { $_.StatusCat -eq "In Progress" }).Count
        NotStarted  = ($inPI | Where-Object { $_.StatusCat -eq "To Do" }).Count
    }
}
```

> Note: "Completion Rate Trend" (line chart) has been removed — replaced by c2 (PI-span stacked bar).

---

## Theme Breakdown Quality (Epic count per Theme)

Pass C fetches all Epics whose `cf[11140]` (Parent Link) points to a Theme in the report.
Process results in PowerShell to count Epics per Theme key.

```powershell
# $epicPages = paginated jira_search results for Pass C
$allEpics = $epicPages | ForEach-Object { $_.issues } | Where-Object { $_ }

# Build a map: theme key → epic count
$epicCountByTheme = @{}
foreach ($epic in $allEpics) {
    $parentKey = $epic.fields.customfield_11140.key   # Parent Link → Theme key
    if ($parentKey) {
        $epicCountByTheme[$parentKey] = ($epicCountByTheme[$parentKey] ?? 0) + 1
    }
}

# Categorize each theme
$epicBreakdown = foreach ($t in $themes) {
    $count = $epicCountByTheme[$t.Key] ?? 0
    $cat   = switch ($count) {
        0       { "No Epics" }
        1       { "Monolithic" }
        { $_ -ge 2 -and $_ -le 7 } { "Healthy" }
        default { "Over-fragmented" }
    }
    [PSCustomObject]@{
        Key      = $t.Key
        Group    = $t.Group
        EpicCount= $count
        Category = $cat
    }
}

# Summary counts
$noEpics       = ($epicBreakdown | Where-Object { $_.Category -eq "No Epics" }).Count
$monolithic    = ($epicBreakdown | Where-Object { $_.Category -eq "Monolithic" }).Count
$healthy       = ($epicBreakdown | Where-Object { $_.Category -eq "Healthy" }).Count
$overFragmented= ($epicBreakdown | Where-Object { $_.Category -eq "Over-fragmented" }).Count
```

> Tip: Theme keys must be chunked when building the Pass C JQL IN list (max ~50 per query).
> Accumulate results from all pages before processing.

---

## PI Capacity vs. Recommended Velocity

Count themes assigned to each PI (primary PI = first value in PlannedPI array), per group.
Compare assigned count against the group's `VelLow`–`VelHigh` range.

```powershell
$capacityMatrix = foreach ($grp in ($groupStats.Group)) {
    $gStat    = $groupStats | Where-Object { $_.Group -eq $grp }
    $velLow   = $gStat.VelLow
    $velHigh  = $gStat.VelHigh
    $row = [PSCustomObject]@{ Group = $grp; VelRange = "$velLow–$velHigh" }
    foreach ($pi in $piList) {
        $assigned = ($themes | Where-Object {
            $_.Group -eq $grp -and ($_.PIs -split ",")[0].Trim() -eq $pi
        }).Count
        $status   = if ($assigned -gt $velHigh)    { "overload" }
                    elseif ($assigned -lt $velLow)  { "underload" }
                    else                            { "on-target" }
        $row | Add-Member -NotePropertyName "${pi}_count"  -NotePropertyValue $assigned
        $row | Add-Member -NotePropertyName "${pi}_status" -NotePropertyValue $status
    }
    $row
}
```

Color coding for HTML cells: overload = `#fee2e2` (red-tinted), on-target = `#dcfce7` (green), underload = `#fef9c3` (yellow).
