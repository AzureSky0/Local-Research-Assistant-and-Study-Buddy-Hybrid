from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pymupdf

from app.documents.exceptions import ExtractionError
from app.documents.extraction.document_extractor import DocumentExtractor, ExtractedPage

PDF_EXTRACTOR_VERSION = f"pymupdf-{pymupdf.VersionBind}-1"


class PdfExtractor(DocumentExtractor):
    """Reads the text layer of PDF files with PyMuPDF.

    Scanned PDFs (images without a text layer) produce empty pages;
    the processing pipeline reports those, since reading images needs
    OCR, which is planned as an extension.
    """

    @property
    def file_types(self) -> frozenset[str]:
        return frozenset({"pdf"})

    @property
    def version(self) -> str:
        return PDF_EXTRACTOR_VERSION

    def extract(self, file_path: Path) -> Iterator[ExtractedPage]:
        try:
            document = pymupdf.open(file_path)
        except (pymupdf.FileDataError, RuntimeError, ValueError) as error:
            raise ExtractionError(
                "The PDF file is damaged or isn’t a valid PDF."
            ) from error
        except FileNotFoundError as error:
            raise ExtractionError(
                "The original file is no longer at its saved location. "
                "Add it again if it has moved."
            ) from error

        with document:
            if document.needs_pass:
                raise ExtractionError(
                    "This PDF is password-protected. Remove the password, then add it again."
                )

            for index in range(document.page_count):
                try:
                    text = document.load_page(index).get_text("text")
                except (RuntimeError, ValueError) as error:
                    raise ExtractionError(
                        f"Page {index + 1} of the PDF could not be read. The file may be damaged."
                    ) from error

                yield ExtractedPage(page_number=index + 1, text=text)
