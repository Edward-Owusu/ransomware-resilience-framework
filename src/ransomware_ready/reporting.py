"""Write ransomware readiness results: gauge, recovery timeline, findings, and practices."""

from __future__ import annotations

import csv
import io
import json
import math
from html import escape

from .engine import Result

DISCLAIMER = (
    "This is a planning aid based on the information supplied. Recovery times are taken from the inventory "
    "and should be confirmed by timed restore tests. It does not replace an incident response plan, legal "
    "counsel, or professional incident response support."
)
BAND_COLOR = {"Resilient": "#16a34a", "Partially resilient": "#ca8a04", "Vulnerable": "#ea580c",
              "Highly vulnerable": "#be123c"}
ANSWER_LABEL = {"yes": "In place", "partial": "Partly", "no": "Not in place", None: "Not answered"}


def gauge_svg(score: float, band: str, size: int = 260) -> str:
    """Semicircle gauge from 0 to 100."""
    r, cx, cy = 100, 120, 118
    length = math.pi * r
    filled = max(0.0, min(100.0, score)) / 100 * length
    color = BAND_COLOR.get(band, "#e11d48")
    return (f'<svg viewBox="0 0 240 150" width="{size}" role="img" aria-label="Readiness {score:.0f} of 100, {escape(band)}">'
            f'<path d="M {cx - r} {cy} A {r} {r} 0 0 1 {cx + r} {cy}" fill="none" stroke="#ecdfe1" stroke-width="18" stroke-linecap="round"/>'
            f'<path d="M {cx - r} {cy} A {r} {r} 0 0 1 {cx + r} {cy}" fill="none" stroke="{color}" stroke-width="18" '
            f'stroke-linecap="round" stroke-dasharray="{filled:.1f} 999"/>'
            f'<text x="{cx}" y="{cy - 18}" text-anchor="middle" font-size="44" font-weight="700" fill="#2a1a1f" '
            f'font-family="Segoe UI, Roboto, Arial, sans-serif">{score:.0f}</text>'
            f'<text x="{cx}" y="{cy + 6}" text-anchor="middle" font-size="13" fill="{color}" '
            f'font-family="Segoe UI, Roboto, Arial, sans-serif">{escape(band)}</text>'
            f'<text x="{cx - r}" y="{cy + 26}" text-anchor="middle" font-size="11" fill="#8a7378">0</text>'
            f'<text x="{cx + r}" y="{cy + 26}" text-anchor="middle" font-size="11" fill="#8a7378">100</text></svg>')


TIMELINE_CSS = """
.tl{font:13px/1.4 "Segoe UI",Roboto,Arial,sans-serif;color:#3b2a2f}
.tl .row{display:grid;grid-template-columns:200px 1fr 120px;gap:12px;align-items:center;margin:8px 0}
.tl .nm b{display:block;color:#2a1a1f}.tl .nm span{color:#8a7378;font-size:12px}
.tl .track{position:relative;height:22px;background:#f1e4e6;border-radius:4px}
.tl .own{position:absolute;top:0;height:100%;background:#be123c;border-radius:4px}
.tl .own.ok{background:#16a34a}
.tl .wait{position:absolute;top:0;height:100%;background:repeating-linear-gradient(45deg,#b8a9ad,#b8a9ad 4px,#d6cacd 4px,#d6cacd 8px);border-radius:4px 0 0 4px}
.tl .rto{position:absolute;top:-4px;bottom:-4px;width:3px;background:#2a1a1f}
.tl .none{color:#be123c;font-weight:600;padding-left:6px;line-height:22px}
.tl .val{font-size:12px;color:#5b464b}
.tl .legend{color:#8a7378;font-size:12px;margin-top:10px}
.tl .legend i{display:inline-block;width:12px;height:12px;vertical-align:-2px;margin:0 4px 0 12px;border-radius:2px}
"""


