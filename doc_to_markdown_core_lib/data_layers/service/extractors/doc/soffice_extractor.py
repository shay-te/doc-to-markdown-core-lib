import os
import shutil
import subprocess
import tempfile

from doc_to_markdown_core_lib.data_layers.service.types import (
    ExtractionCandidate,
    Extractor,
    ExtractorUnavailable,
)


class SofficeExtractor(Extractor):
    """LibreOffice (``soffice --headless``) converts ``.doc`` →
    ``.docx``; the structured docx is the real payload, so we then
    hand off to ``mammoth`` if available, else a raw text dump. Needs
    the ``soffice`` binary on PATH."""

    name = 'soffice'
    file_types = ('doc', 'docx')

    def extract(self, content: bytes, file_type: str) -> ExtractionCandidate:
        binary = shutil.which('soffice') or shutil.which('libreoffice')
        if binary is None:
            raise ExtractorUnavailable('soffice / libreoffice binary not found')

        suffix = '.doc' if file_type == 'doc' else '.docx'
        with tempfile.TemporaryDirectory() as work_dir:
            input_path = os.path.join(work_dir, f'input{suffix}')
            with open(input_path, 'wb') as input_file:
                input_file.write(content)
            try:
                subprocess.run(
                    [
                        binary, '--headless', '--convert-to', 'docx',
                        '--outdir', work_dir, input_path,
                    ],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=120,
                )
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as run_error:
                raise ExtractorUnavailable(
                    f'soffice conversion failed: {run_error}'
                ) from run_error

            docx_path = os.path.join(work_dir, 'input.docx')
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

        confidence = min(1.0, max(0.0, len(markdown) / 2000)) * 0.85
        return ExtractionCandidate(
            extractor=self.name,
            markdown=markdown,
            confidence=confidence,
            languages=[],
        )
