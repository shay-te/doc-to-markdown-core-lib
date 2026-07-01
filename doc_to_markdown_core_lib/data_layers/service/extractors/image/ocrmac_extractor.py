from doc_to_markdown_core_lib.data_layers.service.extractors.image.image_ocr_extractor import (
    ImageOcrExtractor,
)
from doc_to_markdown_core_lib.error_handling.extractor_unavailable import (
    ExtractorUnavailable,
)


class OcrMacExtractor(ImageOcrExtractor):
    """Apple Vision OCR via ``ocrmac`` — the macOS-native Vision framework
    (no model download, fast, high quality), a distinct opinion on Macs.
    Unavailable off macOS / without the ``ocrmac`` package."""

    name = 'ocrmac'

    def _load_engine(self):
        try:
            from ocrmac import ocrmac
        except ImportError as import_error:
            raise ExtractorUnavailable('ocrmac not installed') from import_error
        return ocrmac

    def _read_image(self, engine, image_bytes: bytes) -> str:
        import io

        from PIL import Image

        image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        annotations = engine.OCR(image).recognize() or []
        lines = [str(annotation[0]).strip() for annotation in annotations]
        return '\n'.join(line for line in lines if line).strip()
