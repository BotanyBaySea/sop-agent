from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

THRESHOLD = 0.2  # below this score = refuse

def load_sections(folder="sops"):
    sections = []
    for file in sorted(Path(folder).glob("*.txt")):
        lines = file.read_text().splitlines()
        sop_id = lines[0].split()[0]          # e.g. "SOP-001"
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
    if scores[best] < THRESHOLD:          
        return {"answer": None, "source": None, "score": float(scores[best])}
    return {"answer": sections[best]["text"], "source": sections[best]["source"],  # blank 2: which key holds the citation?
            "score": float(scores[best])}

if __name__ == "__main__":
    secs = load_sections()
    while True:
        q = input("\nAsk a question (or 'quit'): ")
        if q == "quit":
            break
        r = search(q, secs)
        if r["answer"] is None:
            print(f"Not found in the SOPs. (score {r['score']:.2f})")
        else:
            print(f"{r['answer']}\n  Source: {r['source']}  (score {r['score']:.2f})")