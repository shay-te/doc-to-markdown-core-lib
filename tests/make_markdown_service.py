from doc_to_markdown_core_lib.data_layers.service.candidate_selection_service import (
    CandidateSelectionService,
)
from doc_to_markdown_core_lib.data_layers.service.markdown_service import (
    MarkdownService,
)


def make_markdown_service(extractors, confidence_threshold=0.8):
    """:class:`MarkdownService` over an explicit extractor list."""
    return MarkdownService(
        selection_service=CandidateSelectionService(
            confidence_threshold=confidence_threshold,
        ),
        extractors=extractors,
    )
