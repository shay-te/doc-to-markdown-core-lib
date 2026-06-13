# doc-to-markdown-core-lib

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.7+](https://img.shields.io/badge/python-3.7%2B-blue.svg)](https://www.python.org/downloads/)

Open-source, multi-extractor document-to-Markdown conversion library for Python.

Most converters give you one engine and one answer. `doc-to-markdown-core-lib`
runs **every available extractor for the file type in parallel**, scores the
candidates, and returns the best one — with a structured report explaining
which extractor won, which were tried, and which were skipped (and why).

It's designed for ingestion pipelines that need to be honest about extraction
quality across heterogeneous corpora: scanned PDFs, native PDFs, `.docx` from
ten different authoring tools, legacy `.doc`, plain `.txt`, Markdown,
standalone images.

## Features

- **Ensemble extraction.** Each file type runs through several independent
  engines; the one with the highest confidence wins.
- **Tiered routing.** Clean, text-native PDFs run a single fast primary
  extractor; messy / scanned PDFs fan out across the full ensemble (including
  OCR).
- **Graceful degradation.** Every extractor lazy-imports its backend. Missing
  a dependency means that one extractor is reported as unavailable in the run
  report — the pipeline keeps going on whatever else is installed.
- **Structured reports.** Every call returns the markdown *and* a JSON-able
  `report` listing engines used, engines skipped (with reasons), detected
  languages, and the chosen candidate's confidence.
- **Pluggable.** Drop in your own `Extractor` subclass and `register()` it on
  the service — your engine joins the vote automatically.
- **Hydra-configured.** Wire-up follows the [core-lib](https://github.com/shay-te/core-lib)
  pattern: services live under `data_layers/service/`, the public surface is
  `DocToMarkdownCoreLib`.

## Supported inputs

| File type | Enum         | Primary engine (clean tier) | Ensemble members                                                                              |
|-----------|--------------|-----------------------------|-----------------------------------------------------------------------------------------------|
| `md`      | `FileType.MD`    | `md-passthrough`            | `MdExtractor`                                                                                 |
| `txt`     | `FileType.TXT`   | `plain-text`                | `TxtExtractor`                                                                                |
| `pdf`     | `FileType.PDF`   | `pymupdf`                   | `PyMuPdfExtractor`, `PdfPlumberExtractor`, `PdfMinerExtractor`, `PypdfExtractor`, `PyMuPdf4LlmExtractor`, `MarkItDownExtractor`, `TesseractExtractor` (OCR), `EasyOcrExtractor`, `RapidOcrExtractor` |
| `docx`    | `FileType.DOCX`  | `python-docx`               | `DocxExtractor`, `MammothExtractor`, `SofficeExtractor`, `TextractExtractor`, `MarkItDownExtractor` |
| `doc`     | `FileType.DOC`   | `soffice`                   | `SofficeExtractor`, `TextractExtractor`                                                       |
| `image`   | `FileType.IMAGE` | —                           | `TesseractExtractor`, `EasyOcrExtractor`, `RapidOcrExtractor`                                 |

OCR (Tesseract / EasyOCR / RapidOCR) also handles scanned PDFs after page
rasterization via PyMuPDF.

## Installation

From source:

```bash
git clone https://github.com/<your-fork>/doc-to-markdown-core-lib.git
cd doc-to-markdown-core-lib
pip install -e .
```

The base install pulls only `core-lib`. Extractor backends are optional — each
one lazy-imports its dependency and reports itself unavailable if missing.
Install the engines you want:

```bash
# PDF
pip install PyMuPDF pdfplumber pdfminer.six pypdf pymupdf4llm markitdown

# DOCX / DOC
pip install python-docx mammoth textract
#   .doc also needs LibreOffice (`soffice`) on PATH

# OCR (any combination)
pip install pytesseract Pillow      # plus the `tesseract` binary + language packs
pip install easyocr
pip install rapidocr-onnxruntime
```

You don't need all of these. The library will use whatever's available; a
production deployment typically installs the two or three engines that match
its corpus.

## Quickstart

```python
import hydra
from doc_to_markdown_core_lib import DocToMarkdownCoreLib
from doc_to_markdown_core_lib.data_layers.service.file_type import FileType

hydra.core.global_hydra.GlobalHydra.instance().clear()
hydra.initialize(
    config_path='../../doc_to_markdown_core_lib/config', version_base=None
)
lib = DocToMarkdownCoreLib(hydra.compose('doc_to_markdown_core_lib.yaml'))

with open('paper.pdf', 'rb') as file_handle:
    content = file_handle.read()

result = lib.document.extract(content, file_type=FileType.PDF, filename='paper.pdf')

print(result.markdown)                          # str — best-of-ensemble markdown
print(result.report['winning_extractor'])       # str — name of the chosen extractor
print(result.report['extractors_used'])         # list of extractors that produced candidates
print(result.report['extractors_skipped'])      # list of {extractor, reason}
print(result.report['languages_detected'])      # list of detected language codes
print(result.report['overall_confidence'])      # float in [0, 1]
print(result.report['needs_review'])            # bool — true if confidence/completeness flagged the run
```

`ExtractionResult` exposes:

| Field              | Type                  | Notes                                             |
|--------------------|-----------------------|---------------------------------------------------|
| `markdown`         | `str`                 | Winning candidate's text                          |
| `markdown_bytes`   | `bytes`               | Pre-UTF-8-encoded; persist as-is                  |
| `report`           | `dict`                | Provenance: chosen extractor, used, skipped, etc. |
| `report_bytes`     | `bytes`               | `report` serialized to UTF-8 JSON                 |
| `candidates`       | `List[ExtractionCandidate]` | All non-empty candidates considered         |

## Adding your own extractor

```python
from doc_to_markdown_core_lib.data_layers.service.extractor import Extractor
from doc_to_markdown_core_lib.data_layers.service.extraction_candidate import ExtractionCandidate
from doc_to_markdown_core_lib.data_layers.service.file_type import FileType


class MyPdfExtractor(Extractor):
    name = 'my-pdf'
    file_types = (FileType.PDF,)

    def extract(self, content: bytes, file_type: FileType) -> ExtractionCandidate:
        markdown = my_engine_convert(content)
        return ExtractionCandidate(
            extractor=self.name,
            markdown=markdown,
            confidence=0.8,
            languages=[],
        )


lib.document.register(MyPdfExtractor())
```

Raise `ExtractorUnavailable` from `extract` (typically inside the lazy import
block) when a runtime dependency is missing — the orchestrator will record it
in the report and continue.

## Tiered routing

PDFs in particular are bimodal: a born-digital PDF with a real text layer just
needs one fast extraction, while a scanned image-only PDF needs the full OCR
ensemble. `tier_detector.detect_tier(content, file_type)` classifies each input
as `clean` or `messy`:

- **clean** → run only the primary extractor for that file type
  (`pymupdf` for PDF, `python-docx` for DOCX, etc.).
- **messy** → run the entire matching ensemble and vote.

This keeps the hot path cheap without hand-tuning per document.

## Architecture

```
DocToMarkdownCoreLib                       # public surface, Hydra-configured
└── document: DocumentService               # only public service
    ├── extractors:  list[Extractor]        # per-file_type engines
    ├── tier_detector.detect_tier(...)      # clean vs. messy routing
    └── selection_service: CandidateSelectionService  # injected; not exposed
```

Each extractor lives under
`doc_to_markdown_core_lib/data_layers/service/extractors/<file_type>/`,
e.g. `extractors/pdf/pymupdf_extractor.py`. Type-shared helpers (the
`FileType` enum, dataclasses, abstract base) live one level up under
`data_layers/service/`.

## Testing

The suite uses `unittest` (no pytest). One `TestCase` class per file under
`tests/`:

```bash
PYTHONPATH=../core-lib:. python -m unittest discover -s tests -p "test_*.py"
```

All extractor tests stub their backends (`fitz`, `mammoth`, `pytesseract`,
…) so the suite runs without any of the optional dependencies installed.

## Contributing

Pull requests welcome. To keep the codebase navigable:

- One class per file; filename matches the class (snake_case).
- File-type strings come from the `FileType` enum, never raw literals.
- New extractors subclass `Extractor`, set `name` + `file_types`, and raise
  `ExtractorUnavailable` from `extract` when their backend isn't installed.
- Tests are `unittest.TestCase` subclasses under `tests/`, one class per
  `test_*.py` file.

Please open an issue before large refactors so we can align on direction.

## License

Released under the [MIT License](LICENSE).

Built on top of [core-lib](https://github.com/shay-te/core-lib) (also MIT).
