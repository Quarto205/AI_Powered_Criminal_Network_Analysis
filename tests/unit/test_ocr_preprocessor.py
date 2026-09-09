"""
Unit tests for OCR Preprocessor and Document Text Extraction Engine.
Validates file signature inspection, path traversal security, resource limits,
digital vs scanned PDF processing, image OCR, provenance offset tracking,
and end-to-end integration handoff to Agent 1.
"""

import io
import pytest
from uuid import uuid4
from PIL import Image
import pypdf

from agents.extraction.ocr.exceptions import (
    CorruptedFileError,
    EmptyDocumentError,
    OCREngineFailureError,
    PasswordProtectedError,
    PathTraversalError,
    ResourceLimitExceededError,
    UnsupportedFormatError,
)
from agents.extraction.ocr.preprocessor import (
    OCRPreprocessor,
    clean_utf8_text,
)
from agents.extraction.ocr.providers import MockOCRProvider
from agents.extraction.ocr.schemas import (
    OCRDocumentResult,
    OCRDocumentType,
    OCRProcessingStatus,
)
from agents.extraction.ocr.security import (
    inspect_file_signature,
    sanitize_filename,
    validate_document_security,
)
from agents.extraction.parser import ExtractionEngine
from agents.extraction.schemas import ExtractionEntityType


# ==============================================================================
# TEST FIXTURES & HELPERS
# ==============================================================================

def create_digital_pdf_bytes(text: str = "Suresh Verma drove vehicle MH 02 AB 5678 to the warehouse.") -> bytes:
    """Creates a valid, real in-memory digital PDF with embedded text stream."""
    stream_content = f"BT /F1 12 Tf 50 100 Td ({text}) Tj ET".encode("latin-1")
    length = len(stream_content)
    pdf = (
        b"%PDF-1.4\n"
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 400 200] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj\n"
        b"4 0 obj << /Length " + str(length).encode("ascii") + b" >> stream\n"
        + stream_content + b"\nendstream endobj\n"
        b"5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n"
        b"xref\n"
        b"0 6\n"
        b"0000000000 65535 f \n"
        b"trailer << /Size 6 /Root 1 0 R >>\n"
        b"startxref\n"
        b"500\n"
        b"%%EOF\n"
    )
    # Parse and write through pypdf to ensure 100% compliant structure
    reader = pypdf.PdfReader(io.BytesIO(pdf))
    writer = pypdf.PdfWriter()
    writer.add_page(reader.pages[0])
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


def create_blank_scanned_pdf_bytes(num_pages: int = 1) -> bytes:
    """Creates a PDF with blank pages (simulating a scanned PDF without text layer)."""
    writer = pypdf.PdfWriter()
    for _ in range(num_pages):
        writer.add_blank_page(width=300, height=300)
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


def create_encrypted_pdf_bytes(password: str = "secret") -> bytes:
    """Creates an encrypted, password-protected PDF."""
    writer = pypdf.PdfWriter()
    writer.add_blank_page(width=200, height=200)
    writer.encrypt(password)
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


def create_valid_image_bytes(fmt: str = "PNG", size: tuple[int, int] = (100, 100)) -> bytes:
    """Generates valid PNG or JPEG image bytes."""
    img = Image.new("RGB", size, color="white")
    out = io.BytesIO()
    img.save(out, format=fmt)
    return out.getvalue()


# ==============================================================================
# 1. SECURITY & VALIDATION TESTS
# ==============================================================================

