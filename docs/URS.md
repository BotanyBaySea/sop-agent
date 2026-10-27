# User Requirements Specification — SOP Question-Answering Agent

| Field | Value |
|---|---|
| Document ID | URS-SOPAGENT-001 |
| Version | 1.0 |
| System | SOP RAG Agent (local LLM, retrieval-augmented) |
| Owner | Travis Marks |

## 1. Purpose
Allow operators to ask plain-language questions about approved Standard Operating Procedures and receive answers grounded only in those SOPs, with a citation to the source section.

## 2. Scope
In scope: retrieval from approved SOP text files, answer generation by a locally hosted model, citation, refusal, and audit logging.
Out of scope: editing SOPs, training the model, and any use as a replacement for the controlled SOP itself.

## 3. Requirements

| ID | Requirement | Verified by |
|---|---|---|
| URS-01 | The system shall answer only from approved SOP documents stored in `sops/`. | OQ-01 |
| URS-02 | Every answer shall cite the source SOP number and section. | OQ-02 |
| URS-03 | The system shall refuse to answer when no SOP passage meets the relevance threshold (0.2). | OQ-03 |
| URS-04 | Every question shall be recorded in an append-only audit log with timestamp, question, answer, source, and score. | OQ-04 |
| URS-05 | All processing shall run locally; no SOP content or questions shall be sent to external services. | Design review (Ollama local model) |
| URS-06 | Requirements URS-01 to URS-04 shall be verified by automated tests before each release. | GitHub Actions CI |

## 4. Data Integrity (ALCOA+)
The audit log is attributable (timestamped entries), legible (JSON Lines), contemporaneous (written at time of question), original (append-only), and accurate (records the exact retrieved source and score).