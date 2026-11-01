# Model Card: SOP Agent (Validated RAG Prototype)

## Overview
A retrieval-augmented question-answering agent that answers questions only from approved regulatory guidance documents, cites the exact section used, refuses when no approved section is a confident match, and records every interaction in an append-only audit log. Built as a working prototype to show how GxP validation principles apply to generative AI.

## Intended Use
- Quickly locating and summarizing guidance on data integrity and electronic records in GMP environments.
- Demonstrating requirements-driven validation (URS → OQ tests → CI) for an AI system.

**Not intended for:** making GMP decisions without human review, answering questions outside the approved documents, or use as a validated production system.

## Components
| Component | Detail |
|---|---|
| Retrieval | Semantic search with `nomic-embed-text` embeddings (Ollama), cosine similarity |
| Refusal threshold | 0.65 similarity; below this, the agent refuses |
| Answer generation | `llama3.2` via Ollama, run locally; prompt restricts answers to the retrieved passage |
| Audit log | Append-only JSONL: UTC timestamp, user, question, answer, source, document version hash, score, refused flag |
| Runtime | Fully local; no data leaves the machine |

## Approved Documents
| ID | Document |
|---|---|
| FDA-DI-2018 | FDA Data Integrity and Compliance With Drug CGMP: Questions and Answers (2018) |
| FDA-P11-2003 | FDA Part 11, Electronic Records; Electronic Signatures: Scope and Application (2003) |
| WHO-DI-2021 | WHO TRS 1033 Annex 4: Guideline on Data Integrity (2021) |

Documents are downloaded from their public sources by `scripts/fetch_docs.py` and split into 216 sections. Each section carries a SHA-256 version hash of its source file.

## Performance (OQ results)
| Test | Result |
|---|---|
| In-scope questions answered with the correct cited section | 5 / 5 (scores 0.78–0.88) |
| Off-topic questions refused | 3 / 3 (scores 0.48–0.52) |
| Answered and refused interactions logged, log only grows | Pass |
| Margin check | Answers must score ≥ 0.75 and refusals ≤ 0.55, so drift is caught before it crosses the threshold |

All tests run on every push in GitHub Actions against a real Ollama instance.

## Known Limitations
- Retrieves a single best section; answers spanning several sections may be incomplete.
- Threshold was set on a small question set; a production system needs a much larger golden set.
- The language model can still paraphrase imperfectly; outputs require human review.
- Source documents are public guidance, not controlled site SOPs.

## Version Control
Model, threshold, and documents are fixed in code. Any change to them is made through a commit and must pass the OQ suite in CI before merge.