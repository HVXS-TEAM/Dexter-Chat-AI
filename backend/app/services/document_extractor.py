"""Text extraction for supported document formats."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

from app.config import settings

_OCR_READY = False


def _configure_tesseract() -> None:
    """Point pytesseract at the OCR engine, once per process.

    Raises ``ValueError`` with an explicit message when the engine is missing:
    an unreadable image must never be reported as an anonymous failure.
    """
    global _OCR_READY
    if _OCR_READY:
        return

    import pytesseract

    if settings.tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd
    try:
        pytesseract.get_tesseract_version()
    except Exception as exc:
        raise ValueError(
            "Le moteur OCR Tesseract est introuvable : renseignez TESSERACT_CMD dans "
            ".env (voir .env.example), puis redemarrez le backend."
        ) from exc
    _OCR_READY = True


def _ocr_arguments() -> str:
    """Return the extra tesseract arguments (language data directory)."""
    if settings.tessdata_dir:
        return f'--tessdata-dir "{settings.tessdata_dir}"'
    return ""


def extract_text(filename: str, file_bytes: bytes) -> str:
    """Extract plain text from PDF, DOCX, PPTX, images, TXT, or MD."""
    suffix = Path(filename).suffix.lower()
    if suffix in {".txt", ".md"}:
        try:
            text = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            text = file_bytes.decode("latin-1")
    elif suffix == ".pdf":
        from PyPDF2 import PdfReader

        reader = PdfReader(BytesIO(file_bytes))
        text = "\n\n".join(page.extract_text() or "" for page in reader.pages)
    elif suffix == ".docx":
        from docx import Document as DocxDocument

        document = DocxDocument(BytesIO(file_bytes))
        paragraphs = [paragraph.text for paragraph in document.paragraphs]
        paragraphs.extend(" | ".join(cell.text for cell in row.cells) for table in document.tables for row in table.rows)
        text = "\n\n".join(paragraphs)
    elif suffix == ".pptx":
        from pptx import Presentation

        presentation = Presentation(BytesIO(file_bytes))
        slides = []
        for slide in presentation.slides:
            slides.append("\n".join(shape.text for shape in slide.shapes if hasattr(shape, "text")))
        text = "\n\n".join(slides)
    elif suffix in {".png", ".jpg", ".jpeg"}:
        from PIL import Image

        import pytesseract

        _configure_tesseract()
        text = pytesseract.image_to_string(
            Image.open(BytesIO(file_bytes)),
            lang=settings.ocr_lang,
            config=_ocr_arguments(),
        )
    else:
        raise ValueError(f"Unsupported document type: {suffix or 'unknown'}")

    cleaned = text.strip()
    if not cleaned:
        raise ValueError("The document does not contain extractable text.")
    return cleaned
