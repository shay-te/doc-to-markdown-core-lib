from omegaconf import DictConfig

from core_lib.core_lib import CoreLib

from doc_to_markdown_core_lib.data_layers.service.candidate_selection_service import (
    CandidateSelectionService,
)
from doc_to_markdown_core_lib.data_layers.service.markdown_service import (
    MarkdownService,
)


class DocToMarkdownCoreLib(CoreLib):
    """Stateless conversion lib.

    Two services are exposed:

    - :attr:`selection` (:class:`CandidateSelectionService`) — the
      voting/agreement layer that picks the best candidate markdown
      and computes the extraction report. Reusable on its own when a
      caller already has candidates from somewhere else.
    - :attr:`markdown` (:class:`MarkdownService`) — the orchestrator
      that picks which extractors to run per file_type, runs them,
      and hands the candidates to :attr:`selection`.

    Config knobs (under ``core_lib`` in the supplied :class:`DictConfig`):

    - ``extraction.ocr_languages``: tuple of tesseract language codes.
    - ``extraction.confidence_threshold``: float, gates ``needs_review``.
    """

    def __init__(self, conf: DictConfig):
        super().__init__()
        self.config = conf

        core_cfg = conf.get('core_lib', {}) if conf else {}
        extraction_cfg = core_cfg.get('extraction', {}) or {}
        ocr_languages_raw = extraction_cfg.get('ocr_languages')
        confidence_threshold = float(
            extraction_cfg.get('confidence_threshold', 0.8)
        )

        ocr_languages = (
            tuple(ocr_languages_raw)
            if ocr_languages_raw is not None
            else None
        )

        self.selection = CandidateSelectionService(
            confidence_threshold=confidence_threshold,
        )
        self.markdown = MarkdownService(
            selection_service=self.selection,
            ocr_languages=ocr_languages,
        )
