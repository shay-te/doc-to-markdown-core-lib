from doc_to_markdown_core_lib.data_layers.service.types import ExtractionCandidate, Extractor


class TxtExtractor(Extractor):
    """Plain-text source — try UTF variants, then fall back to latin-1."""

    name = 'plain-text'
    file_types = ('txt',)

    def extract(self, content: bytes, file_type: str) -> ExtractionCandidate:
        last_err = None
        for enc in ('utf-8-sig', 'utf-8', 'utf-16', 'latin-1'):
            try:
                text = content.decode(enc)
                return ExtractionCandidate(
                    extractor=self.name,
                    markdown=text,
                    confidence=1.0 if enc.startswith('utf') else 0.5,
                    languages=[],
                )
            except UnicodeDecodeError as e:
                last_err = e
        # latin-1 never fails — only reached if the fallback list shrinks.
        raise RuntimeError(f'could not decode text content: {last_err}')  # pragma: no cover
