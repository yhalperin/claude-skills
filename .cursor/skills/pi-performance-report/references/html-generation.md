# HTML Generation Guide

## CSS classes reference

| Class | Purpose |
|-------|---------|
| `.scorecard` | 3-column grid for the 6 health indicator cards |
| `.sc-card` | Individual card with colored left border |
| `.sc-green` / `.sc-amber` / `.sc-red` | Card status colors |
| `.sc-title` | Small uppercase metric name |
| `.sc-value` | Large bold number |
| `.sc-tag` | Colored pill: "On Track", "Monitor", "Action Needed" |
| `.sc-signal` | Trend line ("↑ Improving · 8 → 24 → 29") |
| `.sc-desc` | Descriptive sentence |
| `.kpi-grid` | 6-column grid for global summary KPIs |
| `.kpi` | Individual KPI box |
| `.kpi-value` / `.kpi-label` | Number and label inside KPI box |
| `.kpi-row` | Flex row for cycle-time section KPIs |
| `.kpi-num` / `.kpi-lbl` | Number and label inside `.kpi-row` item |
| `.chart-grid` | 2-column grid for side-by-side charts |
| `.badge` | Inline pill for velocity recommendations (white text) |

## Full CSS block

```css
*, *::before, *::after { box-sizing:border-box; margin:0; padding:0; }
body { font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;
       font-size:13px; color:#111; background:#fff; padding:32px 40px 48px;
       max-width:980px; margin:0 auto; }
h1 { font-size:22px; font-weight:700; color:#0a0a0a; margin-bottom:4px; }
h2 { font-size:15px; font-weight:600; color:#111; margin:32px 0 10px;
     border-bottom:1px solid #e0e0e0; padding-bottom:6px; }
h3 { font-size:12px; font-weight:600; color:#333; margin:0 0 6px;
     text-transform:uppercase; letter-spacing:.4px; }
p, .meta { font-size:12px; color:#666; line-height:1.6; margin-bottom:6px; }
hr { border:none; border-top:1px solid #ebebeb; margin:28px 0; }

/* Global KPIs */
.kpi-grid { display:grid; grid-template-columns:repeat(6,1fr); gap:12px; margin:16px 0 6px; }
.kpi { background:#f7f7f7; border:1px solid #e8e8e8; border-radius:6px;
       padding:12px 10px; text-align:center; }
.kpi-value { font-size:26px; font-weight:700; line-height:1.1; display:block; margin-bottom:3px; }
.kpi-label { font-size:11px; color:#666; }
.kpi.green .kpi-value { color:#1a7a3a; }
.kpi.blue  .kpi-value { color:#1558b0; }
.kpi.orange .kpi-value { color:#b05800; }

/* Charts */
.chart-grid { display:grid; grid-template-columns:1fr 1fr; gap:20px; margin:14px 0 20px; }
.chart-full { margin:14px 0 20px; }

/* Tables */
table { width:100%; border-collapse:collapse; font-size:12px; margin-bottom:6px; }
thead th { background:#f2f2f2; color:#333; font-weight:600; text-align:left;
           padding:7px 10px; border-bottom:1px solid #d4d4d4;
           border-top:1px solid #d4d4d4; white-space:nowrap; }
tbody tr:nth-child(even) { background:#fafafa; }
tbody tr.total-row { background:#efefef; font-weight:600; }
tbody td { padding:6px 10px; border-bottom:1px solid #ebebeb; color:#222; vertical-align:top; }
tbody td.ok   { color:#1a7a3a; }
tbody td.warn { color:#b05800; font-weight:600; }

/* Callout */
.callout { background:#fff8ed; border-left:3px solid #e07a20;
           padding:10px 14px; border-radius:0 4px 4px 0;
           margin:10px 0 14px; font-size:12px; color:#5a3800; }

/* Badges + KPI row (cycle-time section) */
.badge { display:inline-block; padding:3px 9px; border-radius:12px;
         color:#fff; font-size:11px; font-weight:600; white-space:nowrap; }
.kpi-row { display:flex; gap:12px; flex-wrap:wrap; }
.kpi-row .kpi { flex:1; min-width:110px; }
.kpi-num { font-size:26px; font-weight:700; line-height:1.1; display:block; margin-bottom:3px; }
.kpi-lbl { font-size:11px; color:#666; }

/* Scorecard */
.scorecard { display:grid; grid-template-columns:repeat(3,1fr); gap:12px; margin:16px 0 24px; }
.sc-card { border:1px solid #e0e0e0; border-radius:8px; padding:14px 16px 12px;
           position:relative; background:#fff; overflow:hidden; }
.sc-card::before { content:''; position:absolute; top:0; left:0; bottom:0;
                   width:5px; border-radius:8px 0 0 8px; }
.sc-green::before { background:#2d9e5a; }
.sc-amber::before { background:#e07a20; }
.sc-red::before   { background:#c0392b; }
.sc-title  { font-size:10px; font-weight:700; text-transform:uppercase;
             letter-spacing:.5px; color:#888; margin-bottom:6px; }
.sc-value  { font-size:30px; font-weight:800; line-height:1; margin-bottom:5px; }
.sc-green .sc-value { color:#1a7a3a; }
.sc-amber .sc-value { color:#a05500; }
.sc-red   .sc-value { color:#a02020; }
.sc-tag    { display:inline-block; font-size:9px; font-weight:700; text-transform:uppercase;
             letter-spacing:.4px; padding:2px 7px; border-radius:10px; margin-bottom:7px; }
.sc-green .sc-tag { background:#e6f6ed; color:#1a7a3a; }
.sc-amber .sc-tag { background:#fff2e0; color:#a05500; }
.sc-red   .sc-tag { background:#fde8e8; color:#a02020; }
.sc-signal { font-size:11px; font-weight:600; margin-bottom:6px; display:block; }
.sc-green .sc-signal { color:#1a7a3a; }
.sc-amber .sc-signal { color:#a05500; }
.sc-red   .sc-signal { color:#a02020; }
.sc-desc   { font-size:11px; color:#666; line-height:1.5; }

@media print {
  body { padding:16px 20px; }
  .scorecard, .chart-grid { page-break-inside:avoid; }
}
```

