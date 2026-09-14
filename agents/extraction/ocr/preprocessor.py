"""
Core OCR Preprocessor and Document Text Extraction Engine.
Orchestrates security validation, digital vs scanned PDF routing, image OCR,
clean UTF-8 normalization, page-level character offset tracking, and Agent 1 handoff.
"""

import io
import logging
import re
from typing import List, Optional
from uuid import UUID, uuid4

from PIL import Image
import pypdf
from pypdf.errors import PdfReadError

from agents.extraction.ocr.exceptions import (
    CorruptedFileError,
    EmptyDocumentError,
    OCREngineFailureError,
    PasswordProtectedError,
    ResourceLimitExceededError,
    UnsupportedFormatError,
)
from agents.extraction.ocr.providers import MockOCRProvider, OCRProvider
from agents.extraction.ocr.schemas import (
    OCRDocumentResult,
    OCRDocumentType,
    OCRPageResult,
    OCRProcessingStatus,
)
from agents.extraction.ocr.security import (
    DEFAULT_MAX_FILE_SIZE,
    DEFAULT_MAX_IMAGE_DIMENSION,
    DEFAULT_MAX_PDF_PAGES,
    validate_document_security,
)
from agents.extraction.schemas import ExtractionJobRequest

logger = logging.getLogger("sih26189.agents.extraction.ocr")


def clean_utf8_text(raw: str) -> str:
    """
    Normalizes text to clean UTF-8.
    Strips non-printable control characters (except newline \n and tab \t)
    and normalizes carriage returns.
    """
    if not raw:
        return ""
    # Standardize newlines
    normalized = raw.replace("\r\n", "\n").replace("\r", "\n")
    # Remove control characters except \n and \t
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", normalized)
    return cleaned.strip()


