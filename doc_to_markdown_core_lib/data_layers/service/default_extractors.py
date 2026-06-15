"""Factory for the default extractor lineup.

Lives in its own module so :mod:`document_service` can stay focused on
orchestration logic instead of the 16-import wall every extractor
brings."""
from typing import List, Tuple

from doc_to_markdown_core_lib.data_layers.service.extractor import Extractor
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