def timeline_html(r: Result) -> str:
    e = escape
    vals = [s.rto_hours for s in r.systems] + [s.effective_recovery_hours or 0 for s in r.systems]
    scale = max(vals + [1]) * 1.08
    rows = []
    for s in r.systems:
        rto_pos = 100 * s.rto_hours / scale
        if s.effective_recovery_hours is None:
            bar = f'<div class="none">Cannot be recovered{" (needs " + e(s.blocking_dependency) + ")" if s.blocking_dependency else ""}</div>'
            val = "No recovery"
        else:
            own = s.restore_time_hours or 0
            wait = max(0.0, s.effective_recovery_hours - own)
            ok = s.effective_recovery_hours <= s.rto_hours
            bar = ((f'<div class="wait" style="left:0;width:{100 * wait / scale:.1f}%" title="Waiting for {e(s.blocking_dependency or "")}"></div>'
                    if wait else "")
                   + f'<div class="own{" ok" if ok else ""}" style="left:{100 * wait / scale:.1f}%;width:{max(0.6, 100 * own / scale):.1f}%"></div>')
            val = f"{s.effective_recovery_hours:g} h / target {s.rto_hours:g} h"
        rows.append(f'<div class="row"><div class="nm"><b>{e(s.system)}</b><span>{e(s.criticality.title())}</span></div>'
                    f'<div class="track">{bar}<div class="rto" style="left:{rto_pos:.1f}%" title="Recovery time objective {s.rto_hours:g} h"></div></div>'
                    f'<div class="val">{val}</div></div>')
    legend = ('<div class="legend"><i style="background:#16a34a"></i>Recovers within target'
              '<i style="background:#be123c"></i>Misses target<i style="background:#b8a9ad"></i>Waiting for a dependency'
              '<i style="background:#2a1a1f;width:3px"></i>Maximum tolerable downtime</div>')
    return f'<div class="tl">{"".join(rows)}{legend}</div>'


def to_json(r: Result) -> str:
    return json.dumps(r.to_dict(), indent=2, default=str)


def to_csv(r: Result) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["system", "criticality", "check_id", "title", "severity", "controls", "detail", "remediation"])
    for name, f in r.findings():
        crit = next(s.criticality for s in r.systems if s.system == name)
        w.writerow([name, crit, f.check_id, f.title, f.severity, "; ".join(f.controls), f.detail, f.remediation])
    return buf.getvalue()


def to_markdown(r: Result) -> str:
    c = r.counts()
    lines = [f"# Ransomware recovery readiness: {r.organization}", "",
             f"As of {r.as_of} | {c['systems']} systems | Generated {r.generated_at}", "",
             f"- Readiness: **{r.readiness:.0f}/100 ({r.band})** (systems {r.system_score:.0f}, practices {r.practice_score:.0f})",
             f"- Systems that would miss their downtime target: **{c['miss_rto']}**",
             f"- Systems without a backup copy ransomware cannot reach: **{c['no_safe_copy']}**",
             f"- Systems with no restore test in the last year: **{c['untested']}**", "",
             "## Recovery timeline", "", "| System | Criticality | Recovery | Target | Status |", "|---|---|---|---|---|"]
    for s in r.systems:
        rec = "cannot recover" if s.effective_recovery_hours is None else f"{s.effective_recovery_hours:g} h"
        ok = s.effective_recovery_hours is not None and s.effective_recovery_hours <= s.rto_hours
        lines.append(f"| {s.system} | {s.criticality} | {rec} | {s.rto_hours:g} h | {'Within target' if ok else 'Misses target'} |")
    lines += ["", "## Findings", ""]
    for name, f in r.findings():
        lines.append(f"- **[{f.severity.upper()}] {f.check_id} {name}: {f.title}.** {f.detail} Fix: {f.remediation} "
                     f"_({', '.join(f.controls)})_")
    lines += ["", "## Organization-wide practices", "", "| Practice | Status | Controls |", "|---|---|---|"]
    lines += [f"| {p.label} | {ANSWER_LABEL[p.answer]} | {', '.join(p.controls)} |" for p in r.practices]
    lines += ["", f"_{DISCLAIMER}_", ""]
    return "\n".join(lines)