---

## JavaScript chart rendering (place in a single `<script>` at end of `<body>`)

```javascript
(function () {
  var NS = 'http://www.w3.org/2000/svg';

  function el(tag, attrs) {
    var e = document.createElementNS(NS, tag);
    for (var k in attrs) e.setAttribute(k, attrs[k]);
    return e;
  }
  function txt(tag, attrs, content) {
    var e = el(tag, attrs);
    e.textContent = String(content);
    return e;
  }
  function r(n) { return parseFloat(n.toFixed(1)); }

  // ── stackedBar ────────────────────────────────────────────────────────────
  // series: [{n:label, c:color, v:[values]}] — bottom-to-top stacking order
  function stackedBar(id, cats, series, opts) {
    opts = opts || {};
    var container = document.getElementById(id);
    if (!container) return;
    var W = opts.W || 460, H = 218, mL = 38, mR = 10, mT = 18, mB = 44;
    var pw = W - mL - mR, ph = H - mT - mB, n = cats.length;
    var totals = cats.map(function(_, i) {
      return series.reduce(function(s, ser) { return s + ser.v[i]; }, 0);
    });
    var maxV = opts.maxV || (Math.ceil(Math.max.apply(null, totals) * 1.2 / 5) * 5);
    var bw = Math.min(58, r(pw / n * 0.5)), step = pw / n;
    var svg = el('svg', { viewBox:'0 0 '+W+' '+H, style:'width:100%;height:auto;display:block' });
    for (var i = 0; i <= 5; i++) {
      var v = Math.round(maxV * i / 5), gy = r(mT + ph - ph * i / 5);
      svg.appendChild(el('line', { x1:mL, y1:gy, x2:mL+pw, y2:gy, stroke:'#e8e8e8', 'stroke-width':'1' }));
      svg.appendChild(txt('text', { x:mL-5, y:gy+4, 'text-anchor':'end', 'font-size':'10', 'font-family':'sans-serif', fill:'#aaa' }, v));
    }
    svg.appendChild(el('line', { x1:mL, y1:mT+ph, x2:mL+pw, y2:mT+ph, stroke:'#ddd', 'stroke-width':'1' }));
    for (var i = 0; i < n; i++) {
      var cx = r(mL + i * step + step / 2), bx = r(cx - bw / 2), curY = mT + ph;
      for (var j = 0; j < series.length; j++) {
        var val = series[j].v[i], bh = r((val / maxV) * ph);
        curY = r(curY - bh);
        if (bh > 0.5) {
          svg.appendChild(el('rect', { x:bx, y:curY, width:bw, height:r(bh), fill:series[j].c, rx:'1' }));
          if (bh >= 13 && val > 0)
            svg.appendChild(txt('text', { x:cx, y:r(curY+bh/2+3.5), 'text-anchor':'middle', 'font-size':'9', 'font-family':'sans-serif', fill:'rgba(255,255,255,0.9)', 'font-weight':'bold' }, val));
        }
      }
      var topY = r(mT + ph - (totals[i] / maxV) * ph);
      svg.appendChild(txt('text', { x:cx, y:topY-4, 'text-anchor':'middle', 'font-size':'10', 'font-family':'sans-serif', 'font-weight':'bold', fill:'#333' }, totals[i]));
      svg.appendChild(txt('text', { x:cx, y:mT+ph+14, 'text-anchor':'middle', 'font-size':'11', 'font-family':'sans-serif', fill:'#444' }, cats[i]));
    }
    var lx = mL, ly = H - 11;
    for (var j = series.length - 1; j >= 0; j--) {
      svg.appendChild(el('rect', { x:lx, y:ly-8, width:'10', height:'10', fill:series[j].c, rx:'2' }));
      svg.appendChild(txt('text', { x:lx+14, y:ly+1, 'font-size':'10', 'font-family':'sans-serif', fill:'#555' }, series[j].n));
      lx += series[j].n.length * 5.8 + 22;
    }
    container.appendChild(svg);
  }

  // ── lineChart ─────────────────────────────────────────────────────────────
  function lineChart(id, cats, series, opts) {
    opts = opts || {};
    var container = document.getElementById(id);
    if (!container) return;
    var W = opts.W || 460, H = 218, mL = 38, mR = 10, mT = 22, mB = 44;
    var pw = W - mL - mR, ph = H - mT - mB, n = cats.length;
    var suf = opts.suf || '', maxV = opts.maxV || 100, step = pw / (n - 1);
    var svg = el('svg', { viewBox:'0 0 '+W+' '+H, style:'width:100%;height:auto;display:block' });
    for (var i = 0; i <= 5; i++) {
      var v = Math.round(maxV * i / 5), gy = r(mT + ph - ph * i / 5);
      svg.appendChild(el('line', { x1:mL, y1:gy, x2:mL+pw, y2:gy, stroke:'#e8e8e8', 'stroke-width':'1' }));
      svg.appendChild(txt('text', { x:mL-5, y:gy+4, 'text-anchor':'end', 'font-size':'10', 'font-family':'sans-serif', fill:'#aaa' }, v+suf));
    }
    svg.appendChild(el('line', { x1:mL, y1:mT+ph, x2:mL+pw, y2:mT+ph, stroke:'#ddd', 'stroke-width':'1' }));
    if (opts.annotations) opts.annotations.forEach(function(ann) {
      var ax = r(mL + ann.i * step);
      svg.appendChild(el('line', { x1:ax, y1:mT, x2:ax, y2:mT+ph, stroke:'#e0e0e0', 'stroke-width':'1', 'stroke-dasharray':'4,3' }));
      svg.appendChild(txt('text', { x:ax, y:mT-6, 'text-anchor':'middle', 'font-size':'9', 'font-family':'sans-serif', fill:'#bbb' }, ann.label));
    });
    for (var si = 0; si < series.length; si++) {
      var ser = series[si];
      var pts = ser.v.map(function(val, i) { return { x:r(mL+i*step), y:r(mT+ph-(val/maxV)*ph) }; });
      var aD = 'M'+pts[0].x+','+(mT+ph);
      pts.forEach(function(p) { aD += ' L'+p.x+','+p.y; });
      aD += ' L'+pts[pts.length-1].x+','+(mT+ph)+' Z';
      svg.appendChild(el('path', { d:aD, fill:ser.c, opacity:'0.07' }));
      svg.appendChild(el('path', { d:pts.map(function(p,i){return(i===0?'M':'L')+p.x+','+p.y;}).join(' '), fill:'none', stroke:ser.c, 'stroke-width':'2.5', 'stroke-linejoin':'round', 'stroke-linecap':'round' }));
      pts.forEach(function(p, i) {
        svg.appendChild(el('circle', { cx:p.x, cy:p.y, r:'4', fill:'#fff', stroke:ser.c, 'stroke-width':'2' }));
        svg.appendChild(txt('text', { x:p.x, y:r(p.y-9), 'text-anchor':'middle', 'font-size':'10', 'font-family':'sans-serif', 'font-weight':'bold', fill:ser.c }, ser.v[i]+suf));
      });
    }
    for (var i = 0; i < n; i++)
      svg.appendChild(txt('text', { x:r(mL+i*step), y:mT+ph+14, 'text-anchor':'middle', 'font-size':'11', 'font-family':'sans-serif', fill:'#444' }, cats[i]));
    var lx = mL, ly = H - 11;
    for (var si = 0; si < series.length; si++) {
      var ser = series[si];
      svg.appendChild(el('line', { x1:lx, y1:ly-4, x2:lx+14, y2:ly-4, stroke:ser.c, 'stroke-width':'2.5', 'stroke-linecap':'round' }));
      svg.appendChild(el('circle', { cx:lx+7, cy:ly-4, r:'3.5', fill:'#fff', stroke:ser.c, 'stroke-width':'2' }));
      svg.appendChild(txt('text', { x:lx+20, y:ly+1, 'font-size':'10', 'font-family':'sans-serif', fill:'#555' }, ser.n));
      lx += ser.n.length * 5.8 + 28;
    }
    container.appendChild(svg);
  }

  // ── groupedBar ────────────────────────────────────────────────────────────
  // opts.refLine: draw a dashed horizontal line at this Y value (e.g. PI=91)
  function groupedBar(id, cats, series, opts) {
    opts = opts || {};
    var container = document.getElementById(id);
    if (!container) return;
    var W = opts.W || 460, H = 218, mL = 38, mR = 10, mT = 26, mB = 44;
    var pw = W - mL - mR, ph = H - mT - mB, n = cats.length, ns = series.length;
    var allV = []; series.forEach(function(s){ s.v.forEach(function(v){ allV.push(v); }); });
    var maxV = opts.maxV || (Math.ceil(Math.max.apply(null, allV) * 1.2 / 20) * 20);
    var groupW = pw / n, gap = 3, bw = Math.min(30, (groupW - gap * (ns+1)) / ns);
    var svg = el('svg', { viewBox:'0 0 '+W+' '+H, style:'width:100%;height:auto;display:block' });
    for (var i = 0; i <= 5; i++) {
      var v = Math.round(maxV * i / 5), gy = r(mT + ph - ph * i / 5);
      svg.appendChild(el('line', { x1:mL, y1:gy, x2:mL+pw, y2:gy, stroke:'#e8e8e8', 'stroke-width':'1' }));
      svg.appendChild(txt('text', { x:mL-5, y:gy+4, 'text-anchor':'end', 'font-size':'10', 'font-family':'sans-serif', fill:'#aaa' }, v));
    }
    svg.appendChild(el('line', { x1:mL, y1:mT+ph, x2:mL+pw, y2:mT+ph, stroke:'#ddd', 'stroke-width':'1' }));
    if (opts.refLine) {
      var rl = r(mT + ph - (opts.refLine / maxV) * ph);
      svg.appendChild(el('line', { x1:mL, y1:rl, x2:mL+pw, y2:rl, stroke:'#e07a20', 'stroke-width':'1.5', 'stroke-dasharray':'5,3' }));
      svg.appendChild(txt('text', { x:mL+pw-2, y:rl-4, 'text-anchor':'end', 'font-size':'9', 'font-family':'sans-serif', fill:'#e07a20', 'font-weight':'bold' }, 'PI='+opts.refLine+'d'));
    }
    for (var i = 0; i < n; i++) {
      var gx = r(mL + i * groupW + groupW / 2);
      var startX = gx - (ns * bw + (ns-1) * gap) / 2;
      for (var si = 0; si < ns; si++) {
        var val = series[si].v[i], bx = r(startX + si * (bw+gap));
        var bh = r((val / maxV) * ph), by = r(mT + ph - bh);
        svg.appendChild(el('rect', { x:bx, y:by, width:r(bw), height:bh, fill:series[si].c, rx:'2' }));
        svg.appendChild(txt('text', { x:r(bx+bw/2), y:by-3, 'text-anchor':'middle', 'font-size':'9', 'font-family':'sans-serif', 'font-weight':'bold', fill:series[si].c }, val));
      }
      svg.appendChild(txt('text', { x:gx, y:mT+ph+14, 'text-anchor':'middle', 'font-size':'11', 'font-family':'sans-serif', fill:'#444' }, cats[i]));
    }
    var lx = mL, ly = H - 11;
    for (var si = 0; si < series.length; si++) {
      svg.appendChild(el('rect', { x:lx, y:ly-8, width:'10', height:'10', fill:series[si].c, rx:'2' }));
      svg.appendChild(txt('text', { x:lx+14, y:ly+1, 'font-size':'10', 'font-family':'sans-serif', fill:'#555' }, series[si].n));
      lx += series[si].n.length * 5.8 + 22;
    }
    container.appendChild(svg);
  }

  // ── render calls go here ──────────────────────────────────────────────────
  // Replace the arrays below with your computed data.

  var CATS_PI    = ['26-Q1','26-Q2','27-Q1','27-Q2'];
  // Groups from cf[22720] — use actual group names, not project keys.
  // For Privilege Cloud the current groups are:
  var CATS_GROUP = ['EPV pCloud','pCloud','DV'];   // adjust per division

  // c1 — Status by PI (stacked bar)
  stackedBar('c1', CATS_PI, [
    { n:'Done',        c:'#2d9e5a', v:[/*done per PI*/] },
    { n:'In Progress', c:'#3b7ed4', v:[/*ip per PI*/] },
    { n:'Not Started', c:'#cacaca', v:[/*ns per PI*/] }
  ]);

  // c2 — Done themes by PI span per PI (replaces completion rate trend line chart)
  // Shows how many Done themes completed in 1 PI, 2 PIs, or 3+ PIs, per PI quarter.
  stackedBar('c2', CATS_PI, [
    { n:'1 PI',  c:'#2d9e5a', v:[/*1-PI done per PI*/] },
    { n:'2 PIs', c:'#3b7ed4', v:[/*2-PI done per PI*/] },
    { n:'3+ PIs',c:'#e07a20', v:[/*3+-PI done per PI*/] }
  ]);

  // c3 — Themes per PI — Delivery State (4-way unambiguous split)
  // Primary PI = first value in PlannedPI array.
  // NEVER use "Single-PI In-Flight" — use the 4-way split below.
  stackedBar('c3', CATS_PI, [
    { n:'Done \u2014 1 PI',      c:'#2d9e5a', v:[/*done-1PI per PI*/] },
    { n:'Done \u2014 Multi PI',  c:'#52b37a', v:[/*done-multiPI per PI*/] },
    { n:'In Progress',           c:'#3b7ed4', v:[/*in-progress per PI*/] },
    { n:'Not Started',           c:'#cacaca', v:[/*not-started per PI*/] }
  ]);

  // c4 — Status by Group (stacked bar)
  stackedBar('c4', CATS_GROUP, [
    { n:'Done',        c:'#2d9e5a', v:[/*done per group*/] },
    { n:'In Progress', c:'#3b7ed4', v:[/*ip per group*/] },
    { n:'Not Started', c:'#cacaca', v:[/*ns per group*/] }
  ]);

  // c5 — Delivery State by Group (4-way split)
  stackedBar('c5', CATS_GROUP, [
    { n:'Done \u2014 1 PI',      c:'#2d9e5a', v:[/*done-1PI per group*/] },
    { n:'Done \u2014 Multi PI',  c:'#52b37a', v:[/*done-multiPI per group*/] },
    { n:'In Progress',           c:'#3b7ed4', v:[/*in-progress per group*/] },
    { n:'Not Started',           c:'#cacaca', v:[/*not-started per group*/] }
  ]);

  // c6 — Cycle time: avg vs median by group (dashed ref line at 91d = 1 PI)
  // Do NOT include P90. Only Avg and Median.
  groupedBar('c6', CATS_GROUP, [
    { n:'Avg cycle (days)',    c:'#2d6be4', v:[/*avg per group*/] },
    { n:'Median cycle (days)', c:'#7fb3f5', v:[/*median per group*/] }
  ], { maxV:220, refLine:91 });

  // c7 — Throughput per PI window, stacked by group.
  // Values are mapped by FinishWork date → PI window (NOT by PlannedPI field).
  // Label the active/partial PI bar "(active)".
  stackedBar('c7', CATS_PI, [
    { n:'EPV pCloud', c:'#3b7ed4', v:[/*EPV pCloud done per PI window*/] },
    { n:'pCloud',     c:'#2d9e5a', v:[/*pCloud done per PI window*/] },
    { n:'DV',         c:'#9b59b6', v:[/*DV done per PI window*/] }
  ]);

  // c8 — Epic Breakdown Quality by group (grouped bar)
  // Shows how many themes in each group fall into each decomposition category.
  groupedBar('c8', CATS_GROUP, [
    { n:'No Epics',         c:'#e07a20', v:[/*no-epics per group*/] },
    { n:'Monolithic (1)',   c:'#f5c542', v:[/*monolithic per group*/] },
    { n:'Healthy (2\u20137)', c:'#2d9e5a', v:[/*healthy per group*/] },
    { n:'Over-frag (>7)',   c:'#c0392b', v:[/*over-fragmented per group*/] }
  ]);

})();
```

