# These two numbers help us guess which extractor did the best job.
#
# Several extractors read the SAME file and each returns some text; then we
# keep just one. We can't know which text is actually correct, so we use a
# simple stand-in: an extractor that returns lots of text probably read the
# file fine, while one that returns almost nothing probably choked. To compare
# them we turn "how many characters did it return" into a score from 0 to 1:
#
#     score = len(text) / NORM        # then capped at 1.0
#
# NORM is just the number of characters that counts as "a full, healthy
# result" — hit it and you score the full 1.0; return less and the score
# drops. Worked example, using the document NORM = 2000:
#
#       returned   50 chars  ->    50 / 2000  = 0.03   (barely trust it)
#       returned 1800 chars  ->  1800 / 2000  = 0.90
#       returned 4000 chars  ->      capped   = 1.00   (fully trust it)
#
# So the extractor that pulled a whole document beats one that returned a stub,
# and `candidate_selection_service.select()` keeps the highest-scoring one.
# (A few extractors multiply their score by a penalty, e.g. 0.7, when the text
# they produced lost the original formatting.) The score only RANKS the
# extractors against each other — it is not a probability and never makes the
# request succeed or fail.
#
# There are two NORMs because "a full result" is a different amount of text
# depending on what was read:

# A whole document (PDF / DOC / DOCX / …) — a page or two of text, ~2000 chars.
CONFIDENCE_DOCUMENT_CHARS_NORM = 2000

# One image run through OCR (a single photo / scan / slide) holds less text
# than a whole document, so the "full result" bar is set lower, at 1500 chars.
CONFIDENCE_SINGLE_IMAGE_CHARS_NORM = 1500
