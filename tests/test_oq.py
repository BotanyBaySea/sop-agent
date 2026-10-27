import json

import pytest

import agent
from audit import log_event
from search import THRESHOLD, load_sections, search

SECTIONS = load_sections()


@pytest.fixture
def fake_llm(monkeypatch):
    def chat(model, messages):
        return {"message": {"content": "Within 4 hours."}}

    monkeypatch.setattr(agent.ollama, "chat", chat)


@pytest.fixture
def temp_log(tmp_path, monkeypatch):
    path = tmp_path / "audit_log.jsonl"

    def logger(*args, **kwargs):
        return log_event(*args, log_path=path, **kwargs)

    monkeypatch.setattr(agent, "log_event", logger)
    return path


def test_oq01_answers_come_only_from_approved_sops():
    """URS-01"""
    sop_texts = {s["text"] for s in SECTIONS}
    r = search("How long is the alcohol contact time?", SECTIONS)
    assert r["answer"] in sop_texts


@pytest.mark.parametrize(
    "question, expected_source",
    [
        ("How long is the alcohol contact time?", "SOP-001 Section 2"),
        ("When do swab samples go to QC?", "SOP-001 Section 3"),
        ("How soon must a deviation be reported to QA?", "SOP-003"),
    ],
)
def test_oq02_answers_cite_correct_source(question, expected_source):
    """URS-02"""
    r = search(question, SECTIONS)
    assert r["source"] is not None
    assert r["source"].startswith(expected_source)


@pytest.mark.parametrize(
    "question",
    ["Who won the Super Bowl?", "What's on the cafeteria menu?", "Can I go to the bathroom?"],
)
def test_oq03_refuses_out_of_scope_questions(question, fake_llm, temp_log):
    """URS-03"""
    r = search(question, SECTIONS)
    assert r["score"] < THRESHOLD
    answer, source = agent.ask(question)
    assert answer == agent.REFUSAL
    assert source is None


def test_oq04_audit_log_records_every_question(fake_llm, temp_log):
    """URS-04"""
    agent.ask("When do swab samples go to QC?")
    agent.ask("Who won the Super Bowl?")

    entries = [json.loads(line) for line in temp_log.read_text().splitlines()]
    assert len(entries) == 2
    for e in entries:
        assert {"timestamp", "question", "answer", "source", "score", "refused"} <= e.keys()
    assert entries[0]["refused"] is False
    assert entries[0]["source"] == "SOP-001 Section 3"
    assert entries[1]["refused"] is True


def test_oq04_audit_log_is_append_only(tmp_path):
    """URS-04"""
    path = tmp_path / "audit_log.jsonl"
    log_event("q1", "a1", "SOP-001 Section 1", 0.5, False, log_path=path)
    log_event("q2", "a2", None, 0.0, True, log_path=path)
    lines = path.read_text().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["question"] == "q1"