---

## Chart containers in HTML body

**Always use `<div id="cN" style="height:220px">` — never `<canvas>`.**

Chart ID reference:
| ID | Chart | Function |
|----|-------|----------|
| c1 | Status by PI | `stackedBar` |
| c2 | Done themes by PI span per PI | `stackedBar` |
| c3 | Themes per PI — Delivery State | `stackedBar` |
| c4 | Status by Group | `stackedBar` |
| c5 | Delivery State by Group | `stackedBar` |
| c6 | Cycle time by group (avg/median) | `groupedBar` |
| c7 | Throughput per PI window | `stackedBar` |
| c8 | Epic Breakdown Quality by group | `groupedBar` |

> **Do NOT add a "Completion Rate Trend" line chart (c2 was previously this) — it has been removed.**
> c2 is now the "Done themes by PI span per PI" stacked bar chart.

---

## Scorecard card HTML skeleton

```html
<div class="sc-card sc-green">   <!-- or sc-amber / sc-red -->
  <div class="sc-title">Metric Name</div>
  <div class="sc-value">42 <span style="font-size:15px;font-weight:500">%</span></div>
  <span class="sc-signal">&#8593; Signal text &nbsp;&middot;&nbsp; detail</span>
  <span class="sc-tag">Status Label</span>
  <div class="sc-desc">One to two sentence explanation with <strong>recommended action</strong>.</div>
</div>
```

HTML entities: `&#8593;` = ↑, `&#8595;` = ↓, `&#9632;` = ■, `&middot;` = ·, `&rarr;` = →
