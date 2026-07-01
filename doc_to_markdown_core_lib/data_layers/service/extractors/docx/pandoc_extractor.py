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

_PANDOC_TIMEOUT_SECONDS = 90


class PandocExtractor(Extractor):
    """``pandoc`` converts DOCX straight to GitHub-flavored Markdown, keeping
    headings, lists and tables — the strongest structured-markdown opinion in
    the DOCX pool. Needs the ``pandoc`` binary on PATH."""

    name = 'pandoc'
    file_types = (FileType.DOCX,)

    def extract(self, content: bytes, file_type: FileType) -> ExtractionCandidate:
        binary = shutil.which('pandoc')
        if binary is None:
            raise ExtractorUnavailable('pandoc binary not found')

        with tempfile.NamedTemporaryFile(
            suffix=f'.{FileType.DOCX.value}', delete=False
        ) as temp_file:
            temp_file.write(content)
            temp_path = temp_file.name
        try:
            try:
                completed = subprocess.run(
                    [binary, temp_path, '-f', 'docx', '-t', 'gfm', '--wrap=none'],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    timeout=_PANDOC_TIMEOUT_SECONDS,
                )
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as run_error:
                raise ExtractorUnavailable(
                    f'pandoc failed: {run_error}'
                ) from run_error
        finally:
            try:
                os.unlink(temp_path)
            except OSError:
                pass

        # Structured Markdown (not a plain dump), so no plain-text discount.
        markdown = completed.stdout.decode('utf-8', errors='replace').strip()
        confidence = min(1.0, max(0.0, len(markdown) / CONFIDENCE_DOCUMENT_CHARS_NORM))
        return ExtractionCandidate(
            extractor=self.name,
            markdown=markdown,
            confidence=confidence,
            languages=[],
        )
