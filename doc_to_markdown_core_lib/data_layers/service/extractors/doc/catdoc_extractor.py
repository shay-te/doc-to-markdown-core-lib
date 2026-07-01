import os
import shutil
import subprocess
import tempfile

from doc_to_markdown_core_lib.constants import CONFIDENCE_DOCUMENT_CHARS_NORM
from doc_to_markdown_core_lib.data_layers.data.extraction.extraction_candidate import (
    ExtractionCandidate,
)
from doc_to_markdown_core_lib.data_layers.service.extractors.extractor import Extractor
from doc_to_markdown_core_lib.error_handling.extractor_unavailable import (
    ExtractorUnavailable,
)
from doc_to_markdown_core_lib.data_layers.data.file_type import FileType

_CATDOC_TIMEOUT_SECONDS = 60

# Plain-text dump loses structure, so it scores below format-aware extractors.
_PLAIN_TEXT_CONFIDENCE_DISCOUNT = 0.7


class CatdocExtractor(Extractor):
    """``catdoc`` reads legacy ``.doc`` to plain text with a decoder distinct
    from antiword — a different failure profile on damaged/odd files. Needs
    the ``catdoc`` binary on PATH."""

    name = 'catdoc'
    file_types = (FileType.DOC,)

    def extract(self, content: bytes, file_type: FileType) -> ExtractionCandidate:
        binary = shutil.which('catdoc')
        if binary is None:
            raise ExtractorUnavailable('catdoc binary not found')

        with tempfile.NamedTemporaryFile(
            suffix=f'.{FileType.DOC.value}', delete=False
        ) as temp_file:
            temp_file.write(content)
            temp_path = temp_file.name
        try:
            try:
                completed = subprocess.run(
                    [binary, temp_path],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    timeout=_CATDOC_TIMEOUT_SECONDS,
                )
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as run_error:
                raise ExtractorUnavailable(
                    f'catdoc failed: {run_error}'
                ) from run_error
        finally:
            try:
                os.unlink(temp_path)
            except OSError:
                pass

        markdown = completed.stdout.decode('utf-8', errors='replace').strip()
        confidence = (
            min(1.0, max(0.0, len(markdown) / CONFIDENCE_DOCUMENT_CHARS_NORM))
            * _PLAIN_TEXT_CONFIDENCE_DISCOUNT
        )
        return ExtractionCandidate(
            extractor=self.name,
            markdown=markdown,
            confidence=confidence,
            languages=[],
        )
