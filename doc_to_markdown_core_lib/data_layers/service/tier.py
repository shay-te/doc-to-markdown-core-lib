import enum


class Tier(str, enum.Enum):
    """Pre-flight document classification.

    The tier is a routing hint produced by :func:`tier_detector.detect_tier`
    and consumed by :meth:`DocumentService.extract` to decide whether
    to run a single extractor or fan out across the full ensemble.

    - :attr:`CLEAN` — born-digital text-native documents (markdown,
      txt, docx, PDFs with a real text layer). We trust the primary
      extractor for the file type; running the full ensemble would
      just burn CPU on near-identical outputs.
    - :attr:`RISKY` — anything else (scanned PDFs, images, unknown
      shapes). We run every applicable extractor and let the selection
      service vote, because no single engine is reliable across this
      bucket.

    The string values are stored verbatim in the run report's
    ``'tier'`` field so log/analytics consumers can read it without
    importing this enum."""
    CLEAN = 'clean'
    RISKY = 'risky'
