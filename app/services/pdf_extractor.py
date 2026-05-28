from io import BytesIO

from PyPDF2 import PdfReader

MAX_PDF_BYTES = 10 * 1024 * 1024  # 10 MB


class PdfExtractionError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


def extract_text_from_pdf(file_bytes: bytes) -> str:
    if len(file_bytes) > MAX_PDF_BYTES:
        raise PdfExtractionError("PDF file is too large. Maximum size is 10 MB.", 413)

    try:
        reader = PdfReader(BytesIO(file_bytes))
    except Exception as exc:
        raise PdfExtractionError(f"Could not read PDF file: {exc}") from exc

    if reader.is_encrypted:
        try:
            reader.decrypt("")
        except Exception:
            raise PdfExtractionError("Encrypted PDFs are not supported.")

    parts: list[str] = []
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            parts.append(page_text.strip())

    text = "\n\n".join(parts).strip()
    if not text:
        raise PdfExtractionError("No extractable text found in this PDF.")

    return text
