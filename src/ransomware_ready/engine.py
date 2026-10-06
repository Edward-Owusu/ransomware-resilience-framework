"""Assess ransomware recoverability from a system inventory and organization-wide practices."""

from __future__ import annotations

import csv
import io
import json
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

DATA = Path(__file__).parent / "data"
CRITICALITY = ("critical", "high", "medium", "low")
BACKUP_TYPES = ("image", "file", "saas", "replica", "none")
ANSWER = {"yes": 1.0, "partial": 0.5, "no": 0.0}
SEV = ["critical", "high", "medium", "low"]
_T, _F = {"true", "yes", "y", "1"}, {"false", "no", "n", "0"}


class DataError(ValueError):
    """Raised when an input file cannot be read."""


def load_model(path: str | Path | None = None) -> dict:
    m = json.loads((DATA / "model.json").read_text(encoding="utf-8"))
    if path:
        m.update(json.loads(Path(path).read_text(encoding="utf-8")))
    return m


def load_checks() -> dict:
    return json.loads((DATA / "checks.json").read_text(encoding="utf-8"))


@dataclass
class System:
    name: str
    owner: str
    function: str
    criticality: str
    rto_hours: float
    rpo_hours: float
    backup_type: str
    backup_frequency_hours: float | None
    offline_or_immutable: bool | None
    backup_encrypted: bool | None
    separate_backup_credentials: bool | None
    backup_monitored: bool | None
    last_restore_test: date | None
    restore_time_hours: float | None
    restore_time_measured: bool | None
    depends_on: list[str]


def _b(v: str, col: str, row: int) -> bool | None:
    v = (v or "").strip().lower()
    if not v:
        return None
    if v in _T:
        return True
    if v in _F:
        return False
    raise DataError(f"Row {row}: '{col}' must be true or false, got '{v}'.")


def _num(v: str, col: str, row: int, required: bool = False) -> float | None:
    v = (v or "").strip()
    if not v:
        if required:
            raise DataError(f"Row {row}: '{col}' is required.")
        return None
    try:
        n = float(v)
    except ValueError as exc:
        raise DataError(f"Row {row}: '{col}' must be a number of hours, got '{v}'.") from exc
    if n < 0:
        raise DataError(f"Row {row}: '{col}' cannot be negative.")
    return n


def parse_systems(text: str) -> list[System]:
    reader = csv.DictReader(io.StringIO(text.lstrip("\ufeff")))
    cols = [c.strip().lower() for c in (reader.fieldnames or [])]
    missing = [c for c in ("system", "criticality", "rto_hours", "rpo_hours", "backup_type") if c not in cols]
    if missing:
        raise DataError(f"The systems file is missing required column(s): {', '.join(missing)}.")
    systems, seen = [], set()
    for i, raw in enumerate(reader, start=2):
        r = {(k or "").strip().lower(): (v or "").strip() for k, v in raw.items()}
        if not r.get("system"):
            continue
        name = r["system"]
        if name.lower() in seen:
            raise DataError(f"Row {i}: system '{name}' appears more than once.")
        seen.add(name.lower())
        crit, btype = r["criticality"].lower(), r["backup_type"].lower()
        if crit not in CRITICALITY:
            raise DataError(f"Row {i}: criticality must be one of {', '.join(CRITICALITY)}, got '{crit}'.")
        if btype not in BACKUP_TYPES:
            raise DataError(f"Row {i}: backup_type must be one of {', '.join(BACKUP_TYPES)}, got '{btype}'.")
        test = r.get("last_restore_test_date", "")
        try:
            test_d = date.fromisoformat(test) if test else None
        except ValueError as exc:
            raise DataError(f"Row {i}: last_restore_test_date must look like 2026-03-31, got '{test}'.") from exc
        systems.append(System(
            name=name, owner=r.get("owner", ""), function=r.get("business_function", ""), criticality=crit,
            rto_hours=_num(r["rto_hours"], "rto_hours", i, True), rpo_hours=_num(r["rpo_hours"], "rpo_hours", i, True),
            backup_type=btype, backup_frequency_hours=_num(r.get("backup_frequency_hours", ""), "backup_frequency_hours", i),
            offline_or_immutable=_b(r.get("offline_or_immutable", ""), "offline_or_immutable", i),
            backup_encrypted=_b(r.get("backup_encrypted", ""), "backup_encrypted", i),
            separate_backup_credentials=_b(r.get("separate_backup_credentials", ""), "separate_backup_credentials", i),
            backup_monitored=_b(r.get("backup_monitored", ""), "backup_monitored", i),
            last_restore_test=test_d,
            restore_time_hours=_num(r.get("restore_time_hours", ""), "restore_time_hours", i),
            restore_time_measured=_b(r.get("restore_time_measured", ""), "restore_time_measured", i),
            depends_on=[d.strip() for d in r.get("depends_on", "").split(";") if d.strip()],
        ))
    if not systems:
        raise DataError("The systems file has a header but no system rows.")
    names = {s.name.lower() for s in systems}
    for s in systems:
        for d in s.depends_on:
            if d.lower() not in names:
                raise DataError(f"System '{s.name}' depends on '{d}', which is not in the file.")
    return systems


