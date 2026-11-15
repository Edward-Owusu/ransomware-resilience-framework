"""Interactive dashboard for the Ransomware Resilience Framework.

Run locally:   streamlit run app/streamlit_app.py

Layout: no sidebar. The recovery timeline is the main screen: every critical system's recovery time
against its downtime target. Data and a what-if panel for protective practices sit in the top row.
"""

from __future__ import annotations

import json
import sys
from html import escape
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import ui  # noqa: E402
from ransomware_ready import __version__, assess, parse_practices, parse_systems  # noqa: E402
from ransomware_ready.engine import DataError, load_checks  # noqa: E402
from ransomware_ready.reporting import (DISCLAIMER, TIMELINE_CSS, gauge_svg, timeline_html,  # noqa: E402
                                        to_csv, to_html, to_json, to_markdown)

S = ROOT / "samples"
SAMPLES = {
    "Small manufacturer, untested backups (fictional)": "riverbend_components",
    "Cold storage company, tested recovery (fictional)": "northfield_cold_logistics",
}
OPTIONS = ["yes", "partial", "no", ""]
LABELS = {"yes": "In place", "partial": "Partly", "no": "Not in place", "": "Not answered"}
ANSWER_COLOR = {"yes": "#15803D", "partial": "#B45309", "no": "#BE123C", "": "#94A3B8"}

PAL = ui.Palette(accent="#BE123C", band="#2A1A1F", band_text="#FFFFFF", band_sub="#E3C4CB",
                 card="#FFFFFF", line="#EED9DD", ink="#2A1A1F", muted="#8A7378")
ui.setup("If ransomware hit tonight, could you recover in time?", "Ransomware recovery readiness · CISA #StopRansomware",
         "Describe your critical systems and backups, and see which systems would miss their downtime targets, where "
         "backups could be encrypted too, and what to fix first. Mapped to NIST SP 800-53.", "🛡️", PAL)

# ---- Top row: data and what-if practices -------------------------------------------------------------
t1, t2, t3 = st.columns([1.6, 2.6, 1.5], vertical_alignment="top")
systems_text, practices_doc, key = None, None, "upload"
with t1:
    st.caption("Data")
    source = ui.choose("Data", ["Use a sample", "Upload my own files"], key="source", format_func=ui.source_label)
with t2:
    if source == "Use a sample":
        st.caption("Sample organization")
        key = SAMPLES[st.selectbox("Sample organization", list(SAMPLES), label_visibility="collapsed")]
        systems_text = (S / f"{key}_systems.csv").read_text(encoding="utf-8")
        practices_doc = parse_practices((S / f"{key}_practices.json").read_text(encoding="utf-8"))
    else:
        a, b = st.columns(2)
        up_s = a.file_uploader("Systems inventory (.csv)", type=["csv"])
        up_p = b.file_uploader("Practices (.json, optional)", type=["json"])
        if up_s:
            systems_text = up_s.getvalue().decode("utf-8-sig", errors="replace")
        if up_p:
            try:
                practices_doc = parse_practices(up_p.getvalue().decode("utf-8-sig", errors="replace"))
            except DataError as exc:
                st.error(str(exc))
        key = f"upload_{up_p.name if up_p else 'none'}"
practices_doc = practices_doc or {"organization": "", "practices": {}}
answers = {}
with t3:
    st.caption("What if?")
    with st.popover("Protective practices", use_container_width=True):
        st.caption("Change any practice to see how it moves your readiness score.")
        for p in load_checks()["practices"]:
            cur = practices_doc["practices"].get(p["id"]) or ""
            answers[p["id"]] = st.selectbox(p["label"], OPTIONS, index=OPTIONS.index(cur), format_func=LABELS.get,
                                            key=f"{key}_{p['id']}")
        org = st.text_input("Organization name", practices_doc.get("organization") or "My organization",
                            key=f"{key}_org")
        st.download_button("Systems template", (S / "systems_template.csv").read_bytes(), "systems_template.csv",
                           "text/csv")
        st.download_button("Practices template", (S / "practices_template.json").read_bytes(),
                           "practices_template.json", "application/json")

if systems_text is None:
    st.info("Upload a systems inventory above, or switch to a sample, to see the recovery timeline. Templates are "
            "under Protective practices.")
    ui.footer("ransomware_ready", __version__, "ransomware-resilience-framework", DISCLAIMER)
    st.stop()