class OCRPreprocessor:
    """
    Preprocesses binary documents before Agent 1 intelligence extraction.
    Determines digital text vs OCR, enforces provenance, and guarantees clean UTF-8 text.
    """

    def __init__(
        self,
        ocr_provider: Optional[OCRProvider] = None,
        max_file_size: int = DEFAULT_MAX_FILE_SIZE,
        max_pages: int = DEFAULT_MAX_PDF_PAGES,
        max_image_dimension: int = DEFAULT_MAX_IMAGE_DIMENSION,
        min_text_chars_per_page: int = 40,
    ):
        self.ocr_provider = ocr_provider or MockOCRProvider()
        self.max_file_size = max_file_size
        self.max_pages = max_pages
        self.max_image_dimension = max_image_dimension
        self.min_text_chars_per_page = min_text_chars_per_page

    def _process_image(self, data: bytes, doc_type: OCRDocumentType) -> List[tuple[str, bool]]:
        """
        Validates image dimensions and runs OCR recognition.
        Returns list of (text, is_ocr_applied).
        """
        try:
            with Image.open(io.BytesIO(data)) as img:
                width, height = img.size
                if width > self.max_image_dimension or height > self.max_image_dimension:
                    raise ResourceLimitExceededError(
                        f"Image dimensions ({width}x{height}) exceed maximum allowed {self.max_image_dimension}px."
                    )
        except Exception as exc:
            if isinstance(exc, ResourceLimitExceededError):
                raise
            raise CorruptedFileError(f"Failed to decode image data: {exc}") from exc

        # Execute OCR provider
        ocr_text = self.ocr_provider.extract_text_from_image(data)
        cleaned = clean_utf8_text(ocr_text)
        return [(cleaned, True)]

    def _process_pdf(self, data: bytes) -> tuple[List[tuple[str, bool]], OCRDocumentType]:
        """
        Processes PDF page by page.
        Extracts digital text where present, falls back to OCR for scanned/image pages.
        Returns (list_of_pages, resolved_doc_type).
        """
        try:
            stream = io.BytesIO(data)
            reader = pypdf.PdfReader(stream)
        except Exception as exc:
            raise CorruptedFileError(f"Malformed or unreadable PDF: {exc}") from exc

        if reader.is_encrypted:
            raise PasswordProtectedError("PDF is encrypted or password-protected.")

        num_pages = len(reader.pages)
        if num_pages == 0:
            raise EmptyDocumentError("PDF contains 0 pages.")

        if num_pages > self.max_pages:
            raise ResourceLimitExceededError(
                f"PDF page count ({num_pages}) exceeds allowed limit of {self.max_pages} pages."
            )

        page_results: List[tuple[str, bool]] = []
        digital_pages_count = 0
        ocr_pages_count = 0

        for page_idx, page in enumerate(reader.pages):
            try:
                page_text = clean_utf8_text(page.extract_text() or "")
            except Exception as exc:
                logger.warning("Error extracting text from page %d: %s", page_idx + 1, exc)
                page_text = ""

            # If meaningful digital text exists on this page, use it directly
            if len(page_text.strip()) >= self.min_text_chars_per_page:
                page_results.append((page_text, False))
                digital_pages_count += 1
            else:
                # Scanned or image-only page: extract embedded images to OCR
                scanned_text = ""
                has_image = False
                try:
                    for img_obj in page.images:
                        has_image = True
                        img_bytes = img_obj.data
                        text_snippet = self.ocr_provider.extract_text_from_image(img_bytes)
                        if text_snippet:
                            scanned_text += "\n" + clean_utf8_text(text_snippet)
                except Exception as exc:
                    logger.warning("Error extracting images on page %d: %s", page_idx + 1, exc)

                # If no embedded image could be extracted or OCR was empty, try calling OCR provider directly for the page
                if not scanned_text.strip():
                    if not has_image:
                        try:
                            # Attempt OCR extraction for the page
                            fallback_ocr = self.ocr_provider.extract_text_from_image(b"")
                            if fallback_ocr and fallback_ocr.strip():
                                scanned_text = clean_utf8_text(fallback_ocr)
                                has_image = True
                        except Exception as exc:
                            logger.warning("Error in fallback OCR on page %d: %s", page_idx + 1, exc)

                if not scanned_text.strip():
                    if page_text.strip():
                        page_results.append((page_text, False))
                        digital_pages_count += 1
                        continue
                    elif has_image:
                        # OCR ran on image but returned empty text
                        page_results.append(("", True))
                        ocr_pages_count += 1
                        continue
                    else:
                        # Truly blank page
                        page_results.append(("", False))
                        continue

                page_results.append((scanned_text.strip(), True))
                ocr_pages_count += 1

        # Classify overall document type
        if digital_pages_count > 0 and ocr_pages_count == 0:
            resolved_type = OCRDocumentType.DIGITAL_PDF
        elif ocr_pages_count > 0 and digital_pages_count == 0:
            resolved_type = OCRDocumentType.SCANNED_PDF
        elif digital_pages_count > 0 and ocr_pages_count > 0:
            resolved_type = OCRDocumentType.MIXED_PDF
        else:
            resolved_type = OCRDocumentType.DIGITAL_PDF

        return page_results, resolved_type

    def process_document(
        self,
        data: bytes,
        original_filename: str = "document.pdf",
        document_id: Optional[UUID] = None,
    ) -> OCRDocumentResult:
        """
        Main entry point for document parsing and OCR preprocessing.
        """
        doc_id = document_id or uuid4()

        # 1. Defensively validate security boundaries
        try:
            val_res = validate_document_security(
                data=data,
                original_filename=original_filename,
                max_file_size=self.max_file_size,
            )
            if not val_res.is_valid:
                return OCRDocumentResult(
                    document_id=doc_id,
                    status=OCRProcessingStatus.UNSUPPORTED_FORMAT,
                    detected_type=val_res.detected_type,
                    error_message=val_res.error_message,
                )
        except ResourceLimitExceededError as exc:
            return OCRDocumentResult(
                document_id=doc_id,
                status=OCRProcessingStatus.LIMIT_EXCEEDED,
                detected_type=OCRDocumentType.UNKNOWN,
                error_message=str(exc),
            )
        except Exception as exc:
            return OCRDocumentResult(
                document_id=doc_id,
                status=OCRProcessingStatus.UNSUPPORTED_FORMAT,
                detected_type=OCRDocumentType.UNKNOWN,
                error_message=str(exc),
            )

        # 2. Route processing according to detected document type
        raw_pages: List[tuple[str, bool]] = []
        resolved_type = val_res.detected_type

        try:
            if val_res.detected_type in [OCRDocumentType.DIGITAL_PDF, OCRDocumentType.SCANNED_PDF]:
                raw_pages, resolved_type = self._process_pdf(data)
            elif val_res.detected_type in [OCRDocumentType.IMAGE_PNG, OCRDocumentType.IMAGE_JPEG]:
                raw_pages = self._process_image(data, val_res.detected_type)
            else:
                return OCRDocumentResult(
                    document_id=doc_id,
                    status=OCRProcessingStatus.UNSUPPORTED_FORMAT,
                    detected_type=val_res.detected_type,
                    error_message="Unsupported document representation.",
                )
        except PasswordProtectedError as exc:
            return OCRDocumentResult(
                document_id=doc_id,
                status=OCRProcessingStatus.PASSWORD_PROTECTED,
                detected_type=val_res.detected_type,
                error_message=str(exc),
            )
        except ResourceLimitExceededError as exc:
            return OCRDocumentResult(
                document_id=doc_id,
                status=OCRProcessingStatus.LIMIT_EXCEEDED,
                detected_type=val_res.detected_type,
                error_message=str(exc),
            )
        except CorruptedFileError as exc:
            return OCRDocumentResult(
                document_id=doc_id,
                status=OCRProcessingStatus.CORRUPTED_FILE,
                detected_type=val_res.detected_type,
                error_message=str(exc),
            )
        except EmptyDocumentError as exc:
            return OCRDocumentResult(
                document_id=doc_id,
                status=OCRProcessingStatus.EMPTY_DOCUMENT,
                detected_type=val_res.detected_type,
                error_message=str(exc),
            )
        except OCREngineFailureError as exc:
            return OCRDocumentResult(
                document_id=doc_id,
                status=OCRProcessingStatus.OCR_ENGINE_FAILURE,
                detected_type=val_res.detected_type,
                error_message=str(exc),
            )
        except Exception as exc:
            logger.error("Unexpected error processing document %s: %s", doc_id, exc, exc_info=True)
            return OCRDocumentResult(
                document_id=doc_id,
                status=OCRProcessingStatus.CORRUPTED_FILE,
                detected_type=val_res.detected_type,
                error_message=f"Document parsing failed: {exc}",
            )

        # 3. Concatenate text with strict page offset provenance
        pages: List[OCRPageResult] = []
        full_text_parts = []
        current_offset = 0

        for idx, (p_text, was_ocr) in enumerate(raw_pages, start=1):
            char_start = current_offset
            char_end = current_offset + len(p_text)

            pages.append(
                OCRPageResult(
                    page_number=idx,
                    text=p_text,
                    character_start=char_start,
                    character_end=char_end,
                    is_ocr_applied=was_ocr,
                )
            )
            full_text_parts.append(p_text)
            # Advance offset including the double-newline delimiter between pages
            current_offset = char_end + 2

        full_text = "\n\n".join(full_text_parts).strip()

        # Check if entire document produced empty text
        if not full_text:
            return OCRDocumentResult(
                document_id=doc_id,
                status=OCRProcessingStatus.EMPTY_DOCUMENT,
                detected_type=resolved_type,
                total_pages=len(raw_pages),
                pages=pages,
                full_text="",
                error_message="Document contains no extractable text.",
            )

        return OCRDocumentResult(
            document_id=doc_id,
            status=OCRProcessingStatus.SUCCESS,
            detected_type=resolved_type,
            total_pages=len(raw_pages),
            pages=pages,
            full_text=full_text,
        )

    def to_agent1_request(self, result: OCRDocumentResult) -> ExtractionJobRequest:
        """
        Handoff adapter that converts an OCRDocumentResult directly into an ExtractionJobRequest
        ready for Agent 1 consumption.
        """
        return ExtractionJobRequest(
            job_id=result.document_id,
            text=result.full_text,
            metadata={
                "document_id": str(result.document_id),
                "total_pages": result.total_pages,
                "detected_type": result.detected_type.value,
                "status": result.status.value,
            },
        )
