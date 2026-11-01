"""Semantic search over approved SOP sections using Ollama embeddings."""
import hashlib
import json
from pathlib import Path

import numpy as np
import ollama

ROOT = Path(__file__).resolve().parent.parent
SOP_DIR = ROOT / "sops"
CACHE_FILE = ROOT / ".cache" / "embeddings.json"
MODEL = "nomic-embed-text"
THRESHOLD = 0.65


def load_sections(folder=SOP_DIR):
    """Return every section of every approved document as {'source', 'text'}."""
    sections = []
    for path in sorted(Path(folder).glob("*.txt")):
        lines = path.read_text(encoding="utf-8").splitlines()
        sop_id = lines[0].split()[0]
        for line in lines[1:]:
            if line.startswith("Section ") and ":" in line:
                label, text = line.split(":", 1)
                sections.append({"source": f"{sop_id} {label.strip()}", "text": text.strip()})
    return sections


def _key(text):
    return hashlib.sha256(f"{MODEL}\n{text}".encode("utf-8")).hexdigest()


def _embed(texts):
    vectors = np.array(ollama.embed(model=MODEL, input=texts)["embeddings"], dtype=np.float32)
    return vectors / np.linalg.norm(vectors, axis=1, keepdims=True)


def _load_cache():
    if CACHE_FILE.exists():
        return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    return {}


def section_vectors(sections):
    """Return normalized document embeddings, embedding only sections missing from the cache."""
    cache = _load_cache()
    keys = [_key(s["text"]) for s in sections]
    missing = [i for i, k in enumerate(keys) if k not in cache]
    for start in range(0, len(missing), 32):
        batch = missing[start:start + 32]
        vectors = _embed([f"search_document: {sections[i]['text']}" for i in batch])
        for i, vector in zip(batch, vectors):
            cache[keys[i]] = [round(float(x), 6) for x in vector]
    if missing:
        CACHE_FILE.parent.mkdir(exist_ok=True)
        CACHE_FILE.write_text(json.dumps(cache), encoding="utf-8")
    return np.array([cache[k] for k in keys], dtype=np.float32)


def rank(question, sections):
    """Return (index, score) pairs for all sections, best first."""
    query = _embed([f"search_query: {question}"])[0]
    scores = section_vectors(sections) @ query
    order = np.argsort(scores)[::-1]
    return [(int(i), float(scores[i])) for i in order]


def search(question, sections):
    """Return the best-matching section, or answer None when the match is below THRESHOLD."""
    best, score = rank(question, sections)[0]
    source = sections[best]["source"]
    if score < THRESHOLD:
        return {"answer": None, "source": source, "score": score}
    return {"answer": sections[best]["text"], "source": source, "score": score}