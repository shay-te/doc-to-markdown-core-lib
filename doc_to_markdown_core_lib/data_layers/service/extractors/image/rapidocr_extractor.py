from doc_to_markdown_core_lib.data_layers.service.extractors.image.image_ocr_extractor import (
    ImageOcrExtractor,
)
from doc_to_markdown_core_lib.error_handling.extractor_unavailable import (
    ExtractorUnavailable,
)


class RapidOcrExtractor(ImageOcrExtractor):
    """Lightweight ONNX OCR (``rapidocr-onnxruntime``) — a third OCR opinion
    that ships its own latin+chinese models, no language config."""

    name = 'rapidocr'

    def _load_engine(self):
        try:
            from rapidocr_onnxruntime import RapidOCR
        except ImportError as import_error:
            raise ExtractorUnavailable(
                'rapidocr-onnxruntime not installed'
            ) from import_error
        return RapidOCR()

    def _read_image(self, engine, image_bytes: bytes) -> str:
        detections, _elapsed = engine(image_bytes)
        if not detections:
            return ''
        return '\n'.join(
            (detection[1] or '').strip()
            for detection in detections
            if len(detection) > 1
        ).strip()