_CSS = """
*{box-sizing:border-box}
body{margin:0;background:#fcf8f8;color:#2a1a1f;font:15px/1.55 "Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif}
main{max-width:1060px;margin:0 auto;padding:34px 24px 60px}
.kicker{color:#be123c;text-transform:uppercase;letter-spacing:.14em;font-size:12px;margin:0;font-weight:600}
h1{font-size:30px;margin:4px 0 2px}
.sub{color:#8a7378;margin:0}
h2{font-size:18px;margin:38px 0 14px;color:#be123c;border-bottom:1px solid #ecdfe1;padding-bottom:8px}
.hero{display:grid;grid-template-columns:300px 1fr;gap:28px;align-items:center;margin-top:24px;background:#fff;border:1px solid #ecdfe1;border-top:5px solid #be123c;border-radius:14px;padding:18px 24px}
.stats{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}
.stat{background:#fcf8f8;border:1px solid #ecdfe1;border-radius:10px;padding:12px 14px}
.stat b{display:block;font-size:26px}.stat span{color:#8a7378;font-size:13px}
.panel{background:#fff;border:1px solid #ecdfe1;border-radius:14px;padding:16px 20px}
.f{border-top:1px solid #ecdfe1;padding:10px 0}.f:first-child{border-top:0}
.f p{margin:2px 0}
.sev{display:inline-block;font-size:11px;font-weight:700;text-transform:uppercase;padding:1px 7px;border-radius:3px;color:#fff;background:#be123c;margin-right:6px}
.sev.high{background:#ea580c}.sev.medium{background:#ca8a04}.sev.low{background:#78716c}
.muted{color:#8a7378}
.table-wrap{overflow-x:auto}
table{border-collapse:collapse;width:100%;font-size:14px}
th,td{border-bottom:1px solid #ecdfe1;padding:8px 10px;text-align:left}
th{color:#8a7378;font-weight:600}
.a-yes{color:#16a34a;font-weight:600}.a-partial{color:#ca8a04;font-weight:600}.a-no,.a-None{color:#be123c;font-weight:600}
.note{color:#8a7378;font-size:13px;margin-top:30px}
@media(max-width:760px){.hero{grid-template-columns:1fr}}
"""


def to_html(r: Result) -> str:
    e = escape
    c = r.counts()
    fnd = "".join(
        f'<div class="f"><p><span class="sev {f.severity}">{e(f.severity)}</span><strong>{e(name)}</strong>: {e(f.title)}</p>'
        f'<p class="muted">{e(f.detail)} Controls: {e(", ".join(f.controls))}.</p><p><strong>Fix:</strong> {e(f.remediation)}</p></div>'
        for name, f in r.findings()) or "<p>No findings.</p>"
    prac = "".join(f'<tr><td>{e(p.label)}</td><td class="a-{p.answer}">{ANSWER_LABEL[p.answer]}</td><td>{e(", ".join(p.controls))}</td></tr>'
                   for p in r.practices)
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Ransomware recovery readiness: {e(r.organization)}</title><style>{_CSS}{TIMELINE_CSS}</style></head><body><main>
<p class="kicker">Ransomware recovery readiness</p><h1>{e(r.organization)}</h1>
<p class="sub">As of {e(r.as_of)}. Generated {e(r.generated_at)} by ransomware_ready {e(r.tool_version)}.</p>
<div class="hero"><div>{gauge_svg(r.readiness, r.band)}</div><div class="stats">
<div class="stat"><b>{c['miss_rto']} of {c['systems']}</b><span>Systems that would miss their downtime target</span></div>
<div class="stat"><b>{c['no_safe_copy']}</b><span>Systems with no backup ransomware cannot reach</span></div>
<div class="stat"><b>{c['untested']}</b><span>Systems with no restore test in the last year</span></div>
<div class="stat"><b>{c['practice_gaps']} of {len(r.practices)}</b><span>Protective practices not fully in place</span></div></div></div>
<h2>Recovery timeline</h2><div class="panel">{timeline_html(r)}</div>
<h2>Findings</h2><div class="panel">{fnd}</div>
<h2>Organization-wide practices</h2><div class="panel table-wrap"><table><thead><tr><th>Practice</th><th>Status</th><th>Controls</th></tr></thead><tbody>{prac}</tbody></table></div>
<p class="note">Readiness combines system recoverability ({r.system_score:.0f}/100, weighted by criticality) and protective practices ({r.practice_score:.0f}/100). {e(DISCLAIMER)}</p>
</main></body></html>"""


WRITERS = {"json": to_json, "csv": to_csv, "md": to_markdown, "html": to_html}
