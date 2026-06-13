from typing import List, Optional

from doc_to_markdown_core_lib.data_layers.service.types import (
    CONFIDENCE_DOCUMENT_CHARS_NORM,
    CONFIDENCE_SINGLE_IMAGE_CHARS_NORM,
    ExtractionCandidate,
    Extractor,
    ExtractorUnavailable,
    FileType,
)


class TesseractExtractor(Extractor):
    """OCR fallback for scans/images. Wrong language pack → line noise,
    so configure ``ocr_languages`` to match the corpora you receive.
    PDFs are rasterized via PyMuPDF; missing PyMuPDF → unavailable."""

    name = 'tesseract'
    file_types = (FileType.PDF.value, FileType.IMAGE.value)

    def __init__(self, languages: Optional[List[str]] = None, dpi: int = 200):
        self._languages = list(languages or ['eng'])
        self._dpi = dpi

    def extract(self, content: bytes, file_type: str) -> ExtractionCandidate:
        try:
            import io

            import pytesseract
            from PIL import Image
        except ImportError as import_error:
            raise ExtractorUnavailable(
                'pytesseract / Pillow not installed'
            ) from import_error

        lang_arg = '+'.join(self._languages)

        if file_type == FileType.IMAGE.value:
            img = Image.open(io.BytesIO(content))
            text = (pytesseract.image_to_string(img, lang=lang_arg) or '').strip()
            confidence = min(
                1.0,
                max(0.0, len(text) / CONFIDENCE_SINGLE_IMAGE_CHARS_NORM),
            )
            return ExtractionCandidate(
                extractor=self.name,
                markdown=text,
                confidence=confidence,
                languages=list(self._languages),
            )

        if file_type == FileType.PDF.value:
            try:
                import fitz
            except ImportError as import_error:
                raise ExtractorUnavailable(
                    'PyMuPDF (fitz) required to rasterize PDF pages for tesseract'
                ) from import_error

            parts = []
            doc = fitz.open(stream=content, filetype='pdf')
            try:
                for page_number, page in enumerate(doc, start=1):
                    pix = page.get_pixmap(dpi=self._dpi)
                    img = Image.open(io.BytesIO(pix.tobytes('png')))
                    text = (pytesseract.image_to_string(img, lang=lang_arg) or '').strip()
                    parts.append(f'<!-- page {page_number} -->\n\n{text}')
            finally:
                doc.close()

            markdown = '\n\n'.join(parts).strip()
            confidence = min(
                1.0,
                max(0.0, len(markdown) / CONFIDENCE_DOCUMENT_CHARS_NORM),
            )
            return ExtractionCandidate(
                extractor=self.name,
                markdown=markdown,
                confidence=confidence,
                languages=list(self._languages),
            )

        raise ValueError(f'tesseract cannot handle file_type={file_type!r}')
