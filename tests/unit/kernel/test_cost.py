"""Unit tests for kernel.cost."""
import json
from pathlib import Path

import pytest

from agentsuite.kernel.cost import CostCap, CostTracker, HardCapExceeded
from agentsuite.kernel.schema import Cost


def test_tracker_starts_at_zero():
    t = CostTracker(cap=CostCap(soft_warn_usd=1.0, hard_kill_usd=5.0))
    assert t.total.usd == 0.0


def test_tracker_accumulates():
    t = CostTracker(cap=CostCap(soft_warn_usd=1.0, hard_kill_usd=5.0))
    t.add(Cost(input_tokens=100, output_tokens=50, usd=0.5))
    t.add(Cost(input_tokens=200, output_tokens=80, usd=0.3))
    assert t.total.usd == pytest.approx(0.8)


def test_tracker_warns_at_soft_cap():
    t = CostTracker(cap=CostCap(soft_warn_usd=1.0, hard_kill_usd=5.0))
    t.add(Cost(usd=1.5))
    assert t.warned is True


def test_tracker_does_not_warn_below_soft_cap():
    t = CostTracker(cap=CostCap(soft_warn_usd=1.0, hard_kill_usd=5.0))
    t.add(Cost(usd=0.5))
    assert t.warned is False


def test_tracker_raises_at_hard_cap():
    t = CostTracker(cap=CostCap(soft_warn_usd=1.0, hard_kill_usd=5.0))
    with pytest.raises(HardCapExceeded) as exc:
        t.add(Cost(usd=5.5))
    assert "5.5000" in str(exc.value)
    assert "exceed hard cap" in str(exc.value)


def test_cap_loads_from_env(monkeypatch):
    monkeypatch.setenv("AGENTSUITE_COST_CAP_USD", "2.5")
    cap = CostCap.from_env()
    assert cap.hard_kill_usd == pytest.approx(2.5)
    assert cap.soft_warn_usd == pytest.approx(2.5 * 0.2)


def test_cap_uses_default_when_env_missing(monkeypatch):
    monkeypatch.delenv("AGENTSUITE_COST_CAP_USD", raising=False)
    cap = CostCap.from_env()
    assert cap.hard_kill_usd == pytest.approx(5.0)
    assert cap.soft_warn_usd == pytest.approx(1.0)


def test_tracker_handles_zero_cost_runs():
    """Ollama (and other zero-cost providers) accumulate cleanly under cap logic."""
    t = CostTracker(cap=CostCap(soft_warn_usd=1.0, hard_kill_usd=5.0))
    for _ in range(100):
        t.add(Cost(input_tokens=200, output_tokens=80, usd=0.0))
    assert t.total.usd == 0.0
    assert t.total.input_tokens == 200 * 100
    assert t.total.output_tokens == 80 * 100
    assert t.warned is False


def test_hard_cap_does_not_mutate_total_on_overflow():
    """The total must NOT advance when a hard-cap-overflowing add() raises.

    Subsequent retries with the same overflow must continue to raise from
    the same baseline.
    """
    t = CostTracker(cap=CostCap(soft_warn_usd=1.0, hard_kill_usd=5.0))
    t.add(Cost(usd=4.0))
    with pytest.raises(HardCapExceeded):
        t.add(Cost(usd=2.0))
    assert t.total.usd == pytest.approx(4.0)
    with pytest.raises(HardCapExceeded):
        t.add(Cost(usd=2.0))  # second attempt with same overflow
    assert t.total.usd == pytest.approx(4.0)


# --- per-stage telemetry (v0.9.0) ----------------------------------------


def test_per_stage_breakdown_when_current_stage_set():
    """Costs added under a current_stage land in per_stage AND total."""
    t = CostTracker(cap=CostCap(hard_kill_usd=10.0))
    t.current_stage = "intake"
    t.add(Cost(input_tokens=100, output_tokens=50, usd=0.10))
    t.current_stage = "extract"
    t.add(Cost(input_tokens=200, output_tokens=80, usd=0.20))
    t.add(Cost(input_tokens=50, output_tokens=20, usd=0.05))  # second extract call
    assert t.total.usd == pytest.approx(0.35)
    assert t.per_stage["intake"].usd == pytest.approx(0.10)
    assert t.per_stage["extract"].usd == pytest.approx(0.25)
    # Aggregation within a stage sums tokens too.
    assert t.per_stage["extract"].input_tokens == 250
    assert t.per_stage["extract"].output_tokens == 100


def test_per_stage_skipped_when_current_stage_none():
    """Without current_stage set, total still accumulates but per_stage stays empty."""
    t = CostTracker(cap=CostCap(hard_kill_usd=10.0))
    t.add(Cost(usd=0.10))
    assert t.total.usd == pytest.approx(0.10)
    assert t.per_stage == {}


def test_summary_schema_keys():
    """summary() returns the documented schema."""
    t = CostTracker(
        cap=CostCap(hard_kill_usd=5.0),
        run_id="run-abc",
        agent="founder",
        provider="anthropic",
    )
    t.current_stage = "intake"
    t.add(Cost(input_tokens=100, output_tokens=50, usd=0.10, model="claude-sonnet-4-6"))
    s = t.summary()
    assert set(s.keys()) == {
        "run_id", "agent", "provider", "model",
        "stages",
        "total_input_tokens", "total_output_tokens", "total_cost_usd",
        "cap_usd", "cap_remaining_usd", "cap_warned",
    }
    assert s["run_id"] == "run-abc"
    assert s["agent"] == "founder"
    assert s["provider"] == "anthropic"
    assert s["model"] == "claude-sonnet-4-6"
    assert s["total_cost_usd"] == pytest.approx(0.10)
    assert s["cap_usd"] == pytest.approx(5.0)
    assert s["cap_remaining_usd"] == pytest.approx(4.9)
    assert s["cap_warned"] is False
    assert len(s["stages"]) == 1
    assert s["stages"][0]["stage"] == "intake"
    assert s["stages"][0]["cost_usd"] == pytest.approx(0.10)
    assert s["stages"][0]["model"] == "claude-sonnet-4-6"


