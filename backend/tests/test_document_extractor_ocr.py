"""Regression tests for image OCR (``.png`` / ``.jpg`` / ``.jpeg``).

They cover a bug that made every image upload fail with HTTP 422:
``--tessdata-dir "<dir>"`` was passed to pytesseract, and on Windows
``shlex.split(config, posix=False)`` keeps the quotes, so Tesseract answered
``Error opening data file "<dir>"/fra.traineddata`` and could not load any
language. The fix exports the directory through ``TESSDATA_PREFIX`` instead.

Tesseract is an external binary: the tests are skipped, with an explicit
reason shown by pytest, when the engine or the language data is not installed
on the machine. They never fail silently (AGENTS.md, rules 6 and 12).
"""

from __future__ import annotations

import io
import os
from pathlib import Path

import pytest

from app.config import settings
from app.services import document_extractor
from app.services.document_extractor import extract_text

IMAGE_TEXT = "Dexter OCR 12345"
FONT_CANDIDATES = ("arial.ttf", "C:/Windows/Fonts/arial.ttf", "DejaVuSans.ttf")


def _engine_unavailable_reason() -> str:
    """Return the reason why the OCR engine cannot be used, or an empty string."""
    try:
        document_extractor._configure_tesseract()
    except Exception as exc:  # noqa: BLE001 - the message is reported to pytest
        return f"moteur OCR Tesseract indisponible : {exc}"
    return ""


def _language_data_path() -> Path | None:
    """Return the language data file used by Tesseract, or ``None`` if missing."""
    filename = f"{settings.ocr_lang}.traineddata"
    if settings.tessdata_dir:
        candidate = Path(settings.tessdata_dir) / filename
        return candidate if candidate.is_file() else None
    if settings.tesseract_cmd:
        candidate = Path(settings.tesseract_cmd).parent / "tessdata" / filename
        return candidate if candidate.is_file() else None
    return None


@pytest.fixture(scope="module")
def ocr_engine() -> None:
    """Skip the whole module, with an explicit reason, when OCR is unusable."""
    reason = _engine_unavailable_reason()
    if reason:
        pytest.skip(reason)
    language_data = _language_data_path()
    if language_data is None:
        pytest.skip(
            f"donnees de langue '{settings.ocr_lang}' introuvables "
            f"(TESSDATA_DIR={settings.tessdata_dir!r}) : renseignez TESSDATA_DIR dans .env"
        )


def _image_with_text() -> bytes:
    """Render ``IMAGE_TEXT`` into a PNG image, in memory."""
    from PIL import Image, ImageDraw, ImageFont

    font = None
    for candidate in FONT_CANDIDATES:
        try:
            font = ImageFont.truetype(candidate, 48)
            break
        except OSError:
            continue
    if font is None:
        pytest.skip(f"aucune police utilisable parmi {FONT_CANDIDATES} pour generer l'image")

    image = Image.new("RGB", (900, 200), "white")
    ImageDraw.Draw(image).text((40, 60), IMAGE_TEXT, fill="black", font=font)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_tessdata_dir_is_exported_through_environment(ocr_engine):
    """The configured directory must reach Tesseract through TESSDATA_PREFIX."""
    if not settings.tessdata_dir:
        pytest.skip("TESSDATA_DIR vide : Tesseract utilise son dossier par defaut")

    document_extractor._configure_tesseract()

    assert Path(os.environ["TESSDATA_PREFIX"]) == Path(settings.tessdata_dir)


def test_extract_text_reads_text_from_image(ocr_engine):
    """A PNG containing text must be readable (would fail with the old option)."""
    text = extract_text("ocr_check.png", _image_with_text())

    assert "12345" in text, f"texte OCR inattendu : {text!r}"
    assert "Dexter" in text, f"texte OCR inattendu : {text!r}"