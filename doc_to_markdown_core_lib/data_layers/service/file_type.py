import enum


class FileType(str, enum.Enum):
    """Canonical pipeline file types — ``Extractor.file_types``,
    ``MarkdownService.extract`` and ``detect_tier`` all speak these
    values."""
    MD = 'md'
    TXT = 'txt'
    PDF = 'pdf'
    DOC = 'doc'
    DOCX = 'docx'
    IMAGE = 'image'
