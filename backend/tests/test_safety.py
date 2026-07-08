from __future__ import annotations

import pytest
from backend.core.safety import (
    Severity,
    SafetyVerdict,
    _Threshold,
    _compute_risk_score,
    _severity_index,
    check_critical_symptoms,
    check_vitals,
    evaluate_safety,
)


# ─── Severity helpers ─────────────────────────────────────────────────


class TestSeverityIndex:
    def test_info_is_zero(self):
        assert _severity_index(Severity.INFO) == 0

    def test_warn_is_one(self):
        assert _severity_index(Severity.WARN) == 1

    def test_critical_is_two(self):
        assert _severity_index(Severity.CRITICAL) == 2


class TestComputeRiskScore:
    def test_info_returns_zero(self):
        assert _compute_risk_score(Severity.INFO, 0) == 0.0

    def test_warn_single_borderline(self):
        assert _compute_risk_score(Severity.WARN, 1) == 3.0

    def test_warn_multiple_borderline_increases(self):
        score = _compute_risk_score(Severity.WARN, 3)
        assert score == 3.0 + 2 * 1.5  # base + compound

    def test_critical_single(self):
        assert _compute_risk_score(Severity.CRITICAL, 1) == 8.0

    def test_capped_at_ten(self):
        score = _compute_risk_score(Severity.CRITICAL, 10)
        assert score == 10.0


# ─── Threshold checks ────────────────────────────────────────────────


class TestThresholdCheck:
    def test_within_normal_returns_none(self):
        t = _Threshold(label="HR", warn_min=50, warn_max=110, crit_min=40, crit_max=140)
        sev, msg = t.check(72)
        assert sev is None
        assert msg == ""

    def test_exceeds_crit_max(self):
        t = _Threshold(label="BP", warn_min=None, warn_max=160, crit_min=None, crit_max=180)
        sev, msg = t.check(185)
        assert sev == Severity.CRITICAL
        assert "185" in msg

    def test_below_crit_min(self):
        t = _Threshold(label="SpO2", warn_min=94, warn_max=None, crit_min=90, crit_max=None)
        sev, msg = t.check(88)
        assert sev == Severity.CRITICAL
        assert "88" in msg

    def test_exceeds_warn_max(self):
        t = _Threshold(label="Temp", warn_min=None, warn_max=38.0, crit_min=None, crit_max=39.5)
        sev, msg = t.check(38.5)
        assert sev == Severity.WARN
        assert "38.5" in msg

    def test_below_warn_min(self):
        t = _Threshold(label="HR", warn_min=50, warn_max=110, crit_min=40, crit_max=140)
        sev, msg = t.check(48)
        assert sev == Severity.WARN
        assert "48" in msg

    def test_crit_takes_priority_over_warn(self):
        t = _Threshold(label="HR", warn_min=50, warn_max=110, crit_min=40, crit_max=140)
        sev, msg = t.check(150)
        assert sev == Severity.CRITICAL


# ─── check_vitals ─────────────────────────────────────────────────────


class TestCheckVitals:
    def test_normal_vitals_no_alerts(self):
        result = check_vitals({"systolic_bp": 120, "heart_rate": 72, "sp_o2": 98, "temperature": 36.8})
        assert result.severity == Severity.INFO
        assert result.alerts == []
        assert result.risk_score == 0.0

    def test_warn_level_systolic_bp(self):
        result = check_vitals({"systolic_bp": 165})
        assert result.severity == Severity.WARN
        assert len(result.alerts) == 1
        assert result.risk_score > 0

    def test_critical_level_systolic_bp(self):
        result = check_vitals({"systolic_bp": 185})
        assert result.severity == Severity.CRITICAL

    def test_critical_heart_rate_low(self):
        result = check_vitals({"heart_rate": 35})
        assert result.severity == Severity.CRITICAL

    def test_warn_oxygen_saturation(self):
        result = check_vitals({"sp_o2": 92})
        assert result.severity == Severity.WARN

    def test_critical_oxygen_saturation(self):
        result = check_vitals({"sp_o2": 88})
        assert result.severity == Severity.CRITICAL

    def test_multiple_borderline_increases_risk(self):
        result = check_vitals({"systolic_bp": 165, "heart_rate": 115, "sp_o2": 92})
        assert result.severity == Severity.WARN
        assert len(result.alerts) == 3
        assert result.risk_score > 3.0

    def test_highest_severity_wins(self):
        result = check_vitals({"systolic_bp": 185, "heart_rate": 115})
        assert result.severity == Severity.CRITICAL
        assert len(result.alerts) == 2

    def test_empty_vitals(self):
        result = check_vitals({})
        assert result.severity == Severity.INFO
        assert result.alerts == []

    def test_none_vitals_skipped(self):
        result = check_vitals({"systolic_bp": None, "heart_rate": 72})
        assert result.severity == Severity.INFO


