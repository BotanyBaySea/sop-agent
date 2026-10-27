import ollama
from search import load_sections, search

def ask(question, sections):
    r = search(question, sections)
    if r["answer"] is None:
        return "Not found in the SOPs.", None
    prompt = (
        "Answer the question using ONLY the SOP text below. "
        "If the text does not answer it, say 'Not found in the SOPs.'\n\n"
        f"SOP text ({r['source']}): {r['answer']}\n\n"
        f"Question: {question}"
    )
    reply = ollama.chat(model="llama3.2", messages=[{"role": "user", "content": prompt}])
    return reply["message"]["content"], r["source"]

if __name__ == "__main__":
    secs = load_sections()
    while True:
        q = input("\nAsk a question (or 'quit'): ")
        if q == "quit":
            break
        answer, source = ask(q, secs)
        print(answer)
        if source:
            print(f"  Source: {source}")