import os
import shutil
import subprocess
import tempfile

from doc_to_markdown_core_lib.data_layers.service.confidence_norms import (
    CONFIDENCE_DOCUMENT_CHARS_NORM,
)
from doc_to_markdown_core_lib.data_layers.service.extraction_candidate import (
    ExtractionCandidate,
)
from doc_to_markdown_core_lib.data_layers.service.extractor import Extractor
from doc_to_markdown_core_lib.data_layers.service.extractor_unavailable import (
    ExtractorUnavailable,
)
from doc_to_markdown_core_lib.data_layers.service.file_type import FileType

_SOFFICE_TIMEOUT_SECONDS = 120

# The conversion hop (doc → docx → markdown) can drop formatting at
# either step, so the score is discounted versus direct extractors.
_CONVERSION_HOP_CONFIDENCE_DISCOUNT = 0.85


class SofficeExtractor(Extractor):
    """LibreOffice (``soffice --headless``) converts ``.doc`` →
    ``.docx``; the structured docx is the real payload, handed off to
    ``mammoth``. Without ``mammoth`` installed the candidate is empty
    (zero confidence) and loses the vote. Needs the ``soffice`` binary
    on PATH."""

    name = 'soffice'
    file_types = (FileType.DOC, FileType.DOCX)

    def extract(self, content: bytes, file_type: FileType) -> ExtractionCandidate:
        binary = shutil.which('soffice') or shutil.which('libreoffice')
        if binary is None:
            raise ExtractorUnavailable('soffice / libreoffice binary not found')

        suffix = f'.{file_type.value}'
        with tempfile.TemporaryDirectory() as work_dir:
            input_path = os.path.join(work_dir, f'input{suffix}')
            with open(input_path, 'wb') as input_file:
                input_file.write(content)
            try:
                subprocess.run(
                    [
                        binary, '--headless', '--convert-to', FileType.DOCX.value,
                        '--outdir', work_dir, input_path,
                    ],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=_SOFFICE_TIMEOUT_SECONDS,
                )
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as run_error:
                raise ExtractorUnavailable(
                    f'soffice conversion failed: {run_error}'
                ) from run_error

            docx_path = os.path.join(work_dir, f'input.{FileType.DOCX.value}')
            if not os.path.exists(docx_path):
                raise ExtractorUnavailable('soffice produced no output file')
            with open(docx_path, 'rb') as docx_file:
                docx_bytes = docx_file.read()

        try:
            import mammoth
            import io
            result = mammoth.convert_to_markdown(io.BytesIO(docx_bytes))
            markdown = (result.value or '').strip()
        except ImportError:
            markdown = ''

        confidence = (
            min(1.0, max(0.0, len(markdown) / CONFIDENCE_DOCUMENT_CHARS_NORM))
            * _CONVERSION_HOP_CONFIDENCE_DISCOUNT
        )
        return ExtractionCandidate(
            extractor=self.name,
            markdown=markdown,
            confidence=confidence,
            languages=[],
        )
