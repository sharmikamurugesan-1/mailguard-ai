"""Tests for reliability module, uncertain band, and warning heuristics (Phase 6)."""

import pytest
from src.reliability import (
    check_non_english,
    compute_reliability,
    evaluate_decision,
    get_uncertain_high,
    get_uncertain_low,
)


def test_injected_probabilities_uncertain_band():
    """Verify that probabilities within [0.40, 0.60] return 'uncertain'."""
    pred, label, risk, conf = evaluate_decision(0.50)
    assert pred == "uncertain"
    assert label == "Needs review"
    assert risk == "medium"
    assert conf == 0.50

    pred, label, risk, conf = evaluate_decision(0.40)
    assert pred == "uncertain"
    assert label == "Needs review"

    pred, label, risk, conf = evaluate_decision(0.60)
    assert pred == "uncertain"
    assert label == "Needs review"


def test_injected_probabilities_outside_band():
    """Verify decisive classifications outside the uncertain band."""
    # High spam probability
    pred, label, risk, conf = evaluate_decision(0.85)
    assert pred == "spam"
    assert label == "Likely spam"
    assert risk == "high"
    assert conf == 0.85

    # Low spam probability
    pred, label, risk, conf = evaluate_decision(0.15)
    assert pred == "ham"
    assert label == "Likely legitimate"
    assert risk == "low"
    assert conf == 0.85


def test_no_unsafe_terminology():
    """Verify no label ever contains 'safe' or '100%'."""
    for p in [0.0, 0.05, 0.20, 0.50, 0.80, 0.99, 1.0]:
        pred, label, risk, conf = evaluate_decision(p)
        assert "safe" not in label.lower()
        assert "100%" not in label


def test_warning_code_near_decision_boundary():
    """near_decision_boundary triggers when spam probability is in [0.35, 0.65]."""
    res_inside = compute_reliability(
        spam_probability=0.45,
        text="This is a standard email with many legitimate words discussing our weekly meeting agenda.",
    )
    assert "near_decision_boundary" in res_inside["warnings"]

    res_outside = compute_reliability(
        spam_probability=0.95,
        text="This is a standard email with many legitimate words discussing our weekly meeting agenda.",
    )
    assert "near_decision_boundary" not in res_outside["warnings"]


def test_warning_code_short_input():
    """short_input triggers when input contains fewer than 10 tokens."""
    res = compute_reliability(
        spam_probability=0.10,
        text="Quick note.",
    )
    assert "short_input" in res["warnings"]


def test_warning_code_low_vocab_coverage():
    """low_vocab_coverage triggers when less than 50% of tokens are in vectorizer vocabulary."""
    class DummyVectorizer:
        vocabulary_ = {"known": 0, "word": 1}

    # 12 tokens, only 2 known
    gibberish_text = "known word xyza qwerty asdfgh zxcvbn poiu lkjd mnbvc qazwsx edcrfv tgbyhn"
    res = compute_reliability(
        spam_probability=0.10,
        text=gibberish_text,
        vectorizer=DummyVectorizer(),
    )
    assert "low_vocab_coverage" in res["warnings"]


def test_warning_code_non_english():
    """non_english_suspected triggers when share of non-ASCII characters is high."""
    non_ascii_text = "Привет, это важное сообщение о встрече на следующей неделе в Москве."
    assert check_non_english(non_ascii_text)

    res = compute_reliability(
        spam_probability=0.20,
        text=non_ascii_text,
    )
    assert "non_english_suspected" in res["warnings"]


def test_dataset_age_notice_is_persistent():
    """dataset_age_notice is always present for the Enron-era model."""
    res = compute_reliability(spam_probability=0.10, text="Standard text for checking persistent notice.")
    assert "dataset_age_notice" in res["warnings"]


def test_reliability_levels():
    """Test high, medium, and low reliability levels based on warning count."""
    # 0 data warnings -> high
    res_high = compute_reliability(
        spam_probability=0.95,
        text="This is an extensive legitimate email discussing project schedules, deliverables, and team assignments for tomorrow.",
    )
    assert res_high["level"] == "high"

    # 1 data warning (e.g. short input only) -> medium
    res_med = compute_reliability(
        spam_probability=0.95,
        text="Short email.",
    )
    assert res_med["level"] == "medium"

    # 2 data warnings (e.g. short input + near decision boundary) -> low
    res_low = compute_reliability(
        spam_probability=0.50,
        text="Short boundary.",
    )
    assert res_low["level"] == "low"


def test_thresholds_change_with_env_vars(monkeypatch):
    """Verify that changing env vars modifies uncertain band thresholds."""
    monkeypatch.setenv("UNCERTAIN_LOW", "0.30")
    monkeypatch.setenv("UNCERTAIN_HIGH", "0.70")

    assert get_uncertain_low() == 0.30
    assert get_uncertain_high() == 0.70

    # 0.35 is now inside the [0.30, 0.70] band
    pred, label, risk, conf = evaluate_decision(0.35)
    assert pred == "uncertain"
    assert label == "Needs review"

    # 0.25 is outside
    pred, label, risk, conf = evaluate_decision(0.25)
    assert pred == "ham"
