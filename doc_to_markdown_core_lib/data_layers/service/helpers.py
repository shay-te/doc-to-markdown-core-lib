"""Service-level helpers for the extraction pipeline.

Two concerns that :mod:`document_service` leans on but shouldn't be
cluttered with:

* **Pre-flight tiering** (:func:`detect_tier`) — :attr:`Tier.CLEAN` →
  one engine is enough; :attr:`Tier.RISKY` → run the full ensemble.
  PyMuPDF missing → PDFs default to :attr:`Tier.RISKY`.
* **The default extractor lineup** (:func:`build_default_extractors`) —
  kept here so the orchestrator stays focused on orchestration instead
  of the 16-import wall every extractor brings.
"""
from typing import List, Tuple

from doc_to_markdown_core_lib.data_layers.service.extractors.extractor import Extractor
from doc_to_markdown_core_lib.data_layers.service.extractors.doc.soffice_extractor import (
    SofficeExtractor,
)
from doc_to_markdown_core_lib.data_layers.service.extractors.doc.textract_extractor import (
    TextractExtractor,
)
from doc_to_markdown_core_lib.data_layers.service.extractors.docx.docx_extractor import (
    DocxExtractor,
)
from doc_to_markdown_core_lib.data_layers.service.extractors.docx.mammoth_extractor import (
    MammothExtractor,
)
from doc_to_markdown_core_lib.data_layers.service.extractors.image.easyocr_extractor import (
    EasyOcrExtractor,
)
from doc_to_markdown_core_lib.data_layers.service.extractors.image.rapidocr_extractor import (
    RapidOcrExtractor,
)
from doc_to_markdown_core_lib.data_layers.service.extractors.image.tesseract_extractor import (
    TesseractExtractor,
)
from doc_to_markdown_core_lib.data_layers.service.extractors.md.md_extractor import (
    MdExtractor,
)
from doc_to_markdown_core_lib.data_layers.service.extractors.pdf.hybrid_pdf_extractor import (
    HybridPdfExtractor,
)
from doc_to_markdown_core_lib.data_layers.service.extractors.pdf.markitdown_extractor import (
    MarkItDownExtractor,
)
from doc_to_markdown_core_lib.data_layers.service.extractors.pdf.pdfminer_extractor import (
    PdfMinerExtractor,
)
from doc_to_markdown_core_lib.data_layers.service.extractors.pdf.pdfplumber_extractor import (
    PdfPlumberExtractor,
)
from doc_to_markdown_core_lib.data_layers.service.extractors.pdf.pymupdf4llm_extractor import (
    PyMuPdf4LlmExtractor,
)
from doc_to_markdown_core_lib.data_layers.service.extractors.pdf.pymupdf_extractor import (
    PyMuPdfExtractor,
)
from doc_to_markdown_core_lib.data_layers.service.extractors.pdf.pypdf_extractor import (
    PypdfExtractor,
)
from doc_to_markdown_core_lib.data_layers.service.extractors.txt.txt_extractor import (
    TxtExtractor,
)
from doc_to_markdown_core_lib.data_layers.data.file_type import FileType
from doc_to_markdown_core_lib.data_layers.data.tier import Tier

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


def build_default_extractors(
    ocr_languages: Tuple[str, ...],
) -> List[Extractor]:
    """Default lineup, in candidate-fan-out order.

    ``ocr_languages`` uses tesseract codes; easyocr / rapidocr manage
    their own language models internally (see their docstrings)."""
    return [
        MdExtractor(),
        TxtExtractor(),
        DocxExtractor(),
        MammothExtractor(),
        TextractExtractor(),
        SofficeExtractor(),
        HybridPdfExtractor(TesseractExtractor(languages=list(ocr_languages))),
        PyMuPdfExtractor(),
        PdfPlumberExtractor(),
        PdfMinerExtractor(),
        PypdfExtractor(),
        PyMuPdf4LlmExtractor(),
        MarkItDownExtractor(),
        TesseractExtractor(languages=list(ocr_languages)),
        EasyOcrExtractor(),
        RapidOcrExtractor(),
    ]