class TestSecurityAndValidation:
    """Validates magic byte verification, filename sanitization, and resource limits."""

    def test_magic_bytes_pdf(self):
        data = b"%PDF-1.4 test data"
        doc_type, mime = inspect_file_signature(data)
        assert doc_type == OCRDocumentType.DIGITAL_PDF
        assert mime == "application/pdf"

    def test_magic_bytes_png(self):
        data = b"\x89PNG\r\n\x1a\n\x00\x00"
        doc_type, mime = inspect_file_signature(data)
        assert doc_type == OCRDocumentType.IMAGE_PNG
        assert mime == "image/png"

    def test_magic_bytes_jpeg(self):
        data = b"\xFF\xD8\xFF\xE0\x00\x10JFIF"
        doc_type, mime = inspect_file_signature(data)
        assert doc_type == OCRDocumentType.IMAGE_JPEG
        assert mime == "image/jpeg"

    def test_magic_bytes_rejection_for_unknown(self):
        data = b"MZ\x90\x00\x03"  # Windows PE executable
        with pytest.raises(UnsupportedFormatError, match="do not match permitted document types"):
            inspect_file_signature(data)

    def test_extension_spoofing_rejection(self):
        # File named .pdf but contains arbitrary/executable bytes
        fake_pdf = b"MZ\x90\x00\x03\x00\x00\x00"
        res = validate_document_security(fake_pdf, "malware.pdf")
        assert res.is_valid is False
        assert "do not match permitted document types" in (res.error_message or "")

    def test_empty_bytes_validation(self):
        res = validate_document_security(b"", "empty.pdf")
        assert res.is_valid is False
        assert res.file_size_bytes == 0

    def test_oversized_file_rejection(self):
        # Set max_file_size to 1KB for test
        large_data = b"%PDF-" + b"0" * 2000
        with pytest.raises(ResourceLimitExceededError, match="exceeds maximum allowed limit"):
            validate_document_security(large_data, "large.pdf", max_file_size=1024)

    def test_path_traversal_prevention(self):
        with pytest.raises(PathTraversalError):
            sanitize_filename("../../etc/passwd")

        with pytest.raises(PathTraversalError):
            sanitize_filename("..\\..\\windows\\system32\\calc.exe")

        with pytest.raises(PathTraversalError):
            sanitize_filename("valid_name\x00.pdf")

        clean = sanitize_filename("Case#2026-Report (Confidential).pdf")
        assert "Case_2026-Report__Confidential_.pdf" in clean


# ==============================================================================
# 2. PDF PROCESSING TESTS
# ==============================================================================

class TestPDFProcessing:
    """Validates digital, scanned, mixed, corrupt, and password-protected PDF extraction."""

    def test_digital_pdf_direct_extraction(self):
        expected_text = "Suresh Verma drove vehicle MH 02 AB 5678 to the warehouse."
        pdf_bytes = create_digital_pdf_bytes(expected_text)

        # Mock provider should NOT be called for a digital text PDF
        provider = MockOCRProvider(default_text="OCR SHOULD NOT BE CALLED")
        preprocessor = OCRPreprocessor(ocr_provider=provider)

        res = preprocessor.process_document(pdf_bytes, "investigation_report.pdf")
        assert res.status == OCRProcessingStatus.SUCCESS
        assert res.detected_type == OCRDocumentType.DIGITAL_PDF
        assert res.total_pages == 1
        assert expected_text in res.full_text
        assert res.pages[0].is_ocr_applied is False
        assert provider.invocations == 0

    def test_scanned_pdf_fallback_to_ocr(self):
        # Blank PDF has no text layer, should trigger OCR on image/blank page
        pdf_bytes = create_blank_scanned_pdf_bytes(1)
        ocr_text = "Statement by Rajesh Sharma on phone 9876543210"
        provider = MockOCRProvider(default_text=ocr_text)
        preprocessor = OCRPreprocessor(ocr_provider=provider)

        res = preprocessor.process_document(pdf_bytes, "scanned_fir.pdf")
        assert res.status == OCRProcessingStatus.SUCCESS
        assert res.total_pages == 1
        assert res.full_text == ocr_text

    def test_password_protected_pdf(self):
        encrypted_bytes = create_encrypted_pdf_bytes("secret123")
        preprocessor = OCRPreprocessor()
        res = preprocessor.process_document(encrypted_bytes, "protected.pdf")
        assert res.status == OCRProcessingStatus.PASSWORD_PROTECTED
        assert "encrypted or password-protected" in (res.error_message or "")

    def test_corrupt_pdf(self):
        corrupt_bytes = b"%PDF-1.4\nCorrupted binary payload\x00\xff\xfe random noise %%EOF"
        preprocessor = OCRPreprocessor()
        res = preprocessor.process_document(corrupt_bytes, "corrupt.pdf")
        assert res.status == OCRProcessingStatus.CORRUPTED_FILE

    def test_pdf_page_limit_enforcement(self):
        pdf_bytes = create_blank_scanned_pdf_bytes(num_pages=5)
        # Configure max_pages = 3
        preprocessor = OCRPreprocessor(max_pages=3)
        res = preprocessor.process_document(pdf_bytes, "multipage.pdf")
        assert res.status == OCRProcessingStatus.LIMIT_EXCEEDED
        assert "exceeds allowed limit of 3 pages" in (res.error_message or "")


