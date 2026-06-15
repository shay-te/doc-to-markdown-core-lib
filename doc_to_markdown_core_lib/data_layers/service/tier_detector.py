"""Pre-flight tiering. :attr:`Tier.CLEAN` → one engine is enough;
:attr:`Tier.RISKY` → run the full ensemble. PyMuPDF missing → PDFs
default to :attr:`Tier.RISKY`."""
from doc_to_markdown_core_lib.data_layers.service.file_type import FileType
from doc_to_markdown_core_lib.data_layers.service.tier import Tier

_TEXT_LAYER_CHAR_FLOOR = 100  # avg chars/page above this → clean

_CLEAN_TIER_TYPES = (FileType.TXT, FileType.MD, FileType.DOCX)


def detect_tier(content: bytes, file_type: FileType) -> Tier:
    # ``FileType`` is exhaustive, so the enum-strict signature removes
    # the old string-era unknown-type fallback. Every member lands in
    # one of the three branches below.
    if file_type in _CLEAN_TIER_TYPES:
        return Tier.CLEAN
    if file_type == FileType.PDF:
        return _detect_pdf_tier(content)
    return Tier.RISKY


def _detect_pdf_tier(content: bytes) -> Tier:
    try:
        import fitz  # PyMuPDF
    except ImportError:
        return Tier.RISKY
    try:
        doc = fitz.open(stream=content, filetype=FileType.PDF.value)
    except Exception:
        return Tier.RISKY
    try:
        pages = len(doc)
        if pages == 0:
            return Tier.RISKY
        total = sum(len(page.get_text() or '') for page in doc)
        if (total / pages) > _TEXT_LAYER_CHAR_FLOOR:
            return Tier.CLEAN
        return Tier.RISKY
    finally:
        doc.close()
