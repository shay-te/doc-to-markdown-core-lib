from doc_to_markdown_core_lib.data_layers.service.extraction_candidate import (
    ExtractionCandidate,
)
from doc_to_markdown_core_lib.data_layers.service.extractor import Extractor
from doc_to_markdown_core_lib.data_layers.service.file_type import FileType


class MdExtractor(Extractor):
    """Pass-through for already-markdown sources."""

    name = 'md-passthrough'
    file_types = (FileType.MD,)

    def extract(self, content: bytes, file_type: FileType) -> ExtractionCandidate:
        # utf-8-sig strips a leading BOM if present.
        text = content.decode('utf-8-sig')
        return ExtractionCandidate(
            extractor=self.name,
            markdown=text,
            confidence=1.0,
            languages=[],
        )
