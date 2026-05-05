import pytest
from pydantic import ValidationError

from prompt_vett.schemas.analysis import AnalysisReport, DimensionAnalysis
from prompt_vett.schemas.quality import QualityScore
from prompt_vett.schemas.request import EvaluateRequest
from prompt_vett.schemas.rewrite import RewriteResult


# ── EvaluateRequest ──────────────────────────────────────────────────────────


def test_evaluate_request_valid() -> None:
    req = EvaluateRequest(
        prompt="You are a helpful assistant.",
        test_messages=["Hello", "What is 2+2?"],
        model="gemini-2.5-flash",
    )
    assert req.byok_key is None
    assert len(req.test_messages) == 2


def test_evaluate_request_byok_none() -> None:
    req = EvaluateRequest(
        prompt="p",
        test_messages=["m"],
        byok_key=None,
        model="gemini-2.5-pro",
    )
    assert req.byok_key is None


def test_evaluate_request_byok_set() -> None:
    req = EvaluateRequest(
        prompt="p",
        test_messages=["m"],
        byok_key="sk-abc",
        model="gemini-2.5-flash",
    )
    assert req.byok_key == "sk-abc"


def test_evaluate_request_empty_prompt_rejected() -> None:
    with pytest.raises(ValidationError):
        EvaluateRequest(prompt="", test_messages=["m"], model="gemini-2.5-flash")


def test_evaluate_request_empty_test_messages_rejected() -> None:
    with pytest.raises(ValidationError):
        EvaluateRequest(prompt="p", test_messages=[], model="gemini-2.5-flash")


def test_evaluate_request_too_many_test_messages_rejected() -> None:
    with pytest.raises(ValidationError):
        EvaluateRequest(
            prompt="p",
            test_messages=[f"msg {i}" for i in range(21)],
            model="gemini-2.5-flash",
        )


def test_evaluate_request_invalid_model_rejected() -> None:
    with pytest.raises(ValidationError):
        EvaluateRequest(prompt="p", test_messages=["m"], model="gpt-4o")  # type: ignore[arg-type]


# ── DimensionAnalysis ────────────────────────────────────────────────────────


def test_dimension_analysis_valid() -> None:
    d = DimensionAnalysis(score=7, findings=["clear instructions"], severity="medium")
    assert d.score == 7


def test_dimension_analysis_score_negative_rejected() -> None:
    with pytest.raises(ValidationError):
        DimensionAnalysis(score=-1, findings=[], severity="low")


def test_dimension_analysis_score_over_ten_rejected() -> None:
    with pytest.raises(ValidationError):
        DimensionAnalysis(score=11, findings=[], severity="high")


def test_dimension_analysis_invalid_severity_rejected() -> None:
    with pytest.raises(ValidationError):
        DimensionAnalysis(score=5, findings=[], severity="critical")  # type: ignore[arg-type]


# ── AnalysisReport ───────────────────────────────────────────────────────────


def _make_dimension(**kwargs: object) -> DimensionAnalysis:
    return DimensionAnalysis(score=5, findings=[], severity="low", **kwargs)  # type: ignore[arg-type]


def test_analysis_report_valid() -> None:
    report = AnalysisReport(
        quality=_make_dimension(),
        consistency=_make_dimension(),
        injection_resistance=_make_dimension(),
        edge_cases=_make_dimension(),
    )
    assert report.quality.score == 5


def test_analysis_report_missing_field_rejected() -> None:
    with pytest.raises(ValidationError):
        AnalysisReport(  # type: ignore[call-arg]
            quality=_make_dimension(),
            consistency=_make_dimension(),
            injection_resistance=_make_dimension(),
            # edge_cases missing
        )


# ── RewriteResult ────────────────────────────────────────────────────────────


def test_rewrite_result_valid() -> None:
    r = RewriteResult(
        improved_prompt="You are an expert assistant.",
        change_summary=["Clarified role", "Removed ambiguity"],
        rationale="The original was vague.",
    )
    assert len(r.change_summary) == 2


def test_rewrite_result_empty_improved_prompt_rejected() -> None:
    with pytest.raises(ValidationError):
        RewriteResult(improved_prompt="", change_summary=["x"], rationale="r")


def test_rewrite_result_empty_change_summary_rejected() -> None:
    with pytest.raises(ValidationError):
        RewriteResult(improved_prompt="p", change_summary=[], rationale="r")


def test_rewrite_result_empty_rationale_rejected() -> None:
    with pytest.raises(ValidationError):
        RewriteResult(improved_prompt="p", change_summary=["x"], rationale="")


# ── QualityScore ─────────────────────────────────────────────────────────────


def test_quality_score_valid() -> None:
    q = QualityScore(
        overall=8,
        dimensions={"clarity": 9, "safety": 7},
        verdict="accept",
        reasoning="Solid prompt with minor issues.",
    )
    assert q.overall == 8


def test_quality_score_overall_negative_rejected() -> None:
    with pytest.raises(ValidationError):
        QualityScore(overall=-1, dimensions={}, verdict="accept", reasoning="r")


def test_quality_score_overall_over_ten_rejected() -> None:
    with pytest.raises(ValidationError):
        QualityScore(overall=11, dimensions={}, verdict="revise", reasoning="r")


def test_quality_score_dimension_value_over_ten_rejected() -> None:
    with pytest.raises(ValidationError):
        QualityScore(
            overall=5, dimensions={"clarity": 11}, verdict="accept", reasoning="r"
        )


def test_quality_score_dimension_value_negative_rejected() -> None:
    with pytest.raises(ValidationError):
        QualityScore(
            overall=5, dimensions={"clarity": -1}, verdict="revise", reasoning="r"
        )


def test_quality_score_invalid_verdict_rejected() -> None:
    with pytest.raises(ValidationError):
        QualityScore(overall=5, dimensions={}, verdict="maybe", reasoning="r")  # type: ignore[arg-type]


def test_quality_score_empty_reasoning_rejected() -> None:
    with pytest.raises(ValidationError):
        QualityScore(overall=5, dimensions={}, verdict="accept", reasoning="")
