class ExtractorUnavailable(RuntimeError):
    """Raised when an extractor's backing library is missing. The
    pipeline records the reason and continues."""
