import ollama

from audit import log_event
from search import load_sections, search

MODEL = "llama3.2"
REFUSAL = "I can't answer that from the approved SOPs."
SECTIONS = load_sections()


def ask(question):
    r = search(question, SECTIONS)

    if r["answer"] is None:
        log_event(question, REFUSAL, None, r.get("score"), refused=True)
        return REFUSAL, None

    prompt = (
        "Answer the question using ONLY the SOP passage below. "
        "If the passage does not contain the answer, say you don't know.\n\n"
        f"Passage ({r['source']}):\n{r['answer']}\n\n"
        f"Question: {question}"
    )
    response = ollama.chat(model=MODEL, messages=[{"role": "user", "content": prompt}])
    answer = response["message"]["content"].strip()

    log_event(question, answer, r["source"], r.get("score"), refused=False)
    return answer, r["source"]


if __name__ == "__main__":
    while True:
        q = input("\nAsk about an SOP (or 'quit'): ").strip()
        if q.lower() in ("quit", "exit", ""):
            break
        answer, source = ask(q)
        print(f"\n{answer}")
        if source:
            print(f"Source: {source}")