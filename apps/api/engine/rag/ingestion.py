"""RAG — PDF ingestion and chunking for Harrison's Medicine."""

import re
from dataclasses import dataclass, field
from pathlib import Path

try:
    import fitz  # PyMuPDF
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False


@dataclass
class Chunk:
    text: str
    metadata: dict = field(default_factory=dict)


# Patterns for detecting chapter headings
CHAPTER_PATTERN = re.compile(
    r"(?:^|\n)\s*(?:CHAPTER|Chapter|PART|Part|SECTION|Section)\s+(\d+)\s*[:\-–—]?\s*(.+)",
    re.MULTILINE,
)


def load_harrison_pdf(path: str | Path) -> list[dict]:
    """Load Harrison's PDF and return a list of {page_num, text} dicts."""
    if not HAS_FITZ:
        raise RuntimeError("PyMuPDF (fitz) is required for PDF ingestion. Install with: pip install PyMuPDF")

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")

    doc = fitz.open(str(path))
    pages = []
    for i, page in enumerate(doc):
        text = page.get_text("text")
        if text.strip():
            pages.append({"page_num": i + 1, "text": text})
    doc.close()
    return pages


def detect_chapters(pages: list[dict]) -> list[dict]:
    """Detect chapter boundaries from page text.

    Returns list of {chapter_num, chapter_title, start_page, end_page, pages_text}.
    """
    chapters: list[dict] = []
    current_chapter = {
        "chapter_num": 0,
        "chapter_title": "Front Matter",
        "start_page": 1,
        "pages_text": [],
    }

    for page in pages:
        text = page["text"]
        match = CHAPTER_PATTERN.search(text[:500])  # Check first 500 chars
        if match:
            # Save previous chapter
            if current_chapter["pages_text"]:
                current_chapter["end_page"] = page["page_num"] - 1
                chapters.append(current_chapter)

            current_chapter = {
                "chapter_num": int(match.group(1)) if match.group(1).isdigit() else 0,
                "chapter_title": match.group(2).strip(),
                "start_page": page["page_num"],
                "pages_text": [text],
            }
        else:
            current_chapter["pages_text"].append(text)

    # Don't forget the last chapter
    if current_chapter["pages_text"]:
        current_chapter["end_page"] = pages[-1]["page_num"] if pages else 0
        chapters.append(current_chapter)

    return chapters


def chunk_text(
    text: str,
    max_tokens: int = 700,
    overlap_tokens: int = 100,
    metadata: dict | None = None,
) -> list[Chunk]:
    """Split text into overlapping chunks of approximate token size.

    Uses word-based splitting (~0.75 words per token approximation).
    """
    words = text.split()
    max_words = int(max_tokens * 0.75)
    overlap_words = int(overlap_tokens * 0.75)

    if not words:
        return []

    chunks = []
    start = 0
    while start < len(words):
        end = min(start + max_words, len(words))
        chunk_words = words[start:end]
        chunk_text = " ".join(chunk_words)

        if chunk_text.strip():
            chunk_meta = dict(metadata or {})
            chunk_meta["word_start"] = start
            chunk_meta["word_end"] = end
            chunks.append(Chunk(text=chunk_text, metadata=chunk_meta))

        start = end - overlap_words if end < len(words) else len(words)

    return chunks


def ingest_pdf(path: str | Path) -> list[Chunk]:
    """Full ingestion pipeline: PDF → pages → chapters → chunks with metadata."""
    pages = load_harrison_pdf(path)
    chapters = detect_chapters(pages)

    all_chunks: list[Chunk] = []

    # Map clinical domains by keywords in chapter titles
    domain_keywords = {
        "hematology": ["anemia", "blood", "hematolog", "iron", "coagul", "platelet", "leukemia", "lymphoma"],
        "nephrology": ["kidney", "renal", "nephr", "glomerul", "dialysis", "electrolyte"],
        "endocrinology": ["diabetes", "thyroid", "adrenal", "pituitary", "endocrin", "metabol"],
        "hepatology": ["liver", "hepat", "biliary", "cirrhosis", "jaundice"],
        "cardiology": ["heart", "cardiac", "coronary", "arrhythmia", "hypertension", "lipid", "cholesterol"],
        "gastroenterology": ["gastro", "intestin", "pancrea", "esophag", "colon"],
        "rheumatology": ["arthrit", "autoimmune", "lupus", "rheumat", "inflammat"],
        "pulmonology": ["lung", "pulmon", "respirat", "asthma", "pneumon"],
        "neurology": ["brain", "neuro", "seizure", "stroke", "dement"],
        "oncology": ["cancer", "tumor", "oncol", "malignan", "neoplas"],
        "infectious_disease": ["infect", "bacteria", "virus", "fungal", "antibiotic", "HIV", "tuberculosis"],
    }

    for chapter in chapters:
        full_text = "\n".join(chapter["pages_text"])
        title_lower = chapter["chapter_title"].lower()

        # Detect clinical domain
        clinical_domain = "general"
        for domain, keywords in domain_keywords.items():
            if any(kw in title_lower for kw in keywords):
                clinical_domain = domain
                break

        base_meta = {
            "chapter_num": chapter["chapter_num"],
            "chapter_title": chapter["chapter_title"],
            "start_page": chapter["start_page"],
            "end_page": chapter.get("end_page", chapter["start_page"]),
            "clinical_domain": clinical_domain,
            "section_type": "chapter",
        }

        chunks = chunk_text(full_text, max_tokens=700, overlap_tokens=100, metadata=base_meta)
        for i, chunk in enumerate(chunks):
            chunk.metadata["chunk_index"] = i
            chunk.metadata["total_chunks"] = len(chunks)

        all_chunks.extend(chunks)

    return all_chunks