try:
    systems = parse_systems(systems_text)
    r = assess(systems, {"organization": org, "practices": {k: v or None for k, v in answers.items()}}, org)
except DataError as exc:
    st.error(f"The file could not be read. {exc} Fix the file and upload it again.")
    st.stop()

c = r.counts()
st.markdown(f"<div class='g-sec'>{escape(r.organization)}</div>", unsafe_allow_html=True)
g, m = st.columns([1.1, 3], vertical_alignment="center")
with g:
    st.markdown(f"<div style='text-align:center'>{gauge_svg(r.readiness, r.band, 250)}</div>", unsafe_allow_html=True)
with m:
    ui.tiles([(f"{c['miss_rto']} of {c['systems']}", "Systems that would miss their downtime target", "#BE123C"),
              (c["no_safe_copy"], "Systems with no backup ransomware cannot reach", "#9F1239"),
              (c["untested"], "Systems with no restore test in the last year", "#B45309"),
              (f"{c['practice_gaps']} of {len(r.practices)}", "Protective practices not fully in place")], PAL)
    st.caption(f"Readiness combines system recoverability ({r.system_score:.0f}/100, weighted by criticality) and "
               f"protective practices ({r.practice_score:.0f}/100).")

ui.section("Recovery timeline", "How long each system would take to recover, including time spent waiting for "
           "systems it depends on, compared with the longest the business can be without it (white marker).")
st.markdown(f"<style>{TIMELINE_CSS}</style><div style='background:#fff;border:1px solid #EED9DD;border-radius:12px;"
            f"padding:10px 16px'>{timeline_html(r)}</div>", unsafe_allow_html=True)

view = ui.choose("View", ["Fix first", "Practices", "Systems"], key="view")
if view == "Fix first":
    ui.section(f"{c['findings']} findings by system", "Systems with the lowest recoverability score first.")
    if not c["findings"]:
        st.success("No system findings.")
    cols = st.columns(2)
    for i, s in enumerate([s for s in sorted(r.systems, key=lambda s: s.score) if s.findings]):
        rows = "".join(f"<div class='d'>{ui.sev_pill(f.severity)}<b>{escape(f.check_id)}</b> {escape(f.title)}. "
                       f"<span class='s'>{escape(f.detail)}</span><div class='f'>Fix: {escape(f.remediation)} "
                       f"<span class='s'>({escape(', '.join(f.controls))})</span></div></div>" for f in s.findings)
        with cols[i % 2]:
            ui.card(f"<div class='h'>{escape(s.system)} <span style='float:right'>score {s.score:.0f}</span></div>"
                    f"<div class='s'>{escape(s.criticality)} · {escape(s.function)}</div>",
                    rows, accent=ui.SEV_COLORS[s.findings[0].severity])
elif view == "Practices":
    ui.section("Protective practices", "Change these in the What if? panel at the top.")
    cols = st.columns(2)
    for i, p in enumerate(r.practices):
        ans = p.answer or ""
        cols[i % 2].markdown(f"<div class='g-card' style='border-left-color:{ANSWER_COLOR[ans]}'><div class='h'>"
                             f"{ui.pill(LABELS[ans], ANSWER_COLOR[ans])}{escape(p.label)}</div><div class='s'>"
                             f"{escape(', '.join(p.controls))}</div></div>", unsafe_allow_html=True)
else:
    st.dataframe(pd.DataFrame([{
        "System": s.system, "Criticality": s.criticality, "Target downtime (h)": s.rto_hours,
        "Recovery (h)": s.effective_recovery_hours, "Waits for": s.blocking_dependency,
        "Data loss tolerance (h)": s.rpo_hours, "Backup interval (h)": s.data_loss_window_hours, "Score": s.score}
        for s in r.systems]), hide_index=True, use_container_width=True)

ui.downloads([("HTML report", to_html(r), "ransomware_readiness.html", "text/html"),
              ("Markdown", to_markdown(r), "ransomware_readiness.md", "text/markdown"),
              ("CSV findings", to_csv(r), "ransomware_findings.csv", "text/csv"),
              ("JSON results", to_json(r), "ransomware_readiness.json", "application/json"),
              ("Practices (JSON)", json.dumps({"organization": org, "practices": answers}, indent=2),
               "practices.json", "application/json")])
ui.footer("ransomware_ready", __version__, "ransomware-resilience-framework", DISCLAIMER)
