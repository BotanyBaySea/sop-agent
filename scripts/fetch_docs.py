"""Download public FDA/WHO guidance PDFs and convert them into section files for the SOP search index."""
import io
import re
from pathlib import Path

import requests
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent.parent
SOP_DIR = ROOT / "sops"
MIN_WORDS = 40
MAX_WORDS = 180

DOCUMENTS = [
    {
        "id": "FDA-DI-2018",
        "title": "FDA Data Integrity and Compliance With Drug CGMP: Questions and Answers (2018)",
        "url": "https://www.fda.gov/media/119267/download",
        "file": "FDA-DI-2018_Data_Integrity_QA.txt",
    },
    {
        "id": "FDA-P11-2003",
        "title": "FDA Part 11, Electronic Records; Electronic Signatures: Scope and Application (2003)",
        "url": "https://www.fda.gov/media/75414/download",
        "file": "FDA-P11-2003_Part11_Scope.txt",
        "line_numbers": True,
    },
    {
        "id": "WHO-DI-2021",
        "title": "WHO TRS 1033 Annex 4: Guideline on Data Integrity (2021)",
        "url": "https://cdn.who.int/media/docs/default-source/medicines/norms-and-standards/guidelines/inspections/trs1033-annex4-guideline-on-data-integrity.pdf",
        "file": "WHO-DI-2021_Data_Integrity.txt",
    },
]


def download_pdf(url):
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=60)
    response.raise_for_status()
    return PdfReader(io.BytesIO(response.content))


def clean_page(text, line_numbers=False):
    lines = []
    for line in text.splitlines():
        line = line.strip()
        if line_numbers:
            line = re.sub(r"\s+\d{1,3}$", "", line)
        if not line or re.fullmatch(r"\d+", line) or re.fullmatch(r"(Page )?\d+ of \d+", line):
            continue
        if line.lower().startswith("contains nonbinding recommendations"):
            continue
        lines.append(line)
    return "\n".join(lines)


def to_paragraphs(text):
    text = re.sub(r"-\n(\w)", r"\1", text)
    text = re.sub(r"(?<![.:;?!])\n(?=[a-z(])", " ", text)
    blocks = re.split(r"\n(?=(?:\d+(?:\.\d+)*\.?\s+[A-Z])|(?:[A-Z]\.\s)|(?:•))|(?<=[.:?])\n", text)
    return [" ".join(b.split()) for b in blocks if b.strip()]


def chunk(paragraphs):
    chunks, current = [], []
    for para in paragraphs:
        words = para.split()
        if current and len(current) + len(words) > MAX_WORDS:
            chunks.append(" ".join(current))
            current = []
        current.extend(words)
        if len(current) >= MIN_WORDS and para.endswith((".", "?")):
            chunks.append(" ".join(current))
            current = []
    if current:
        if chunks and len(current) < MIN_WORDS:
            chunks[-1] += " " + " ".join(current)
        else:
            chunks.append(" ".join(current))
    return chunks


def is_boilerplate(section):
    if re.search(r"\.{6,}|(?:\. ){6,}", section):
        return True
    if "Department of Health and Human Services" in section:
        return True
    return bool(re.search(r"(?:\b\d+\.\s+[A-Z][a-z]+(?:\s+[a-z]+){0,3}\s+\d{3}\s+){3,}", section))


def build(doc):
    reader = download_pdf(doc["url"])
    text = "\n".join(clean_page(page.extract_text() or "", doc.get("line_numbers", False)) for page in reader.pages)
    sections = [s for s in chunk(to_paragraphs(text)) if not is_boilerplate(s)]
    lines = [f"{doc['id']} {doc['title']}", f"Source URL: {doc['url']}"]
    lines += [f"Section {i}: {s}" for i, s in enumerate(sections, start=1)]
    (SOP_DIR / doc["file"]).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(sections)


if __name__ == "__main__":
    SOP_DIR.mkdir(exist_ok=True)
    for doc in DOCUMENTS:
        count = build(doc)
        print(f"{doc['id']}: {count} sections -> sops/{doc['file']}")