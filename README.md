# SOP Question-Answering Agent (Validated RAG)

![OQ Tests](https://github.com/BotanyBaySea/sop-agent/actions/workflows/tests.yml/badge.svg)

A retrieval-augmented AI agent that answers questions about Standard Operating Procedures using only approved SOP text, cites the source section for every answer, refuses out-of-scope questions, and records every interaction in an append-only audit log. Built and validated using GxP computer system validation practices. Created by Travis Marks.

## How it works
1. **Retrieve:** TF-IDF search finds the SOP section that best matches the question.
2. **Refuse:** if the best match scores below 0.2, the agent declines to answer.
3. **Generate:** a locally hosted Llama 3.2 model (via Ollama) writes the answer using only the retrieved passage.
4. **Record:** the question, answer, source, score, and timestamp are appended to `logs/audit_log.jsonl`.

All processing runs locally. No SOP content or questions leave the machine.

## Validation
| Requirement | Test |
|---|---|
| URS-01 Answers only from approved SOPs | `test_oq01_answers_come_only_from_approved_sops` |
| URS-02 Every answer cites its source | `test_oq02_answers_cite_correct_source` |
| URS-03 Refuses below relevance threshold | `test_oq03_refuses_out_of_scope_questions` |
| URS-04 Append-only audit log | `test_oq04_audit_log_*` |

Full requirements: [docs/URS.md](docs/URS.md). Tests run automatically on every push through GitHub Actions.

## Run it
```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
ollama pull llama3.2
python src/agent.py
pytest -v
```

## Tech
Python, scikit-learn, Ollama (Llama 3.2), pytest, GitHub Actions

## Path to Production

This is a real working prototype. It proves the core controls (approved-source answers, citations, refusal, audit trail, automated OQ) on public guidance. A production deployment in a regulated company would add:

- **Document management system integration:** connect to the existing repository (such as OpenText, Veeva, or MasterControl) through its API, index only current *Effective* versions, and re-index automatically when a document changes. Teams get cited answers in seconds instead of searching and reading full SOPs.
- **Access control and Part 11:** single sign-on, role-based permissions so users only see answers from documents they can open, and audit trails that meet 21 CFR Part 11.
- **Validated hosting:** a qualified server or private cloud environment under change control.
- **Full CSV lifecycle:** risk assessment, IQ/OQ/PQ, a larger golden question set, and periodic review.
- **Monitoring:** tracking of refusal rates, score drift, and user-flagged wrong answers.