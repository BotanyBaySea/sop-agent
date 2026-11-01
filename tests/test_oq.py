"""OQ tests for the SOP agent, traced to URS-SOPAGENT-001, run against public FDA/WHO guidance."""
import functools
import json

import pytest

import agent
import audit
from search import THRESHOLD, load_sections, search

SECTIONS = load_sections()
DOC_IDS = ("FDA-DI-2018", "FDA-P11-2003", "WHO-DI-2021")
MARGIN = 0.10


class FakeResponse(dict):
    def __init__(self, content):
        super().__init__(message={"content": content})
        self.message = type("Message", (), {"content": content})()


class FakeOllama:
    def chat(self, *args, **kwargs):
        return FakeResponse("FAKE ANSWER")

    def generate(self, *args, **kwargs):
        return {"response": "FAKE ANSWER"}


@pytest.fixture
def fake_llm(monkeypatch):
    monkeypatch.setattr(agent, "ollama", FakeOllama())


@pytest.fixture
def temp_log(tmp_path, monkeypatch):
    log_file = tmp_path / "audit_log.jsonl"
    monkeypatch.setattr(agent, "log_event", functools.partial(audit.log_event, log_path=log_file))
    return log_file


def read_log(log_file):
    return [json.loads(line) for line in log_file.read_text(encoding="utf-8").splitlines()]


def test_oq01_sections_come_only_from_approved_documents():
    assert len(SECTIONS) > 100
    assert all(s["source"].startswith(DOC_IDS) for s in SECTIONS)


@pytest.mark.parametrize(
    "question, expected_source",
    [
            ("Why is FDA concerned with shared login accounts?", "FDA-DI-2018 Section 32"),
        ("How should blank forms be controlled?", "FDA-DI-2018 Section 34"),
        ("Are audit trails important even if predicate rules don't require documenting the date, time, or sequence of events?", "FDA-P11-2003 Section 31"),
        ("What is data governance?", "WHO-DI-2021 Section 14"),
        ("What does ALCOA mean?", "WHO-DI-2021 Section 7"),
    ],
)
def test_oq02_answers_cite_the_correct_section(question, expected_source):
    result = search(question, SECTIONS)
    assert result["answer"] is not None
    assert result["source"] == expected_source
    assert result["score"] >= THRESHOLD + MARGIN


@pytest.mark.parametrize(
    "question",
    [
        "How do I bake sourdough bread?",
        "What is the weather in Kalamazoo tomorrow?",
        "Who won the World Series?",
    ],
)
def test_oq03_off_topic_questions_are_refused(question):
    result = search(question, SECTIONS)
    assert result["answer"] is None
    assert result["score"] <= THRESHOLD - MARGIN


def test_oq04_answered_question_is_logged(fake_llm, temp_log):
    answer, source = agent.ask("Why is FDA concerned with shared login accounts?")
    entry = read_log(temp_log)[-1]
    assert entry["refused"] is False
    assert entry["source"] == source
    assert entry["answer"] == answer
    assert entry["timestamp"]
    assert entry["user"]
    assert len(entry["doc_version"]) == 12


def test_oq04_refused_question_is_logged_and_log_only_grows(fake_llm, temp_log):
    agent.ask("Why is FDA concerned with shared login accounts?")
    agent.ask("How do I bake sourdough bread?")
    entries = read_log(temp_log)
    assert len(entries) == 2
    assert entries[0]["refused"] is False
    assert entries[1]["refused"] is True