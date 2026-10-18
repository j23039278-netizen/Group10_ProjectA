"""
SEAGAS — Evidence files (photos / PDFs attached to projects and certifications)

Rules (also described in database/schema.sql, table student_evidence_files):
- JPG, PNG or PDF only. The type is read from the file's first bytes, never from
  the name or the browser's Content-Type, so a renamed .html or .svg is refused.
- At most MAX_BYTES per file and MAX_PER_ITEM files per project / certification.
- The bytes are stored in the database; list queries only select META_COLUMNS.

Used by routers/students.py (upload, download, delete) and routers/advisor.py
(file lists on the student detail page).
"""

import re
import unicodedata

from sqlalchemy import text

MAX_BYTES = 5 * 1024 * 1024      # keep in sync with the CHECK on size_bytes
MAX_PER_ITEM = 5

# (leading bytes, content type, extension)
SIGNATURES = (
    (b"\xff\xd8\xff",          "image/jpeg",      ".jpg"),
    (b"\x89PNG\r\n\x1a\n",     "image/png",       ".png"),
    (b"%PDF-",                 "application/pdf", ".pdf"),
)
EXTENSIONS = {"image/jpeg": (".jpg", ".jpeg"), "image/png": (".png",), "application/pdf": (".pdf",)}

META_COLUMNS = "file_id, project_id, cert_id, file_name, content_type, size_bytes, uploaded_at"


def detect_type(data: bytes):
    """Content type from the file's leading bytes, or None if it is not an allowed type"""
    for magic, content_type, _ in SIGNATURES:
        if data.startswith(magic):
            return content_type
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


def attach_files(db, rows, key):
    """Add a "files" list (metadata only) to each project or certification dict.

    key: "project_id" or "cert_id"
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
