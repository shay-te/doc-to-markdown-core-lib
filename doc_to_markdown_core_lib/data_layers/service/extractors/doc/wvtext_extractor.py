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

_WVTEXT_TIMEOUT_SECONDS = 60

# Plain-text dump loses structure, so it scores below format-aware extractors.
_PLAIN_TEXT_CONFIDENCE_DISCOUNT = 0.7


class WvTextExtractor(Extractor):
    """``wvText`` (wvware) — the classic Word 6/8 ``.doc`` reader, a decoder
    lineage distinct from antiword/catdoc. It writes plain text to an output
    file (not stdout). Needs the ``wvText`` binary on PATH."""

    name = 'wvtext'
    file_types = (FileType.DOC,)

    def extract(self, content: bytes, file_type: FileType) -> ExtractionCandidate:
        binary = shutil.which('wvText')
        if binary is None:
            raise ExtractorUnavailable('wvText binary not found')

        with tempfile.TemporaryDirectory() as work_dir:
            input_path = os.path.join(work_dir, f'input.{FileType.DOC.value}')
            output_path = os.path.join(work_dir, 'output.txt')
            with open(input_path, 'wb') as input_file:
                input_file.write(content)
            try:
                subprocess.run(
                    [binary, input_path, output_path],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=_WVTEXT_TIMEOUT_SECONDS,
                )
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as run_error:
                raise ExtractorUnavailable(
                    f'wvText failed: {run_error}'
                ) from run_error
            try:
                with open(
                    output_path, 'r', encoding='utf-8', errors='replace'
                ) as output_file:
                    markdown = output_file.read().strip()
            except OSError as read_error:
                raise ExtractorUnavailable(
                    f'wvText produced no output: {read_error}'
                ) from read_error

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
