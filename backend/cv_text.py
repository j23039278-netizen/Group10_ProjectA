"""
SEAGAS — Text of an uploaded CV (PDF or Word .docx)

The file type is checked from its content (evidence.detect_type), the same way as
evidence files. Scanned PDFs have no text layer; they give an empty string and
the router asks the student for a text-based file instead.
"""

import io
import re
import zipfile
from xml.etree import ElementTree

from fastapi import HTTPException

import evidence

PDF = "application/pdf"
CV_TYPES = {PDF: ".pdf", evidence.DOCX: ".docx"}
MAX_TEXT = 60_000                 # characters passed to the NLP (a CV is far shorter)
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def _pdf_text(data):
    from pypdf import PdfReader     # imported here so the backend starts without it
    try:
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted:
            raise HTTPException(status_code=400, detail="This PDF is password-protected. Please upload an unprotected copy.")
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="This PDF could not be read. Please save it again and upload it.")


def _docx_text(data):
    """Paragraph text of word/document.xml (tables included), no extra package needed"""
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            root = ElementTree.fromstring(z.read("word/document.xml"))
    except Exception:
        raise HTTPException(status_code=400, detail="This Word file could not be read. Please save it again and upload it.")
    lines = []
    for p in root.iter(f"{W}p"):
        line = "".join(t.text or "" for t in p.iter(f"{W}t"))
        if line.strip():
            lines.append(line)
    return "\n".join(lines)


def read_cv(data):
    """(content_type, text) of a CV file, or 400 for anything but a PDF or .docx"""
    content_type = evidence.detect_type(data)
    if content_type not in CV_TYPES:
        raise HTTPException(status_code=400, detail="Upload your CV as a PDF or Word (.docx) file.")
    text = _pdf_text(data) if content_type == PDF else _docx_text(data)
    text = re.sub(r"[ \t]+", " ", text).strip()
    return content_type, text[:MAX_TEXT]
