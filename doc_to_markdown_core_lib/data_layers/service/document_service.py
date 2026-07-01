"""Document-extraction orchestrator. Single public service of the
library — see :class:`DocumentService` for the whole flow."""
import logging
from typing import List, Optional, Tuple

from core_lib.data_layers.service.service import Service

from doc_to_markdown_core_lib.data_layers.service.candidate_selection_service import (
    CandidateSelectionService,
)
from doc_to_markdown_core_lib.data_layers.data.extraction.extraction_candidate import (
    ExtractionCandidate,
)
from doc_to_markdown_core_lib.data_layers.data.extraction.extraction_result import (
    ExtractionResult,
)
from doc_to_markdown_core_lib.data_layers.service.extractors.extractor import Extractor
from doc_to_markdown_core_lib.error_handling.extractor_unavailable import (
    ExtractorUnavailable,
)
from doc_to_markdown_core_lib.data_layers.data.file_type import FileType
from doc_to_markdown_core_lib.data_layers.service.helpers import (
    build_default_extractors,
    detect_tier,
)

logger = logging.getLogger(__name__)


# Skip-reason strings stored in the run report; named so reviewers can
# grep the report payload back to the branch that produced it.
_REASON_UNAVAILABLE = 'unavailable: {message}'
_REASON_ENGINE_ERROR = 'error: {message}'
_REASON_EMPTY_RESULT = 'empty result'


class DocumentService(Service):
    """Single public surface of the library.

    :meth:`extract` is the whole flow: take document bytes + the
    canonical :class:`FileType`, fan them out across every applicable
    extractor (e.g. a PDF goes to PyMuPDF, pdfplumber, pdfminer, pypdf,
    pymupdf4llm, markitdown, plus OCR), collect every candidate
    markdown, hand the candidates to the injected
    :class:`CandidateSelectionService` for voting, and return the
    winning markdown plus the report explaining the choice.

    The selection service is a constructor parameter — callers never
    see it. Hosts that want their own engine in the vote call
    :meth:`register`."""

    DEFAULT_OCR_LANGUAGES = ('eng', 'heb', 'ara', 'chi_sim')

    def __init__(
        self,
        selection_service: CandidateSelectionService,
        ocr_languages: Optional[Tuple[str, ...]] = None,
        extractors: Optional[List[Extractor]] = None,
    ):
        self._selection_service = selection_service
        self._extractors: List[Extractor] = (
            list(extractors)
            if extractors is not None
            else build_default_extractors(
                tuple(ocr_languages or self.DEFAULT_OCR_LANGUAGES),
            )
        )

    def register(self, extractor: Extractor) -> None:
        """Plug in a host-owned extractor — it joins the candidate
        fan-out on every subsequent :meth:`extract`."""
        self._extractors.append(extractor)

    def extract(
        self,
        content: bytes,
        file_type: FileType,
        filename: Optional[str] = None,
    ) -> ExtractionResult:
        """Run the extraction pipeline and return the winning result.

        The flow is intentionally linear so a reader can follow it
        top-to-bottom:
            1. Classify the input's tier (``clean`` vs ``risky``) — recorded
               in the report as a signal; it does NOT prune the lineup.
            2. Fan out to every extractor that handles this file_type.
            3. Run each one; bucket into candidates / skipped.
            4. Hand the candidates to the selection service to vote.
        """
        tier = detect_tier(content, file_type)
        selected_extractors = self._select_extractors_for(file_type)

        candidates: List[ExtractionCandidate] = []
        used_extractor_names: List[str] = []
        skipped_extractors: List[dict] = []

        for extractor in selected_extractors:
            candidate, skip_reason = self._run_one_extractor(
                extractor, content, file_type
            )
            if candidate is not None:
                candidates.append(candidate)
                used_extractor_names.append(extractor.name)
            else:
                skipped_extractors.append(
                    {'extractor': extractor.name, 'reason': skip_reason}
                )

        return self._selection_service.select(
            candidates,
            tier=tier,
            used=used_extractor_names,
            skipped=skipped_extractors,
            filename=filename,
        )

    def _run_one_extractor(
        self,
        extractor: Extractor,
        content: bytes,
        file_type: FileType,
    ) -> Tuple[Optional[ExtractionCandidate], Optional[str]]:
        """Run one engine in isolation.

        Returns ``(candidate, None)`` on a usable result and
        ``(None, reason)`` for every failure mode (engine missing,
        engine raised, empty output). The two-tuple keeps :meth:`extract`'s
        loop a single ``if/else`` rather than three try/except branches."""
        try:
            candidate = extractor.extract(content, file_type)
        except ExtractorUnavailable as unavailable_error:
            logger.info(
                'extractor `%s` unavailable: %s',
                extractor.name, unavailable_error,
            )
            return None, _REASON_UNAVAILABLE.format(
                message=unavailable_error
            )
        except Exception as engine_error:  # noqa: BLE001
            logger.warning(
                'extractor `%s` failed: %s',
                extractor.name, engine_error,
            )
            return None, _REASON_ENGINE_ERROR.format(message=engine_error)

        if not (candidate.markdown or '').strip():
            return None, _REASON_EMPTY_RESULT
        return candidate, None

    def _select_extractors_for(self, file_type: FileType) -> List[Extractor]:
        """Every registered extractor that handles ``file_type`` runs —
        the full ensemble always fans out and the selection service votes
        on the most correct output (no per-tier short-circuit to a single
        "primary" engine). Empty when nothing handles the type, in which
        case the caller surfaces a "no candidates" report.
        """
        return [
            extractor
            for extractor in self._extractors
            if file_type in extractor.file_types
        ]
