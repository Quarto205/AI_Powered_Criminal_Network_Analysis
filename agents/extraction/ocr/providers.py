"""
Provider abstraction layer for OCR text extraction.
Decouples document processing logic from concrete OCR engine binaries or SDKs.
"""

from typing import Callable, Dict, Optional, Protocol
import io

from agents.extraction.ocr.exceptions import OCREngineFailureError


class OCRProvider(Protocol):
    """Abstract interface for OCR image-to-text recognition."""
    def extract_text_from_image(self, image_bytes: bytes) -> str:
        """Extracts UTF-8 text from raw image bytes."""
        ...


class MockOCRProvider:
    """
    Deterministic OCR provider for unit tests, offline development,
    and synthetic demo reproducibility.
    """
    def __init__(
        self,
        default_text: str = "OCR EXTRACTED TEXT MOCK",
        canned_map: Optional[Dict[bytes, str]] = None,
        custom_handler: Optional[Callable[[bytes], str]] = None,
        should_fail: bool = False,
    ):
        self.default_text = default_text
        self.canned_map = canned_map or {}
        self.custom_handler = custom_handler
        self.should_fail = should_fail
        self.invocations = 0

    def extract_text_from_image(self, image_bytes: bytes) -> str:
        self.invocations += 1
        if self.should_fail:
            raise OCREngineFailureError("Mock OCR provider simulated engine failure.")

        if self.custom_handler:
            return self.custom_handler(image_bytes)

        if image_bytes in self.canned_map:
            return self.canned_map[image_bytes]

        return self.default_text


class PaddleOCRAdapter:
    """
    Concrete adapter for the PaddleOCR engine.
    Encapsulates PaddleOCR initialization and execution safely without tight coupling.
    """
    def __init__(self, lang: str = "en", use_angle_cls: bool = True):
        self.lang = lang
        self.use_angle_cls = use_angle_cls
        self._engine = None
        self._initialized = False

    def _get_engine(self):
        if not self._initialized:
            try:
                from paddleocr import PaddleOCR
                self._engine = PaddleOCR(use_angle_cls=self.use_angle_cls, lang=self.lang)
                self._initialized = True
            except Exception as exc:
                raise OCREngineFailureError(
                    f"PaddleOCR is not available or failed to initialize: {exc}"
                ) from exc
        return self._engine

    def extract_text_from_image(self, image_bytes: bytes) -> str:
        engine = self._get_engine()
        try:
            from PIL import Image
            import numpy as np

            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            img_array = np.array(image)
            result = engine.ocr(img_array, cls=self.use_angle_cls)

            extracted_lines = []
            if result and result[0]:
                for line in result[0]:
                    if line and len(line) >= 2 and line[1] and len(line[1]) >= 1:
                        text_content = line[1][0]
                        if text_content and text_content.strip():
                            extracted_lines.append(text_content.strip())

            return "\n".join(extracted_lines)
        except Exception as exc:
            if isinstance(exc, OCREngineFailureError):
                raise
            raise OCREngineFailureError(f"PaddleOCR execution error: {exc}") from exc
