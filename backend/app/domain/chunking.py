import re

from app.domain.models import Chunk, ExtractedPage

HEADINGS = {"SUMMARY", "SKILLS", "EXPERIENCE", "EDUCATION", "LANGUAGES", "CONTACT"}


def chunk_pages(
    pages: list[ExtractedPage], max_chars: int = 1400, overlap: int = 150
) -> list[Chunk]:
    chunks: list[Chunk] = []
    section = "PROFILE"
    for page in pages:
        lines = [re.sub(r"\s+", " ", line).strip() for line in page.text.splitlines()]
        buffer: list[str] = []
        for line in lines:
            if not line:
                continue
            heading = line.upper().rstrip(":")
            if heading in HEADINGS:
                _flush(chunks, buffer, page.number, section, max_chars, overlap)
                buffer = []
                section = heading
            else:
                buffer.append(line)
        _flush(chunks, buffer, page.number, section, max_chars, overlap)
    return chunks


def _flush(
    output: list[Chunk], lines: list[str], page: int, section: str, max_chars: int, overlap: int
) -> None:
    text = "\n".join(lines).strip()
    while text:
        cut = min(len(text), max_chars)
        if cut < len(text):
            boundary = text.rfind(" ", 0, cut)
            cut = boundary if boundary > max_chars // 2 else cut
        part = text[:cut].strip()
        if part:
            output.append(Chunk(text=part, page=page, section=section))
        if cut >= len(text):
            break
        text = text[max(0, cut - overlap) :].strip()
