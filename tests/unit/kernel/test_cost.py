"""Unit tests for kernel.cost."""
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
