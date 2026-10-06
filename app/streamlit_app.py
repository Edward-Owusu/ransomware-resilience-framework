"""Interactive dashboard for the Ransomware Resilience Framework.

Run locally:   streamlit run app/streamlit_app.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

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
SEV_ICON = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "⚪"}

st.set_page_config(page_title="Ransomware Resilience", page_icon="🛡️", layout="wide")
st.title("🛡️ Ransomware recovery readiness")
st.write("If ransomware hit tonight, could you recover in time? Describe your critical systems and backups, and see "
         "which systems would miss their downtime targets, where backups could be encrypted too, and what to fix "
         "first. Based on CISA and NIST ransomware guidance, mapped to NIST SP 800-53.")

with st.sidebar:
    st.header("1. Choose data")
    source = st.radio("Data", ["Use a sample", "Upload my own files"], label_visibility="collapsed")
    systems_text, practices_doc, key = None, None, "upload"
    if source == "Use a sample":
        key = SAMPLES[st.selectbox("Sample organization", list(SAMPLES))]
        systems_text = (S / f"{key}_systems.csv").read_text(encoding="utf-8")
        practices_doc = parse_practices((S / f"{key}_practices.json").read_text(encoding="utf-8"))
    else:
        up_s = st.file_uploader("Systems inventory (.csv)", type=["csv"])
        up_p = st.file_uploader("Practices (.json, optional)", type=["json"])
        st.download_button("Systems template", (S / "systems_template.csv").read_bytes(), "systems_template.csv", "text/csv")
        st.download_button("Practices template", (S / "practices_template.json").read_bytes(), "practices_template.json",
                           "application/json")
        if up_s:
            systems_text = up_s.getvalue().decode("utf-8-sig", errors="replace")
        if up_p:
            try:
                practices_doc = parse_practices(up_p.getvalue().decode("utf-8-sig", errors="replace"))
            except DataError as exc:
                st.error(str(exc))
        key = f"upload_{up_p.name if up_p else 'none'}"
    practices_doc = practices_doc or {"organization": "", "practices": {}}

    st.header("2. Protective practices")
    st.caption("Adjust these to see how each one changes your readiness.")
    answers = {}
    for p in load_checks()["practices"]:
        cur = practices_doc["practices"].get(p["id"]) or ""
        answers[p["id"]] = st.selectbox(p["label"], OPTIONS, index=OPTIONS.index(cur), format_func=LABELS.get,
                                        key=f"{key}_{p['id']}")
    org = st.text_input("Organization name", practices_doc.get("organization") or "My organization", key=f"{key}_org")
    st.caption(f"ransomware_ready {__version__}. Runs entirely in this session; uploaded files are not stored.")

if systems_text is None:
    st.info("Upload a systems inventory in the sidebar, or switch to a sample, to see results.")
    st.stop()
try:
    systems = parse_systems(systems_text)
    r = assess(systems, {"organization": org, "practices": {k: v or None for k, v in answers.items()}}, org)
except DataError as exc:
    st.error(f"The file could not be read. {exc} Fix the file and upload it again.")
    st.stop()

c = r.counts()
st.subheader(r.organization)
g, m = st.columns([2, 3])
with g:
    st.markdown(f"<div style='text-align:center'>{gauge_svg(r.readiness, r.band, 300)}</div>", unsafe_allow_html=True)
with m:
    a, b = st.columns(2)
    a.metric("Systems that would miss their downtime target", f"{c['miss_rto']} of {c['systems']}")
    b.metric("Systems with no backup ransomware cannot reach", c["no_safe_copy"])
    a.metric("Systems with no restore test in the last year", c["untested"])
    b.metric("Protective practices not fully in place", f"{c['practice_gaps']} of {len(r.practices)}")
    st.caption(f"Readiness combines system recoverability ({r.system_score:.0f}/100, weighted by criticality) and "
               f"protective practices ({r.practice_score:.0f}/100).")

st.markdown("### Recovery timeline")
st.caption("How long each system would take to recover, including time spent waiting for systems it depends on, "
           "compared with the longest the business can be without it (white marker).")
st.markdown(f"<style>{TIMELINE_CSS}</style>{timeline_html(r)}", unsafe_allow_html=True)

tab_f, tab_p, tab_s = st.tabs([f"Findings ({c['findings']})", "Practices", "Systems"])
with tab_f:
    for s in r.systems:
        if not s.findings:
            continue
        worst = s.findings[0].severity
        with st.expander(f"{SEV_ICON[worst]} {s.system} · {s.criticality} · {len(s.findings)} finding(s) · score {s.score:.0f}"):
            for f in s.findings:
                st.markdown(f"**{f.severity.title()} · {f.check_id}** {f.title}. {f.detail}  \n"
                            f"*Fix:* {f.remediation}  \n*Controls:* {', '.join(f.controls)}")
    if not c["findings"]:
        st.success("No system findings.")
with tab_p:
    st.dataframe(pd.DataFrame([{"Practice": p.label, "Status": LABELS[p.answer or ""], "Controls": ", ".join(p.controls)}
                               for p in r.practices]), hide_index=True)
with tab_s:
    st.dataframe(pd.DataFrame([{
        "System": s.system, "Criticality": s.criticality, "Target downtime (h)": s.rto_hours,
        "Recovery (h)": s.effective_recovery_hours, "Waits for": s.blocking_dependency,
        "Data loss tolerance (h)": s.rpo_hours, "Backup interval (h)": s.data_loss_window_hours, "Score": s.score}
        for s in r.systems]), hide_index=True)

st.markdown("### Download the report")
d = st.columns(5)
d[0].download_button("HTML report", to_html(r), "ransomware_readiness.html", "text/html")
d[1].download_button("Markdown", to_markdown(r), "ransomware_readiness.md", "text/markdown")
d[2].download_button("CSV findings", to_csv(r), "ransomware_findings.csv", "text/csv")
d[3].download_button("JSON results", to_json(r), "ransomware_readiness.json", "application/json")
d[4].download_button("Practices (JSON)", json.dumps({"organization": org, "practices": answers}, indent=2),
                     "practices.json", "application/json")
st.caption(DISCLAIMER)
