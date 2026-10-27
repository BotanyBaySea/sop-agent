from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

THRESHOLD = 0.2
SOP_DIR = Path(__file__).resolve().parent.parent / "sops"


def load_sections(folder=SOP_DIR):
    sections = []
    for file in sorted(Path(folder).glob("*.txt")):
        lines = file.read_text(encoding="utf-8").splitlines()
        sop_id = lines[0].split()[0]
        for line in lines[1:]:
            if line.startswith("Section"):
                num, text = line.split(":", 1)
                sections.append({"source": f"{sop_id} {num}", "text": text.strip()})
    return sections


def search(question, sections):
    texts = [s["text"] for s in sections]
    vec = TfidfVectorizer(stop_words="english").fit(texts + [question])
    scores = cosine_similarity(vec.transform([question]), vec.transform(texts))[0]
    best = scores.argmax()
    score = float(scores[best])
    if score < THRESHOLD:
        return {"answer": None, "source": None, "score": score}
    return {"answer": sections[best]["text"], "source": sections[best]["source"], "score": score}


if __name__ == "__main__":
    secs = load_sections()
    while True:
        q = input("\nAsk a question (or 'quit'): ").strip()
        if q.lower() == "quit":
            break
        r = search(q, secs)
        if r["answer"] is None:
            print(f"Not found in the SOPs. (score {r['score']:.2f})")
        else:
            print(f"{r['answer']}\n  Source: {r['source']}  (score {r['score']:.2f})")