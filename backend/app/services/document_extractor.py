"""Text extraction for supported document formats."""

from __future__ import annotations

import os
import zipfile
from io import BytesIO
from pathlib import Path

from app.config import settings

_OCR_READY = False


class UnreadableDocumentError(Exception):
    """The uploaded file cannot be turned into text.

    Raised for content-level failures the user can act on (corrupt or truncated
    file, document without extractable text). Server-side failures (missing OCR
    engine, unavailable embedding model, unexpected bug) must never use this
    class: the upload endpoint reports them as a server error instead of
    presenting them as the user's fault.
    """


def _configure_tesseract() -> None:
    """Point pytesseract at the OCR engine, once per process.

    The language data directory is exported through ``TESSDATA_PREFIX``
    (see the comment below) instead of the ``--tessdata-dir`` option.

    Raises ``ValueError`` with an explicit message when the engine is missing:
    an unreadable image must never be reported as an anonymous failure.
    """
    global _OCR_READY
    if _OCR_READY:
        return

    import pytesseract

    if settings.tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd
    if settings.tessdata_dir:
        # Tesseract reads its language data location from TESSDATA_PREFIX.
        # The ``--tessdata-dir`` command-line option cannot be used here: on
        # Windows pytesseract splits the option string with
        # ``shlex.split(config, posix=False)``, which keeps the quotes and
        # makes Tesseract fail with
        # 'Error opening data file "<dir>"/fra.traineddata'.
        os.environ["TESSDATA_PREFIX"] = settings.tessdata_dir
    try:
        pytesseract.get_tesseract_version()
    except Exception as exc:
        raise ValueError(
            "Le moteur OCR Tesseract est introuvable : renseignez TESSERACT_CMD dans "
            ".env (voir .env.example), puis redemarrez le backend."
        ) from exc
    _OCR_READY = True


def _extract_pdf(file_bytes: bytes) -> str:
    """Read the text layer of a PDF, or fail explicitly on an unreadable file."""
    from PyPDF2 import PdfReader
    from PyPDF2.errors import PyPdfError

    try:
        reader = PdfReader(BytesIO(file_bytes))
        return "\n\n".join(page.extract_text() or "" for page in reader.pages)
    except (PyPdfError, OSError, ValueError) as exc:
        raise UnreadableDocumentError(f"The PDF file cannot be read: {exc}") from exc


def _extract_docx(file_bytes: bytes) -> str:
    """Read paragraphs and tables of a DOCX, or fail explicitly on an unreadable file."""
    from docx import Document as DocxDocument
    from docx.opc.exceptions import PackageNotFoundError

    try:
        document = DocxDocument(BytesIO(file_bytes))
        paragraphs = [paragraph.text for paragraph in document.paragraphs]
        paragraphs.extend(" | ".join(cell.text for cell in row.cells) for table in document.tables for row in table.rows)
        return "\n\n".join(paragraphs)
    except (PackageNotFoundError, zipfile.BadZipFile) as exc:
        raise UnreadableDocumentError(f"The DOCX file cannot be read: {exc}") from exc


def _extract_pptx(file_bytes: bytes) -> str:
    """Read the text of every slide of a PPTX, or fail explicitly on an unreadable file."""
    from pptx import Presentation
    from pptx.exc import PackageNotFoundError

    try:
        presentation = Presentation(BytesIO(file_bytes))
        slides = []
        for slide in presentation.slides:
            slides.append("\n".join(shape.text for shape in slide.shapes if hasattr(shape, "text")))
        return "\n\n".join(slides)
    except (PackageNotFoundError, zipfile.BadZipFile) as exc:
        raise UnreadableDocumentError(f"The PPTX file cannot be read: {exc}") from exc


def _extract_image_text(file_bytes: bytes) -> str:
    """OCR an image. A decoding failure means "unreadable file"; an OCR engine failure does not.

    Animated (GIF) or multi-page (TIFF) inputs are read on their first frame only:
    course material is a static capture, and reading every frame would multiply
    the OCR cost without user benefit.
    """
    import pytesseract
    from PIL import Image

    _configure_tesseract()
    try:
        image = Image.open(BytesIO(file_bytes))
        # Decode at once: a truncated or corrupt image only fails here, never during
        # OCR. PIL signals undecodable data with UnidentifiedImageError, a subclass
        # of OSError, so a single OSError handler covers every decoding failure.
        image.load()
        try:
            # First frame only for animated/multi-page inputs (GIF, TIFF).
            image.seek(0)
            image.load()
        except EOFError as exc:
            raise UnreadableDocumentError(f"The image file cannot be read: {exc}") from exc
    except OSError as exc:
        raise UnreadableDocumentError(f"The image file cannot be read: {exc}") from exc
    if image.mode not in {"RGB", "L"}:
        image = image.convert("RGB")
    # pytesseract.TesseractError is a server-side problem: it is deliberately left
    # to propagate so the endpoint answers with a server error.
    return pytesseract.image_to_string(image, lang=settings.ocr_lang)


def extract_text(filename: str, file_bytes: bytes) -> str:
    """Extract plain text from PDF, DOCX, PPTX, images, TXT, or MD.

    Supported images: PNG, JPG, JPEG, WEBP, BMP, GIF and TIF/TIFF (first frame
    only for animated or multi-page inputs).

    Failures caused by the uploaded content raise ``UnreadableDocumentError`` so the
    caller can answer with a client error; failures caused by the server environment
    keep their own exception type and are reported as server errors.
    """
    suffix = Path(filename).suffix.lower()
    if suffix in {".txt", ".md"}:
        try:
            text = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            text = file_bytes.decode("latin-1")
    elif suffix == ".pdf":
        text = _extract_pdf(file_bytes)
    elif suffix == ".docx":
        text = _extract_docx(file_bytes)
    elif suffix == ".pptx":
        text = _extract_pptx(file_bytes)
    elif suffix in {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tif", ".tiff"}:
        text = _extract_image_text(file_bytes)
    else:
        raise ValueError(f"Unsupported document type: {suffix or 'unknown'}")

    cleaned = text.strip()
    if not cleaned:
        raise UnreadableDocumentError("The document does not contain extractable text.")
    return cleaned