# ==============================================================================
# 3. IMAGE PROCESSING TESTS
# ==============================================================================

class TestImageProcessing:
    """Validates PNG and JPEG decoding, OCR routing, and decompression bomb protection."""

    def test_png_image_ocr(self):
        png_bytes = create_valid_image_bytes(fmt="PNG")
        provider = MockOCRProvider(default_text="Vehicle plate DL 1C AA 1111 spotted.")
        preprocessor = OCRPreprocessor(ocr_provider=provider)

        res = preprocessor.process_document(png_bytes, "vehicle_snap.png")
        assert res.status == OCRProcessingStatus.SUCCESS
        assert res.detected_type == OCRDocumentType.IMAGE_PNG
        assert res.total_pages == 1
        assert res.pages[0].is_ocr_applied is True
        assert "DL 1C AA 1111" in res.full_text
        assert provider.invocations == 1

    def test_jpeg_image_ocr(self):
        jpeg_bytes = create_valid_image_bytes(fmt="JPEG")
        provider = MockOCRProvider(default_text="Transaction transfer to account 123456789012.")
        preprocessor = OCRPreprocessor(ocr_provider=provider)

        res = preprocessor.process_document(jpeg_bytes, "bank_slip.jpg")
        assert res.status == OCRProcessingStatus.SUCCESS
        assert res.detected_type == OCRDocumentType.IMAGE_JPEG
        assert res.total_pages == 1
        assert "123456789012" in res.full_text

    def test_decompression_bomb_dimension_limit(self):
        # Create image with width 200px, max_image_dimension set to 100px
        img_bytes = create_valid_image_bytes(fmt="PNG", size=(200, 50))
        preprocessor = OCRPreprocessor(max_image_dimension=100)

        res = preprocessor.process_document(img_bytes, "bomb.png")
        assert res.status == OCRProcessingStatus.LIMIT_EXCEEDED
        assert "exceed maximum allowed 100px" in (res.error_message or "")

    def test_malformed_image_payload(self):
        malformed_png = b"\x89PNG\r\n\x1a\nCorrupted byte stream without IHDR"
        preprocessor = OCRPreprocessor()
        res = preprocessor.process_document(malformed_png, "broken.png")
        assert res.status == OCRProcessingStatus.CORRUPTED_FILE


# ==============================================================================
# 4. OCR PROVIDER & FAILURE HANDLING TESTS
# ==============================================================================

class TestOCRProviderFailureHandling:
    """Validates failure modes when OCR provider is unavailable or raises exceptions."""

    def test_ocr_provider_engine_failure(self):
        png_bytes = create_valid_image_bytes("PNG")
        failing_provider = MockOCRProvider(should_fail=True)
        preprocessor = OCRPreprocessor(ocr_provider=failing_provider)

        res = preprocessor.process_document(png_bytes, "evidence.png")
        assert res.status == OCRProcessingStatus.OCR_ENGINE_FAILURE
        assert "Mock OCR provider simulated engine failure" in (res.error_message or "")

    def test_empty_ocr_result_produces_empty_document_status(self):
        png_bytes = create_valid_image_bytes("PNG")
        empty_provider = MockOCRProvider(default_text="    \n   ")
        preprocessor = OCRPreprocessor(ocr_provider=empty_provider)

        res = preprocessor.process_document(png_bytes, "blank_evidence.png")
        assert res.status == OCRProcessingStatus.EMPTY_DOCUMENT
        assert res.full_text == ""


