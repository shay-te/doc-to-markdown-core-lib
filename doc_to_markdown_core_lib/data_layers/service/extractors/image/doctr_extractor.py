from doc_to_markdown_core_lib.data_layers.service.extractors.image.image_ocr_extractor import (
    ImageOcrExtractor,
)
from doc_to_markdown_core_lib.error_handling.extractor_unavailable import (
    ExtractorUnavailable,
)


class DocTrExtractor(ImageOcrExtractor):
    """docTR (``python-doctr``) — Mindee's deep-learning detect+recognize OCR,
    a modern high-accuracy opinion on a stack distinct from tesseract/easyocr.
    Auto-detects script; no language config."""

    name = 'doctr'

    def _load_engine(self):
        try:
            from doctr.models import ocr_predictor
        except ImportError as import_error:
            raise ExtractorUnavailable('python-doctr not installed') from import_error
        try:
            return ocr_predictor(pretrained=True)
        except Exception as init_error:
            raise ExtractorUnavailable(
                f'doctr init failed: {init_error}'
            ) from init_error

    def _read_image(self, engine, image_bytes: bytes) -> str:
        from doctr.io import DocumentFile

        document = DocumentFile.from_images(image_bytes)
        result = engine(document)
        return (result.render() or '').strip()
