"""Pre-flight tiering. ``clean`` → one engine is enough; ``risky``
→ run the full ensemble. PyMuPDF missing → PDFs default to ``risky``."""

_TEXT_LAYER_CHAR_FLOOR = 100  # avg chars/page above this → clean


def detect_tier(content: bytes, file_type: str) -> str:
    """Return ``'clean'`` or ``'risky'``."""
    ft = (file_type or '').lower()
    if ft in ('txt', 'md', 'docx'):
        return 'clean'
    if ft == 'image':
        return 'risky'
    if ft == 'pdf':
        return _detect_pdf_tier(content)
    return 'risky'


def _detect_pdf_tier(content: bytes) -> str:
    try:
        import fitz  # PyMuPDF
    except ImportError:
        return 'risky'
    try:
        doc = fitz.open(stream=content, filetype='pdf')
    except Exception:
        return 'risky'
    try:
        pages = len(doc)
        if pages == 0:
            return 'risky'
        total = sum(len(page.get_text() or '') for page in doc)
        return 'clean' if (total / pages) > _TEXT_LAYER_CHAR_FLOOR else 'risky'
    finally:
        doc.close()