# ==============================================================================
# 5. NORMALIZATION, PROVENANCE & AGENT 1 INTEGRATION TESTS
# ==============================================================================

class TestNormalizationAndAgent1Handoff:
    """Validates UTF-8 normalization, character offset tracking, and Agent 1 integration."""

    def test_utf8_control_character_sanitization(self):
        raw = "Witness statement\x00 with illegal\x08 control\x1f chars\r\nand clean lines."
        cleaned = clean_utf8_text(raw)
        assert "\x00" not in cleaned
        assert "\x08" not in cleaned
        assert "\x1f" not in cleaned
        assert "Witness statement with illegal control chars\nand clean lines." == cleaned

    def test_page_offset_tracking_provenance(self):
        page1_text = "Page 1: Suresh Verma was driving vehicle MH 02 AB 5678."
        page2_text = "Page 2: Transfer of funds to account 987654321098."

        writer = pypdf.PdfWriter()
        # Add 2 digital pages
        p1 = pypdf.PdfReader(io.BytesIO(create_digital_pdf_bytes(page1_text))).pages[0]
        p2 = pypdf.PdfReader(io.BytesIO(create_digital_pdf_bytes(page2_text))).pages[0]
        writer.add_page(p1)
        writer.add_page(p2)
        out = io.BytesIO()
        writer.write(out)
        multipage_pdf = out.getvalue()

        preprocessor = OCRPreprocessor()
        res = preprocessor.process_document(multipage_pdf, "multipage_case.pdf")
        assert res.status == OCRProcessingStatus.SUCCESS
        assert res.total_pages == 2

        # Verify page character offsets strictly match full_text slices
        p1_res = res.pages[0]
        p2_res = res.pages[1]
        assert res.full_text[p1_res.character_start:p1_res.character_end] == p1_res.text
        assert res.full_text[p2_res.character_start:p2_res.character_end] == p2_res.text

    @pytest.mark.asyncio
    async def test_end_to_end_ocr_to_agent1_handoff(self):
        """
        Validates complete pipeline:
        Document (PDF) -> OCRPreprocessor -> to_agent1_request() -> Agent 1 ExtractionEngine -> ExtractionJobResponse
        """
        document_text = "Rajesh Sharma drove vehicle MH 02 AB 5678 and transferred money from account 123456789012."
        pdf_bytes = create_digital_pdf_bytes(document_text)

        # 1. Preprocess document via OCRPreprocessor
        ocr_preprocessor = OCRPreprocessor()
        doc_result = ocr_preprocessor.process_document(pdf_bytes, "fir_report.pdf")
        assert doc_result.status == OCRProcessingStatus.SUCCESS

        # 2. Handoff to Agent 1 request
        extraction_request = ocr_preprocessor.to_agent1_request(doc_result)
        assert extraction_request.job_id == doc_result.document_id
        assert extraction_request.text == doc_result.full_text

        # 3. Agent 1 ExtractionEngine extracts structured entities & relationships
        agent1_engine = ExtractionEngine()  # uses deterministic fallback or mock
        extraction_response = await agent1_engine.extract(
            text=extraction_request.text,
            job_id=extraction_request.job_id,
            metadata=extraction_request.metadata,
        )

        assert extraction_response.extraction_job_id == doc_result.document_id
        assert len(extraction_response.extracted_entities) >= 2

        # Verify character offsets against source document text
        extraction_response.verify_source_spans(extraction_request.text)

        # Confirm expected entities extracted
        entity_texts = [e.extracted_text for e in extraction_response.extracted_entities]
        assert "MH 02 AB 5678" in entity_texts
        assert "123456789012" in entity_texts
