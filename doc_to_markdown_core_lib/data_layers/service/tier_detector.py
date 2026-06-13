"""Pre-flight tiering. ``clean`` → one engine is enough; ``risky``
→ run the full ensemble. PyMuPDF missing → PDFs default to ``risky``."""
from doc_to_markdown_core_lib.data_layers.service.file_type import FileType

_TEXT_LAYER_CHAR_FLOOR = 100  # avg chars/page above this → clean

_CLEAN_TIER_TYPES = (FileType.TXT, FileType.MD, FileType.DOCX)


def detect_tier(content: bytes, file_type: FileType) -> str:
    """Return ``'clean'`` or ``'risky'``."""
    # ``FileType`` is exhaustive, so the enum-strict signature removes
    # the old string-era unknown-type fallback. Every member lands in
    # one of the three branches below.
    if file_type in _CLEAN_TIER_TYPES:
        return 'clean'
    if file_type == FileType.PDF:
        return _detect_pdf_tier(content)
    return 'risky'


def _detect_pdf_tier(content: bytes) -> str:
    try:
        import fitz  # PyMuPDF
    except ImportError:
        return 'risky'
    try:
        doc = fitz.open(stream=content, filetype=FileType.PDF.value)
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
