"""
SEAGAS — Evidence (proof attached to projects, certifications and recommended activities)

A piece of evidence is either
- a file: PDF, JPG, PNG, Word (.docx) or PowerPoint (.pptx). The type is read
  from the file's content, never from the name or the browser's Content-Type,
  so a renamed .html, .svg or macro file is refused. At most MAX_BYTES.
- a link: an http(s) URL, e.g. a YouTube / Drive video, a GitHub repository or
  a credential page. Videos are always links, never uploads.
At most MAX_PER_ITEM pieces per project / certification / activity. A recommended
activity needs at least one piece before it can be marked complete
(routers/progress.py).

The bytes are stored in the database; list queries only select META_COLUMNS.
Used by routers/students.py, routers/progress.py and routers/advisor.py.
"""

import io
import re
import unicodedata
import zipfile
from urllib.parse import urlparse

from fastapi import HTTPException
from sqlalchemy import text

MAX_BYTES = 5 * 1024 * 1024      # keep in sync with chk_evidence_kind in database/schema.sql
MAX_PER_ITEM = 5
MAX_LINK_LENGTH = 2000

DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
PPTX = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
EXTENSIONS = {
    "image/jpeg": (".jpg", ".jpeg"), "image/png": (".png",), "application/pdf": (".pdf",),
    DOCX: (".docx",), PPTX: (".pptx",),
}
ALLOWED_TEXT = "PDF, JPG, PNG, Word (.docx) or PowerPoint (.pptx)"

META_COLUMNS = ("file_id, kind, link_url, project_id, cert_id, progress_id, file_name, "
                "content_type, size_bytes, uploaded_at")


def _office_type(data: bytes):
    """DOCX / PPTX from the parts inside the zip; None for anything else (or macros)"""
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            names = set(z.namelist())
    except (zipfile.BadZipFile, ValueError):
        return None
    if "[Content_Types].xml" not in names or any(n.lower().endswith("vbaproject.bin") for n in names):
        return None
    if "word/document.xml" in names:
        return DOCX
    if "ppt/presentation.xml" in names:
        return PPTX
    return None


def detect_type(data: bytes):
    """Content type from the file's content, or None if it is not an allowed type"""
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"%PDF-"):
        return "application/pdf"
    if data.startswith(b"PK\x03\x04"):
        return _office_type(data)
    return None


def clean_name(name, content_type):
    """A safe display name: no folders or control characters, extension matching the real type"""
    name = re.split(r"[\\/]", name or "")[-1]
    name = "".join(ch for ch in name if unicodedata.category(ch)[0] != "C").strip(" .")
    if not name:
        name = "evidence"
    exts = EXTENSIONS[content_type]
    if not name.lower().endswith(exts):
        name += exts[0]
    if len(name) > 255:
        stem, dot, ext = name.rpartition(".")
        name = stem[:250 - len(ext)] + dot + ext
    return name


def clean_link(url, title):
    """(url, display name) for a link, or 400 if the URL is not a plain http(s) address"""
    url = (url or "").strip()
    parsed = urlparse(url)
    if (parsed.scheme.lower() not in ("http", "https") or not parsed.netloc
            or len(url) > MAX_LINK_LENGTH or re.search(r"\s", url)):
        raise HTTPException(status_code=400,
                            detail="Enter a full web address starting with http:// or https://")
    name = "".join(ch for ch in (title or "") if unicodedata.category(ch)[0] != "C").strip()
    return url, (name or parsed.netloc + parsed.path.rstrip("/"))[:255]


def _check_room(db, key, parent_id):
    count = db.execute(text(f"SELECT COUNT(*) FROM student_evidence_files WHERE {key} = :p"),
                       {"p": str(parent_id)}).scalar()
    if count >= MAX_PER_ITEM:
        raise HTTPException(status_code=400,
                            detail=f"You can attach at most {MAX_PER_ITEM} pieces of evidence. Delete one first.")


def save_file(db, profile_id, key, parent_id, upload):
    """Store an uploaded file as evidence. key: project_id / cert_id / progress_id.

    The caller has checked that the parent belongs to profile_id. Commits.
    """
    _check_room(db, key, parent_id)
    data = upload.file.read(MAX_BYTES + 1)
    if not data:
        raise HTTPException(status_code=400, detail="The file is empty.")
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="The file is larger than 5 MB.")
    content_type = detect_type(data)
    if not content_type:
        raise HTTPException(status_code=400, detail=f"Only {ALLOWED_TEXT} files can be attached. "
                                                    "For a video, add a link instead.")
    row = db.execute(
        text(f"""
            INSERT INTO student_evidence_files (profile_id, {key}, kind, file_name, content_type, size_bytes, data)
            VALUES (:pid, :parent, 'file', :name, :ctype, :size, :data)
            RETURNING {META_COLUMNS}
        """),
        {"pid": str(profile_id), "parent": str(parent_id),
         "name": clean_name(upload.filename, content_type), "ctype": content_type,
         "size": len(data), "data": data}
    ).fetchone()
    db.commit()
    return dict(row._mapping)


def save_link(db, profile_id, key, parent_id, url, title=None):
    """Store a link as evidence (same rules as save_file). Commits."""
    _check_room(db, key, parent_id)
    url, name = clean_link(url, title)
    row = db.execute(
        text(f"""
            INSERT INTO student_evidence_files (profile_id, {key}, kind, file_name, link_url)
            VALUES (:pid, :parent, 'link', :name, :url)
            RETURNING {META_COLUMNS}
        """),
        {"pid": str(profile_id), "parent": str(parent_id), "name": name, "url": url}
    ).fetchone()
    db.commit()
    return dict(row._mapping)


def attach_files(db, rows, key):
    """Add a "files" list (metadata only) to each project, certification or activity dict.

    key: "project_id", "cert_id" or "progress_id"
    """
    ids = [str(r[key]) for r in rows]
    by_parent = {i: [] for i in ids}
    if ids:
        files = db.execute(
            text(f"""
                SELECT {META_COLUMNS} FROM student_evidence_files
                WHERE {key} = ANY(CAST(:ids AS uuid[]))
                ORDER BY uploaded_at
            """),
            {"ids": ids}
        ).fetchall()
        for f in files:
            by_parent[str(f._mapping[key])].append(dict(f._mapping))
    for r in rows:
        r["files"] = by_parent[str(r[key])]
    return rows