def parse_practices(text: str) -> dict:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise DataError(f"The practices file is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise DataError("The practices file must be a JSON object.")
    known = {p["id"] for p in load_checks()["practices"]}
    answers = {}
    for pid, val in (data.get("practices") or {}).items():
        if pid not in known:
            raise DataError(f"Unknown practice id '{pid}'.")
        v = str(val or "").strip().lower()
        if v and v not in ANSWER:
            raise DataError(f"Practice {pid}: answer must be yes, partial, or no, got '{v}'.")
        answers[pid] = v or None
    return {"organization": data.get("organization", ""), "practices": answers}


def load_systems(path: str | Path) -> list[System]:
    return parse_systems(Path(path).read_text(encoding="utf-8-sig"))


def load_practices(path: str | Path) -> dict:
    return parse_practices(Path(path).read_text(encoding="utf-8-sig"))


@dataclass
class Finding:
    check_id: str
    title: str
    severity: str
    controls: list[str]
    detail: str
    remediation: str


@dataclass
class SystemResult:
    system: str
    function: str
    criticality: str
    rto_hours: float
    rpo_hours: float
    restore_time_hours: float | None
    effective_recovery_hours: float | None
    blocking_dependency: str | None
    data_loss_window_hours: float | None
    score: float
    findings: list[Finding] = field(default_factory=list)


@dataclass
class PracticeResult:
    id: str
    label: str
    answer: str | None
    controls: list[str]


@dataclass
class Result:
    organization: str
    as_of: str
    generated_at: str
    tool_version: str
    readiness: float
    band: str
    system_score: float
    practice_score: float
    systems: list[SystemResult]
    practices: list[PracticeResult]

    def findings(self) -> list[tuple[str, Finding]]:
        out = [(s.system, f) for s in self.systems for f in s.findings]
        return sorted(out, key=lambda x: (SEV.index(x[1].severity), x[1].check_id, x[0]))

    def counts(self) -> dict[str, Any]:
        fs = self.findings()
        return {
            "systems": len(self.systems),
            "miss_rto": sum(1 for s in self.systems
                            if s.effective_recovery_hours is None or s.effective_recovery_hours > s.rto_hours),
            "no_safe_copy": sum(1 for s in self.systems if any(f.check_id in ("RR-01", "RR-02") for f in s.findings)),
            "untested": sum(1 for s in self.systems if any(f.check_id == "RR-05" for f in s.findings)),
            "critical_findings": sum(1 for _, f in fs if f.severity == "critical"),
            "findings": len(fs),
            "practice_gaps": sum(1 for p in self.practices if p.answer != "yes"),
        }

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["counts"] = self.counts()
        return d


def _effective(systems: dict[str, System]) -> dict[str, tuple[float | None, str | None]]:
    """Recovery time including dependencies that must be restored first: own time + slowest dependency chain."""
    memo: dict[str, tuple[float | None, str | None]] = {}

    def visit(key: str, stack: tuple[str, ...]) -> tuple[float | None, str | None]:
        if key in memo:
            return memo[key]
        if key in stack:
            raise DataError(f"Circular dependency involving '{systems[key].name}'.")
        s = systems[key]
        own = None if s.backup_type == "none" else s.restore_time_hours
        worst, blocker = 0.0, None
        for d in s.depends_on:
            t, _ = visit(d.lower(), stack + (key,))
            if t is None:
                memo[key] = (None, systems[d.lower()].name)
                return memo[key]
            if t > worst:
                worst, blocker = t, systems[d.lower()].name
        memo[key] = (None, None) if own is None else (own + worst, blocker)
        return memo[key]

    for k in systems:
        visit(k, ())
    return memo


def assess(systems: list[System], practices: dict | None = None, organization: str | None = None,
           model: dict | None = None, as_of: date | None = None) -> Result:
    from . import __version__

    model = model or load_model()
    as_of = as_of or date.today()
    meta = load_checks()
    checks = {c["id"]: c for c in meta["system_checks"]}
    by_key = {s.name.lower(): s for s in systems}
    eff = _effective(by_key)

    results: list[SystemResult] = []
    for s in systems:
        fs: list[Finding] = []

        def add(cid: str, detail: str, severity: str | None = None) -> None:
            c = checks[cid]
            fs.append(Finding(cid, c["title"], severity or c["severity"], c["controls"], detail, c["remediation"]))

        effective, blocker = eff[s.name.lower()]
        window = None
        if s.backup_type == "none":
            add("RR-01", "This system has no backup at all.")
        else:
            if s.offline_or_immutable is not True:
                add("RR-02", "All backup copies are online and writable, so ransomware could encrypt or delete them.")
            if s.backup_frequency_hours is not None:
                window = s.backup_frequency_hours
                if window > s.rpo_hours:
                    add("RR-03", f"Backups every {window:g} h, but at most {s.rpo_hours:g} h of data can be lost.")
            if effective is None:
                if blocker:
                    add("RR-04", f"Depends on {blocker}, which cannot be recovered.",
                        "critical" if s.criticality == "critical" else None)
                else:
                    add("RR-04", "No recovery time is recorded, so recovery within the target cannot be shown.")
            elif effective > s.rto_hours:
                via = (f" including {effective - s.restore_time_hours:g} h waiting for {blocker} to be restored first"
                       if blocker and s.restore_time_hours is not None and s.restore_time_hours <= s.rto_hours else "")
                add("RR-04", f"Recovery takes about {effective:g} h{via}; the business can be down at most {s.rto_hours:g} h.",
                    "critical" if s.criticality == "critical" else None)
            age = (as_of - s.last_restore_test).days if s.last_restore_test else None
            if age is None or age > model["restore_test_max_age_days"]:
                add("RR-05", "Restore has never been tested." if age is None else f"Last restore test was {age} days ago.")
            if s.restore_time_hours is not None and s.restore_time_measured is not True:
                add("RR-06", f"The {s.restore_time_hours:g} h restore time has not been confirmed by a timed test.")
            if s.backup_type != "saas" and s.separate_backup_credentials is not True:
                add("RR-07", "Someone who takes over a production admin account could also delete the backups.")
            if s.backup_monitored is not True:
                add("RR-08", "Failed backups could go unnoticed.")
            if s.backup_encrypted is not True:
                add("RR-09", "Backup copies are stored unencrypted.")
        fs.sort(key=lambda f: (SEV.index(f.severity), f.check_id))
        score = max(0.0, 100.0 - sum(checks[f.check_id]["penalty"] for f in fs))
        results.append(SystemResult(s.name, s.function, s.criticality, s.rto_hours, s.rpo_hours, s.restore_time_hours,
                                    effective, blocker, window, score, fs))

    weights = model["criticality_weight"]
    total_w = sum(weights[s.criticality] for s in results)
    system_score = round(sum(weights[s.criticality] * s.score for s in results) / total_w, 1)

    answers = (practices or {}).get("practices", {})
    plist = [PracticeResult(p["id"], p["label"], answers.get(p["id"]), p["controls"]) for p in meta["practices"]]
    pw = {p["id"]: p["weight"] for p in meta["practices"]}
    practice_score = round(100 * sum(pw[p.id] * ANSWER.get(p.answer or "no", 0) for p in plist) / sum(pw.values()), 1)
    readiness = round(model["system_share"] * system_score + model["practice_share"] * practice_score, 1)
    band = next(label for floor, label in model["bands"] if readiness >= floor)
    org = organization or (practices or {}).get("organization") or "Unnamed organization"
    results.sort(key=lambda s: (CRITICALITY.index(s.criticality), s.score, s.system.lower()))
    return Result(org, as_of.isoformat(), datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"), __version__,
                  readiness, band, system_score, practice_score, results, plist)
