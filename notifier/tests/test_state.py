import tempfile
from pathlib import Path
import pytest

from notifier import state


@pytest.fixture
def temp_state_file(monkeypatch):
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        tmp_path = Path(f.name)
    monkeypatch.setattr(state, "STATE_FILE", tmp_path)
    yield tmp_path
    if tmp_path.exists():
        tmp_path.unlink()
    tmp_path.with_suffix(".tmp").unlink(missing_ok=True)


def test_mark_sent_is_idempotent(temp_state_file):
    key = "alert_patient_123_amber"
    assert not state.already_sent(key)

    state.mark_sent(key, "2026-09-19T00:00:00Z")
    assert state.already_sent(key)

    # Calling mark_sent again does not cause errors or corruption
    state.mark_sent(key, "2026-09-19T00:01:00Z")
    assert state.already_sent(key)


def test_ledger_trims_at_max_entries(temp_state_file, monkeypatch):
    monkeypatch.setattr(state, "MAX_ENTRIES", 5)

    for i in range(10):
        state.mark_sent(f"key_{i}", f"2026-09-19T00:0{i:02d}:00Z")

    # Only the newest 5 should remain
    data = state._load()
    assert len(data["sent"]) == 5
    for i in range(5):
        assert not state.already_sent(f"key_{i}")
    for i in range(5, 10):
        assert state.already_sent(f"key_{i}")
