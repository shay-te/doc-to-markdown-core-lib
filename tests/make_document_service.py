from doc_to_markdown_core_lib.data_layers.service.candidate_selection_service import (
    CandidateSelectionService,
)
from doc_to_markdown_core_lib.data_layers.service.document_service import (
    DocumentService,
)


def make_document_service(extractors, confidence_threshold=0.8):
    """:class:`DocumentService` over an explicit extractor list."""
    return DocumentService(
        selection_service=CandidateSelectionService(
            confidence_threshold=confidence_threshold,
        ),
        extractors=extractors,
    )
