from pathlib import Path

import fitz


def test_generated_dataset() -> None:
    paths = sorted((Path(__file__).parents[2] / "data" / "cvs").glob("*.pdf"))
    assert len(paths) == 30
    names = set()
    for path in paths:
        with fitz.open(path) as document:
            text = "".join(page.get_text() for page in document)
        assert all(
            section in text for section in ("SKILLS", "EXPERIENCE", "EDUCATION", "LANGUAGES")
        )
        names.add(text.splitlines()[0])
    assert len(names) == 30
