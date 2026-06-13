# Length-based confidence heuristic shared by the extractors: the
# extracted text length is divided by the norm and clamped to 0..1,
# so output at or above the norm contributes full confidence.
CONFIDENCE_DOCUMENT_CHARS_NORM = 2000
CONFIDENCE_SINGLE_IMAGE_CHARS_NORM = 1500
