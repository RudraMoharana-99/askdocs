import re

# A line that is only digits, or "Chapter 4  ·  87" style running headers.
_PAGE_ARTIFACT = re.compile(r"^\s*(\d{1,4}|[A-Z][A-Za-z ]{0,40}\s+\d{1,4})\s*$", re.MULTILINE)  # Matches page numbers and running headers.

# Word split across a line break: "attent-\nion" -> "attention".
_HYPHEN_BREAK = re.compile(r"(\w)-\n(\w)")

# A single newline INSIDE a paragraph (not a blank-line paragraph break).
# Lookarounds ensure we never collapse "\n\n".
_SOFT_WRAP = re.compile(r"(?<!\n)\n(?!\n)")

# Back-matter headings, matched only as a standalone line.
_BACK_MATTER = re.compile(
    r"^\s*(references|bibliography|index)\s*$", re.IGNORECASE | re.MULTILINE
)

# Book section heading on its own line: "3.2 Self-Attention".
_HEADING_LINE = re.compile(r"^(\d+(?:\.\d+)*)\s+([A-Z][^\n]{2,80})$", re.MULTILINE)

# Watermarks and other per-page boilerplate.
_WATERMARK = re.compile(r"^\s*(OceanofPDF\.com|www\.\S+)\s*$", re.MULTILINE)

def _protect_headings(text: str) -> str:
    """Wrap headings in blank lines so the soft-wrap collapse can't absorb
    them into the following paragraph — which would destroy the line-anchored
    signal the chunker needs to detect sections."""
    return _HEADING_LINE.sub(lambda m: f"\n\n{m.group(0)}\n\n", text)


def clean_pdf_text(text: str) -> str:
    text = _WATERMARK.sub("", text)
    text = _PAGE_ARTIFACT.sub("", text)
    text = _HYPHEN_BREAK.sub(r"\1\2", text)
    text = _protect_headings(text)
    text = _SOFT_WRAP.sub(" ", text)
    text = re.sub(r"[ \t]{2,}", " ", text)  # collapse extraction padding
    return re.sub(r"\n{3,}", "\n\n", text).strip()  # normalise paragraph gaps


def strip_back_matter(text: str) -> str:
    """Drop bibliography/index, which is retrieval noise.

    Heuristic: only cut if the heading appears in the last 30% of the text.
    Guards against a chapter that merely *discusses* references being truncated.
    """
    cutoff = int(len(text) * 0.7)
    for match in _BACK_MATTER.finditer(text):
        if match.start() >= cutoff:
            return text[: match.start()].strip()
    return text