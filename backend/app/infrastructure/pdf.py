from pathlib import Path

import fitz  # type: ignore[import-untyped]

from app.domain.models import ExtractedPage


class PyMuPdfExtractor:
    def extract(self, path: Path) -> list[ExtractedPage]:
        try:
            with fitz.open(path) as document:
                return [
                    ExtractedPage(i + 1, page.get_text("text")) for i, page in enumerate(document)
                ]
        except (fitz.FileDataError, RuntimeError) as exc:
            raise ValueError(f"Could not read PDF {path.name}") from exc
