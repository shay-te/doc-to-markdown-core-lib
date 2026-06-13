"""Picks the best candidate markdown from a list of extractor outputs.

The selection job is its own service so the orchestrator (which knows
*which* extractors to run for a file type) is separated from the
voting/agreement policy (which decides *which output* wins). Both are
intentionally stateless.
"""
import json
import re
from typing import List, Optional

from core_lib.data_layers.service.service import Service

from doc_to_markdown_core_lib.data_layers.service.extraction_candidate import (
    ExtractionCandidate,
)
from doc_to_markdown_core_lib.data_layers.service.extraction_result import (
    ExtractionResult,
)
from doc_to_markdown_core_lib.data_layers.service.tier import Tier


_UNCERTAIN_RE = re.compile(
    r'⚠️\[UNCERTAIN:\s*(?P<best>[^|\]]*?)\s*'
    r'(?:\|\s*candidates:\s*(?P<cands>[^\]]*?))?\s*\]'
)

_COMPLETENESS_TOKEN_FLOOR = 0.6


class CandidateSelectionService(Service):
    """Stateless: picks the highest-confidence candidate, then
    cross-checks against the others (Jaccard agreement, token
    survival, inline UNCERTAIN flags) to compute the final
    ``overall_confidence`` and ``needs_review`` verdict.
    """

    def __init__(self, confidence_threshold: float = 0.8):
        self._confidence_threshold = confidence_threshold

    def select(
        self,
        candidates: List[ExtractionCandidate],
        *,
        tier: Tier,
        used: List[str],
        skipped: List[dict],
        filename: Optional[str],
    ) -> ExtractionResult:
        if not candidates:
            return self._build_empty_result(tier, used, skipped, filename)

        winner = max(candidates, key=lambda candidate: candidate.confidence or 0.0)
        chosen_markdown = winner.markdown
        base_confidence = winner.confidence or 0.0
        winning_extractor = winner.extractor

        agreement = _agreement(candidates)
        overall_confidence = max(0.0, min(1.0, (base_confidence + agreement) / 2))

        chosen_markdown = _strip_bom(chosen_markdown)
        markdown_bytes = chosen_markdown.encode('utf-8')
        _assert_utf8(markdown_bytes)

        flagged_regions = _parse_flagged_regions(chosen_markdown)
        languages = _union_languages(candidates)
        completeness_ok = _completeness_ok(
            chosen_markdown, candidates, floor=_COMPLETENESS_TOKEN_FLOOR
        )

        if not completeness_ok:
            flagged_regions.append(
                {
                    'location': 'document-tail',
                    'best_guess': '',
                    'candidates': [
                        candidate.markdown for candidate in candidates
                    ],
                    'reason': 'token-survival below floor',
                }
            )
            chosen_markdown = chosen_markdown + (
                '\n\n⚠️[UNCERTAIN: extraction may be incomplete — see extraction_report.json]'
            )
            markdown_bytes = chosen_markdown.encode('utf-8')
            _assert_utf8(markdown_bytes)

        needs_review = (
            overall_confidence < self._confidence_threshold
            or bool(flagged_regions)
            or not completeness_ok
        )

        report = {
            'overall_confidence': round(overall_confidence, 4),
            'tier': tier,
            'extractors_used': used,
            'extractors_skipped': skipped,
            'languages_detected': languages,
            'flagged_regions': flagged_regions,
            'completeness_check': completeness_ok,
            'winning_extractor': winning_extractor,
            'agreement_score': round(agreement, 4),
            'needs_review': needs_review,
            'source_filename': filename,
        }
        report_bytes = json.dumps(
            report, ensure_ascii=False, indent=2
        ).encode('utf-8')
        _assert_utf8(report_bytes)

        return ExtractionResult(
            markdown=chosen_markdown,
            markdown_bytes=markdown_bytes,
            report=report,
            report_bytes=report_bytes,
            candidates=candidates,
        )

    def _build_empty_result(
        self,
        tier: Tier,
        used: List[str],
        skipped: List[dict],
        filename: Optional[str],
    ) -> ExtractionResult:
        report = {
            'overall_confidence': 0.0,
            'tier': tier,
            'extractors_used': used,
            'extractors_skipped': skipped,
            'languages_detected': [],
            'flagged_regions': [
                {
                    'location': 'document',
                    'best_guess': '',
                    'candidates': [],
                    'reason': 'no extractor produced output',
                }
            ],
            'completeness_check': False,
            'winning_extractor': None,
            'agreement_score': 0.0,
            'needs_review': True,
            'source_filename': filename,
        }
        markdown = '⚠️[UNCERTAIN: no extractor could read this document]'
        markdown_bytes = markdown.encode('utf-8')
        _assert_utf8(markdown_bytes)
        report_bytes = json.dumps(
            report, ensure_ascii=False, indent=2
        ).encode('utf-8')
        _assert_utf8(report_bytes)
        return ExtractionResult(
            markdown=markdown,
            markdown_bytes=markdown_bytes,
            report=report,
            report_bytes=report_bytes,
            candidates=[],
        )


def _agreement(candidates: List[ExtractionCandidate]) -> float:
    if len(candidates) <= 1:
        return 1.0
    token_sets = [
        set((candidate.markdown or '').split()) for candidate in candidates
    ]
    pairs = 0
    total = 0.0
    for left_index in range(len(token_sets)):
        for right_index in range(left_index + 1, len(token_sets)):
            left, right = token_sets[left_index], token_sets[right_index]
            if not left and not right:
                continue
            union = len(left | right)
            inter = len(left & right)
            total += (inter / union) if union else 0.0
            pairs += 1
    return total / pairs if pairs else 1.0


def _union_languages(candidates: List[ExtractionCandidate]) -> List[str]:
    seen = []
    for candidate in candidates:
        for lang in candidate.languages or []:
            if lang and lang not in seen:
                seen.append(lang)
    return seen


def _completeness_ok(
    chosen: str, candidates: List[ExtractionCandidate], floor: float
) -> bool:
    if not candidates:
        return False
    chosen_tokens = set(chosen.split())
    for candidate in candidates:
        candidate_tokens = set((candidate.markdown or '').split())
        if not candidate_tokens:
            continue
        survived = len(chosen_tokens & candidate_tokens) / len(candidate_tokens)
        if survived < floor:
            return False
    return True


def _parse_flagged_regions(text: str) -> List[dict]:
    regions = []
    for match in _UNCERTAIN_RE.finditer(text or ''):
        best = (match.group('best') or '').strip()
        cands_str = (match.group('cands') or '').strip()
        cands = (
            [
                candidate_text.strip()
                for candidate_text in cands_str.split('|')
                if candidate_text.strip()
            ]
            if cands_str
            else []
        )
        regions.append(
            {
                'location': f'offset {match.start()}',
                'best_guess': best,
                'candidates': cands,
            }
        )
    return regions


def _strip_bom(text: str) -> str:
    if not text:
        return text
    return text.lstrip('﻿')


def _assert_utf8(payload: bytes) -> None:
    payload.decode('utf-8')
    if payload.startswith(b'\xef\xbb\xbf'):
        raise ValueError('output starts with a UTF-8 BOM; spec forbids it')
