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
        "Answer the question using ONLY the SOP passage below.\n"
        "If the passage covers the topic, answer directly from it, even if it uses a related term, "
        "an expanded form, or different wording than the question.\n"
        "State the answer itself. Do not comment on whether the passage answers the question.\n"
        "Say you don't know only if the passage contains nothing relevant to the question.\n\n"
        f"Passage ({r['source']}):\n{r['answer']}\n\n"
        f"Question: {question}"
    )
    response = ollama.chat(model=MODEL, messages=[{"role": "user", "content": prompt}])
    answer = response["message"]["content"].strip()

    log_event(question, answer, r["source"], r.get("score"), refused=False, doc_version=r.get("doc_version"))
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