def test_summary_orders_stages_canonically():
    """stages list follows the canonical Stage Literal order, not insertion order."""
    t = CostTracker(cap=CostCap(hard_kill_usd=10.0))
    # Add in non-canonical order: spec, then intake, then extract.
    for stage in ("spec", "intake", "extract"):
        t.current_stage = stage  # type: ignore[assignment]
        t.add(Cost(usd=0.01))
    stages_in_summary = [row["stage"] for row in t.summary()["stages"]]
    assert stages_in_summary == ["intake", "extract", "spec"]


def test_save_summary_writes_json(tmp_path: Path):
    """save_summary persists the summary dict as JSON, parents created."""
    t = CostTracker(cap=CostCap(hard_kill_usd=5.0), run_id="run-xyz", agent="design")
    t.current_stage = "intake"
    t.add(Cost(input_tokens=10, output_tokens=5, usd=0.01))
    out = tmp_path / "deep" / "nested" / "cost_summary.json"
    t.save_summary(out)
    assert out.exists()
    loaded = json.loads(out.read_text(encoding="utf-8"))
    assert loaded["run_id"] == "run-xyz"
    assert loaded["agent"] == "design"
    assert loaded["total_cost_usd"] == pytest.approx(0.01)


def test_summary_cap_warned_flag_tracks_soft_warn():
    """cap_warned is True once soft_warn is exceeded, False before."""
    t = CostTracker(cap=CostCap(soft_warn_usd=0.5, hard_kill_usd=5.0))
    t.current_stage = "intake"
    t.add(Cost(usd=0.4))
    assert t.summary()["cap_warned"] is False
    t.add(Cost(usd=0.2))  # crosses soft warn
    assert t.summary()["cap_warned"] is True


def test_cost_model_field_last_wins_under_aggregation():
    """Cost.__add__ takes the latest non-None model so summary reflects most recent call."""
    a = Cost(input_tokens=10, output_tokens=5, usd=0.01, model="claude-haiku-4-5-20251001")
    b = Cost(input_tokens=20, output_tokens=8, usd=0.02, model="claude-sonnet-4-6")
    merged = a + b
    assert merged.model == "claude-sonnet-4-6"
    assert merged.usd == pytest.approx(0.03)
    # Single None preserves the other's model.
    c = Cost(usd=0.0)
    assert (a + c).model == "claude-haiku-4-5-20251001"
    assert (c + a).model == "claude-haiku-4-5-20251001"


# --- QA-003: CostCap.from_env() error handling ---------------------------


def test_from_env_raises_on_non_numeric_value(monkeypatch):
    """QA-003: non-numeric AGENTSUITE_COST_CAP_USD raises ValueError with actionable message."""
    monkeypatch.setenv("AGENTSUITE_COST_CAP_USD", "not-a-number")
    with pytest.raises(ValueError) as exc:
        CostCap.from_env()
    msg = str(exc.value)
    assert "AGENTSUITE_COST_CAP_USD" in msg
    assert "not-a-number" in msg
    assert "5.00" in msg  # actionable example in error text


def test_from_env_raises_on_empty_string(monkeypatch):
    """QA-003: empty-string env var also raises ValueError with actionable message."""
    monkeypatch.setenv("AGENTSUITE_COST_CAP_USD", "")
    with pytest.raises(ValueError) as exc:
        CostCap.from_env()
    assert "AGENTSUITE_COST_CAP_USD" in str(exc.value)


def test_from_env_accepts_valid_numeric_string(monkeypatch):
    """QA-003: valid numeric string parses correctly — no exception raised."""
    monkeypatch.setenv("AGENTSUITE_COST_CAP_USD", "10.00")
    cap = CostCap.from_env()
    assert cap.hard_kill_usd == pytest.approx(10.0)
    assert cap.soft_warn_usd == pytest.approx(10.0 * 0.2)


# --- ENG-007: CostCap.from_env() rejects zero and negative values -----------


def test_from_env_raises_on_zero_cap(monkeypatch):
    """ENG-007: zero cap raises ValueError with 'greater than 0' in message."""
    monkeypatch.setenv("AGENTSUITE_COST_CAP_USD", "0")
    with pytest.raises(ValueError) as exc:
        CostCap.from_env()
    assert "greater than 0" in str(exc.value)


def test_from_env_raises_on_negative_cap(monkeypatch):
    """ENG-007: negative cap raises ValueError with 'greater than 0' in message."""
    monkeypatch.setenv("AGENTSUITE_COST_CAP_USD", "-1")
    with pytest.raises(ValueError) as exc:
        CostCap.from_env()
    assert "greater than 0" in str(exc.value)


def test_from_env_accepts_positive_cap(monkeypatch):
    """ENG-007: valid positive cap creates correct CostCap without error."""
    monkeypatch.setenv("AGENTSUITE_COST_CAP_USD", "5.0")
    cap = CostCap.from_env()
    assert cap.hard_kill_usd == pytest.approx(5.0)
    assert cap.soft_warn_usd == pytest.approx(5.0 * 0.2)
