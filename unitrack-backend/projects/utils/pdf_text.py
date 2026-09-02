import io

from pypdf import PdfReader
from pypdf.errors import PdfReadError

# Bounds enforced when extracting document text at upload time.
MAX_BYTES = 10 * 1024 * 1024  # 10 MB
MAX_PAGES = 60


def extract_pdf_text(file_obj):
    """Extract text from an uploaded PDF.

    Returns a ``(text, status, error)`` triple. Status is one of
    ``pending`` (unchanged), ``success``, ``empty``, ``too_large``, ``error``.
    Never raises for document-level problems; unexpected errors are reported
    through the status/error fields.
    """
    try:
        file_obj.seek(0)
        data = file_obj.read()
        file_obj.seek(0)

        if len(data) > MAX_BYTES:
            return ("", "too_large", f"File exceeds {MAX_BYTES} byte limit.")

        reader = PdfReader(file_obj)
        if len(reader.pages) > MAX_PAGES:
            return ("", "too_large", f"File exceeds {MAX_PAGES} page limit.")

        parts = []
        for page in reader.pages:
            try:
                text = page.extract_text() or ""
            except Exception as exc:  # noqa: BLE001 - per-page errors degrade gracefully
                text = ""
            parts.append(text)

        text = "\n".join(parts).strip()
        if not text:
            return ("", "empty", "No extractable text found (blank or scanned PDF).")

        return (text, "success", "")
    except PdfReadError as exc:
        return ("", "error", f"Could not parse PDF: {exc}")
    except Exception as exc:  # noqa: BLE001 - never surface raw parser crashes
        return ("", "error", f"Text extraction failed: {exc}")