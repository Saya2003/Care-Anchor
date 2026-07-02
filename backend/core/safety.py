from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum

from backend.config import settings


class Severity(str, Enum):
    INFO = "info"
    WARN = "warn"
    CRITICAL = "critical"


@dataclass
class SafetyVerdict:
    severity: Severity = Severity.INFO
    alerts: list[str] = field(default_factory=list)
    risk_score: float = 0.0


@dataclass
class _Threshold:
    label: str
    warn_min: float | None
    warn_max: float | None
    crit_min: float | None
    crit_max: float | None

    def check(self, value: float) -> tuple[Severity | None, str]:
        if self.crit_max is not None and value > self.crit_max:
            return Severity.CRITICAL, f"{self.label} ({value}) exceeds critical maximum ({self.crit_max})"
        if self.crit_min is not None and value < self.crit_min:
            return Severity.CRITICAL, f"{self.label} ({value}) below critical minimum ({self.crit_min})"
        if self.warn_max is not None and value > self.warn_max:
            return Severity.WARN, f"{self.label} ({value}) exceeds warning threshold ({self.warn_max})"
        if self.warn_min is not None and value < self.warn_min:
            return Severity.WARN, f"{self.label} ({value}) below warning threshold ({self.warn_min})"
        return None, ""


VITAL_THRESHOLDS: dict[str, _Threshold] = {
    "systolic_bp": _Threshold(
        label="Systolic BP",
        warn_min=90.0,
        warn_max=float(settings.systolic_bp_warn_max),
        crit_min=70.0,
        crit_max=float(settings.systolic_bp_crit_max),
    ),
    "diastolic_bp": _Threshold(
        label="Diastolic BP",
        warn_min=None,
        warn_max=float(settings.diastolic_bp_warn_max),
        crit_min=None,
        crit_max=float(settings.diastolic_bp_crit_max),
    ),
    "heart_rate": _Threshold(
        label="Heart rate",
        warn_min=float(settings.heart_rate_warn_min),
        warn_max=float(settings.heart_rate_warn_max),
        crit_min=float(settings.heart_rate_crit_min),
        crit_max=float(settings.heart_rate_crit_max),
    ),
    "sp_o2": _Threshold(
        label="Oxygen saturation",
        warn_min=float(settings.sp_o2_warn_min),
        warn_max=None,
        crit_min=float(settings.sp_o2_crit_min),
        crit_max=None,
    ),
    "temperature": _Threshold(
        label="Temperature",
        warn_min=None,
        warn_max=settings.temperature_warn_max,
        crit_min=None,
        crit_max=settings.temperature_crit_max,
    ),
    "respiratory_rate": _Threshold(
        label="Respiratory rate",
        warn_min=10.0,
        warn_max=24.0,
        crit_min=8.0,
        crit_max=30.0,
    ),
}


def check_vitals(vitals: dict) -> SafetyVerdict:
    verdict = SafetyVerdict()
    highest: Severity = Severity.INFO
    borderline_count = 0

    for key, threshold in VITAL_THRESHOLDS.items():
        raw = vitals.get(key)
        if raw is None:
            continue
        value = float(raw)
        sev, msg = threshold.check(value)
        if sev is None:
            continue
        verdict.alerts.append(msg)
        borderline_count += 1
        if _severity_index(sev) > _severity_index(highest):
            highest = sev

    if not verdict.alerts:
        return verdict

    verdict.severity = highest
    verdict.risk_score = _compute_risk_score(highest, borderline_count)
    return verdict


def _severity_index(s: Severity) -> int:
    return {"info": 0, "warn": 1, "critical": 2}.get(s.value, 0)


def _compute_risk_score(severity: Severity, borderline_count: int) -> float:
    base = {"info": 0.0, "warn": 3.0, "critical": 8.0}.get(severity.value, 0.0)
    compound = max(0, borderline_count - 1) * 1.5
    return min(base + compound, 10.0)


CRITICAL_KEYWORD_RULES: list[tuple[re.Pattern, Severity, str]] = [
    (re.compile(r"\bsevere chest pain\b", re.IGNORECASE), Severity.CRITICAL, "Patient-reported severe chest pain"),
    (re.compile(r"\b(can'?t breathe|shortness of breath|difficulty breathing)\b", re.IGNORECASE), Severity.CRITICAL, "Patient-reported breathing difficulty"),
    (re.compile(r"\b(unconscious|passed out|blacked out|syncope)\b", re.IGNORECASE), Severity.CRITICAL, "Loss of consciousness reported"),
    (re.compile(r"\b(suicid|want to die|kill myself|end my life)\b", re.IGNORECASE), Severity.CRITICAL, "Suicidal ideation flagged"),
    (re.compile(r"\b(severe bleeding|haemorrhag|hemorrhag)\b", re.IGNORECASE), Severity.CRITICAL, "Severe bleeding reported"),
    (re.compile(r"\banaphylaxis|allergic reaction\b", re.IGNORECASE), Severity.CRITICAL, "Possible allergic reaction"),
    (re.compile(r"\b(overdose|too many|accidentally took)\s+\w+\b", re.IGNORECASE), Severity.CRITICAL, "Possible overdose reported"),
    (re.compile(r"\bstroke symptoms|(face|arm|speech) (droop|slurr|weak)\b", re.IGNORECASE), Severity.CRITICAL, "Possible stroke symptoms"),
    (re.compile(r"\bfalling|fell\b", re.IGNORECASE), Severity.WARN, "Patient reported a fall"),
    (re.compile(r"\b(fever|chills|rigors)\b", re.IGNORECASE), Severity.WARN, "Fever/chills reported — monitor temperature"),
    (re.compile(r"\b(dizzy|dizziness|lightheaded)\b", re.IGNORECASE), Severity.WARN, "Dizziness reported — fall risk"),
    (re.compile(r"\b(swelling|oedema|edema)\b", re.IGNORECASE), Severity.WARN, "Swelling reported — possible fluid retention"),
]


def check_critical_symptoms(text: str) -> SafetyVerdict:
    verdict = SafetyVerdict()
    highest: Severity = Severity.INFO

    for pattern, sev, msg in CRITICAL_KEYWORD_RULES:
        if pattern.search(text):
            verdict.alerts.append(msg)
            if _severity_index(sev) > _severity_index(highest):
                highest = sev

    if verdict.alerts:
        verdict.severity = highest
        verdict.risk_score = _compute_risk_score(highest, len(verdict.alerts))
    return verdict


def evaluate_safety(vitals: dict, message: str) -> SafetyVerdict:
    vital_check = check_vitals(vitals)
    symptom_check = check_critical_symptoms(message)

    alerts = vital_check.alerts + symptom_check.alerts
    if not alerts:
        return SafetyVerdict()

    combined_sev = vital_check.severity
    if _severity_index(symptom_check.severity) > _severity_index(combined_sev):
        combined_sev = symptom_check.severity

    return SafetyVerdict(
        severity=combined_sev,
        alerts=alerts,
        risk_score=max(vital_check.risk_score, symptom_check.risk_score),
    )
