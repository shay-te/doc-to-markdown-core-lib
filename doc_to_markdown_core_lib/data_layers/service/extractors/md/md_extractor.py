from doc_to_markdown_core_lib.data_layers.service.types import ExtractionCandidate, Extractor


class MdExtractor(Extractor):
    """Pass-through for already-markdown sources."""

    name = 'md-passthrough'
    file_types = ('md',)

    def extract(self, content: bytes, file_type: str) -> ExtractionCandidate:
        # utf-8-sig strips a leading BOM if present.
        text = content.decode('utf-8-sig')
        return ExtractionCandidate(
            extractor=self.name,
            markdown=text,
            confidence=1.0,
            languages=[],
        )