# ─── check_critical_symptoms ──────────────────────────────────────────


class TestCheckCriticalSymptoms:
    def test_normal_message_no_alerts(self):
        result = check_critical_symptoms("I feel fine today, thank you")
        assert result.severity == Severity.INFO
        assert result.alerts == []

    def test_severe_chest_pain(self):
        result = check_critical_symptoms("I have severe chest pain")
        assert result.severity == Severity.CRITICAL
        assert any("chest pain" in a.lower() for a in result.alerts)

    def test_breathing_difficulty(self):
        result = check_critical_symptoms("I can't breathe")
        assert result.severity == Severity.CRITICAL

    def test_shortness_of_breath(self):
        result = check_critical_symptoms("shortness of breath")
        assert result.severity == Severity.CRITICAL

    def test_loss_of_consciousness(self):
        result = check_critical_symptoms("I passed out earlier")
        assert result.severity == Severity.CRITICAL

    def test_suicidal_ideation(self):
        result = check_critical_symptoms("I want to die")
        assert result.severity == Severity.CRITICAL

    def test_severe_bleeding(self):
        result = check_critical_symptoms("severe bleeding from wound")
        assert result.severity == Severity.CRITICAL

    def test_anaphylaxis(self):
        result = check_critical_symptoms("anaphylaxis reaction")
        assert result.severity == Severity.CRITICAL

    def test_overdose(self):
        result = check_critical_symptoms("I accidentally took too many pills")
        assert result.severity == Severity.CRITICAL

    def test_stroke_symptoms(self):
        result = check_critical_symptoms("face droop and speech slurr")
        assert result.severity == Severity.CRITICAL

    def test_fall_warn(self):
        result = check_critical_symptoms("I fell down yesterday")
        assert result.severity == Severity.WARN

    def test_fever_warn(self):
        result = check_critical_symptoms("I have fever and chills")
        assert result.severity == Severity.WARN

    def test_dizziness_warn(self):
        result = check_critical_symptoms("feeling dizzy")
        assert result.severity == Severity.WARN

    def test_swelling_warn(self):
        result = check_critical_symptoms("noticeable swelling in legs")
        assert result.severity == Severity.WARN

    def test_case_insensitive(self):
        result = check_critical_symptoms("SEVERE CHEST PAIN")
        assert result.severity == Severity.CRITICAL

    def test_multiple_symptoms_highest_wins(self):
        result = check_critical_symptoms("I fell and now have severe chest pain")
        assert result.severity == Severity.CRITICAL
        assert len(result.alerts) >= 2


# ─── evaluate_safety (combined) ──────────────────────────────────────


class TestEvaluateSafety:
    def test_normal_vitals_and_message(self):
        result = evaluate_safety({"systolic_bp": 120}, "I feel fine")
        assert result.severity == Severity.INFO
        assert result.alerts == []

    def test_warn_vitals_and_normal_message(self):
        result = evaluate_safety({"systolic_bp": 165}, "I feel fine")
        assert result.severity == Severity.WARN

    def test_normal_vitals_critical_message(self):
        result = evaluate_safety({"systolic_bp": 120}, "I can't breathe")
        assert result.severity == Severity.CRITICAL

    def test_both_contribute_alerts(self):
        result = evaluate_safety({"systolic_bp": 165}, "I feel dizzy")
        assert result.severity == Severity.WARN
        assert len(result.alerts) == 2

    def test_critical_overrides_warn(self):
        result = evaluate_safety({"systolic_bp": 165}, "severe chest pain")
        assert result.severity == Severity.CRITICAL
        assert len(result.alerts) == 2

    def test_risk_score_uses_max(self):
        result = evaluate_safety({"systolic_bp": 165}, "I feel dizzy")
        # warn vitals = 3.0, warn symptom = 3.0, max = 3.0
        assert result.risk_score == 3.0

    def test_empty_inputs(self):
        result = evaluate_safety({}, "")
        assert result.severity == Severity.INFO
        assert result.alerts == []
        assert result.risk_score == 0.0
