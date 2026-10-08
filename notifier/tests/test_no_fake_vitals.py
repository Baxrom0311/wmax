from __future__ import annotations

from notifier.ai_assistant import build_system_prompt
from notifier.telegram import format_doctor_alert, format_relative_alert


def test_system_prompt_never_invents_vitals():
    prompt = build_system_prompt("Bemor", {})
    for fabricated in ("86 bpm", "92%", "1840", "Dr. Bahrom Alimov", "YIK"):
        assert fabricated not in prompt


def test_alert_templates_escape_names():
    assert "<script>" not in format_relative_alert("<script>", "", "red")
    text = format_doctor_alert("A&B", 70, "<Xiva>", "dx", "", {}, "id")
    assert "A&amp;B" in text and "&lt;Xiva&gt;" in text
