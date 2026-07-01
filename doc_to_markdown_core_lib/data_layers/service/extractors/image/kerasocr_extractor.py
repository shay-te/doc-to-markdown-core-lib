from doc_to_markdown_core_lib.data_layers.service.extractors.image.image_ocr_extractor import (
    ImageOcrExtractor,
)
from doc_to_markdown_core_lib.error_handling.extractor_unavailable import (
    ExtractorUnavailable,
)


class KerasOcrExtractor(ImageOcrExtractor):
    """keras-ocr (``keras_ocr``) — a TensorFlow CRAFT-detector + CRNN-
    recognizer pipeline, an OCR opinion on a stack distinct from the
    PyTorch/ONNX/native engines. English-only; no language config."""

    name = 'keras-ocr'

    def _load_engine(self):
        try:
            import keras_ocr
        except ImportError as import_error:
            raise ExtractorUnavailable('keras-ocr not installed') from import_error
        try:
            return keras_ocr.pipeline.Pipeline()
        except Exception as init_error:
            raise ExtractorUnavailable(
                f'keras-ocr init failed: {init_error}'
            ) from init_error

    def _read_image(self, engine, image_bytes: bytes) -> str:
        import io

        import numpy
        from PIL import Image

        image = numpy.array(Image.open(io.BytesIO(image_bytes)).convert('RGB'))
        # ``recognize`` returns one (word, box) list per input image.
        predictions = engine.recognize([image]) or [[]]
        words = [str(word).strip() for word, _box in predictions[0]]
        return ' '.join(word for word in words if word).strip()
