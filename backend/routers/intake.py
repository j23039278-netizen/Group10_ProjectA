"""
SEAGAS — New student intake (how student accounts are created)

Advisors do all of it; admins can only look (lists, students and emails).

1. An advisor uploads a list of new students (Excel .xlsx or .csv) with their full
   name, student ID and school email (given by the university), phone number,
   course (Computer Science, Business or Information and Communications
   Technology) and programme (one of the course's programmes).
                                                                POST /batches
2. The advisor checks the list, can correct or reject a student, then creates the
   accounts. Each student gets a temporary password.
   PATCH /rows/{id}, POST /rows/{id}/reject, POST /batches/{id}/create-accounts
3. The student's school email receives the student ID, school email and
   temporary password (notifications.py; stored in the outbox when no mail
   server is configured). The advisor can resend them.          GET /outbox
4. The student signs in with school email + student ID + temporary password and
   must choose a new password first (routers/auth.py).

Phone numbers stay in student_intake_rows. The personal_email column is only filled
for lists uploaded before the Personal Email column was removed (12 Nov 2026).
Use made-up data when testing (NFR-05).
"""

import csv
import io
import re
import secrets
from typing import List, Literal, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

import audit
import notifications
import programmes
from advisor_scope import COURSE_NAMES, check_course, courses_of
from database import get_db
from routers.auth import ROLE_EMAIL_DOMAINS, get_current_user, hash_password, password_error

router = APIRouter()

MAX_FILE_BYTES = 2 * 1024 * 1024
MAX_ROWS = 1000
STUDENT_DOMAIN = ROLE_EMAIL_DOMAINS["student"]
STUDENT_NUMBER_RE = re.compile(r"^[0-9]{9}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^\+?[0-9 ()\-]{7,25}$")

# Header words that identify each column (case-insensitive, first match wins)
# The login email goes to the school email, so a plain "Email" column is the school email
COLUMN_WORDS = {
    "full_name":      ("full name", "name", "student name"),
    "student_number": ("student id", "student number", "student no", "matric"),
    "school_email":   ("school email", "student email", "university email", "email", "e-mail"),
    "phone":          ("phone", "mobile", "contact", "tel"),
    "course":         ("course", "faculty"),
    "programme":      ("programme", "program", "major"),
}
REQUIRED_COLUMNS = "Full Name, Student ID, School Email, Phone Number, Course, Programme"

# What the Course column may say (case-insensitive) -> stored code
COURSES = {
    "cs": "CS", "computer science": "CS",
    "business": "BUSINESS",
    "ict": "ICT", "information and communications technology": "ICT",
    "information & communications technology": "ICT",
    "information and communication technology": "ICT", "information & communication technology": "ICT",
}


def parse_course(value):
    """CS / BUSINESS / ICT, or None if the text is not one of the three courses"""
    return COURSES.get(" ".join((value or "").lower().split()))

ROW_COLUMNS = """r.row_id, r.batch_id, r.line_number, r.full_name, r.phone, r.course, r.programme,
                 r.student_number, r.school_email, r.status, r.user_id, r.note, r.processed_at"""


# ── Permission checks ─────────────────────────────────────────
def require_staff(user):
    if user.role not in ("advisor", "admin"):
        raise HTTPException(status_code=403, detail="Access denied. Advisor or Admin role required.")


def require_advisor(user):
    """Changing anything is the advisor's job; admins only look"""
    if user.role != "advisor":
        raise HTTPException(status_code=403, detail="Access denied. Advisors handle new students; admins can only view them.")


def parse_id(value, what="Not found"):
    """Malformed ids are just "not found", like the other ID routes"""
    try:
        return str(UUID(value))
    except ValueError:
        raise HTTPException(status_code=404, detail=what)


def get_batch(db, batch_id, user):
    batch = db.execute(text("SELECT * FROM student_intake_batches WHERE batch_id = :b"),
                       {"b": parse_id(batch_id, "List not found")}).fetchone()
    # Advisors see only the lists they uploaded; admins see all
    if not batch or (user.role != "admin" and str(batch.uploaded_by) != str(user.user_id)):
        raise HTTPException(status_code=404, detail="List not found")
    return batch


# ── Reading the uploaded file ─────────────────────────────────
def read_table(name, data):
    """Rows of cell strings from a .csv or .xlsx file (first row = headers)"""
    lower = (name or "").lower()
    if lower.endswith(".xlsx"):
        if not data.startswith(b"PK"):
            raise HTTPException(status_code=400, detail="This is not a valid .xlsx file.")
        from openpyxl import load_workbook
        try:
            wb = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
        except Exception:
            raise HTTPException(status_code=400, detail="The Excel file could not be read.")
        ws = wb.worksheets[0]
        rows = [["" if c is None else str(c).strip() for c in row]
                for row in ws.iter_rows(values_only=True, max_row=MAX_ROWS + 2)]
        wb.close()
        return rows
    if lower.endswith(".csv"):
        try:
            content = data.decode("utf-8-sig")
        except UnicodeDecodeError:
            content = data.decode("latin-1")
        return [[c.strip() for c in row] for row in csv.reader(io.StringIO(content))]
    raise HTTPException(status_code=400, detail="Upload an Excel (.xlsx) or CSV (.csv) file.")


def find_columns(header):
    cols = {}
    names = [h.lower().strip() for h in header]
    for key, words in COLUMN_WORDS.items():
        for word in words:
            hit = next((i for i, h in enumerate(names) if word in h and i not in cols.values()), None)
            if hit is not None:
                cols[key] = hit
                break
    missing = [k for k in ("full_name", "student_number", "school_email", "course", "programme")
               if k not in cols]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"The first row must contain the column names: {REQUIRED_COLUMNS}.")
    return cols


def clean_row(cells, cols, course_programmes):
    """(values, None) or (None, error message) for one data row.
    course_programmes: programmes.by_course(db)"""
    cell = lambda k: (cells[cols[k]] if k in cols and cols[k] < len(cells) else "").strip()
    name, phone = " ".join(cell("full_name").split()), cell("phone")
    number, school_email = cell("student_number"), cell("school_email").lower()
    if phone.endswith(".0") and phone[:-2].isdigit():   # Excel stores numbers as floats
        phone = phone[:-2]
    if number.endswith(".0") and number[:-2].isdigit():
        number = number[:-2]
    if not name:
        return None, "full name is empty"
    if len(name) > 255:
        return None, "full name is too long"
    if not STUDENT_NUMBER_RE.match(number):
        return None, "student ID must be exactly 9 digits"
    if not EMAIL_RE.match(school_email) or not school_email.endswith("@" + STUDENT_DOMAIN) or len(school_email) > 255:
        return None, f"school email must end with @{STUDENT_DOMAIN}"
    if phone and not PHONE_RE.match(phone):
        return None, "phone number is not valid"
    course = parse_course(cell("course"))
    if not course:
        return None, "course must be Computer Science, Business or Information and Communications Technology"
    programme = course_programmes.get(course, {}).get(" ".join(cell("programme").lower().split()))
    if not programme:
        return None, f"programme must be one of the {COURSE_NAMES[course]} programmes"
    return {"full_name": name, "student_number": number, "school_email": school_email,
            "phone": phone or None, "course": course, "programme": programme}, None


# ── Advisor: Excel template (Course and Programme are drop-down lists) ──
TEMPLATE_ROWS = [
    ("Example Student", "199000001", "199000001@student.newinti.edu.my", "+60 12-345 6789",
     "Computer Science", "Bachelor of Computer Science (Software Engineering)"),
    ("Another Student", "199000002", "199000002@student.newinti.edu.my", "+60 13-222 3333",
     "Business", "Bachelor of Business (Marketing)"),
    ("Third Student", "199000003", "199000003@student.newinti.edu.my", "+60 14-444 5555",
     "Information and Communications Technology",
     "Bachelor of Information and Communications Technology (Web and Mobile Development)"),
]


@router.get("/template")
def download_template(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """An .xlsx with the six columns. Course only accepts the courses this advisor may add;
    Programme only the programmes of the course chosen in the same row."""
    require_advisor(current_user)
    from openpyxl import Workbook
    from openpyxl.styles import Font
    from openpyxl.workbook.defined_name import DefinedName
    from openpyxl.worksheet.datavalidation import DataValidation

    codes = [c for c in COURSE_NAMES if c in courses_of(current_user)]
    names = [COURSE_NAMES[c] for c in codes]
    wb = Workbook()
    ws = wb.active
    ws.title = "New students"
    ws.append(["Full Name", "Student ID", "School Email", "Phone Number", "Course", "Programme"])
    for cell in ws[1]:
        cell.font = Font(bold=True)
    for row in TEMPLATE_ROWS:
        if row[4] in names:
            ws.append(row)
    for col, width in zip("ABCDEF", (28, 14, 36, 20, 40, 70)):
        ws.column_dimensions[col].width = width
    # Text, so Excel keeps the ID as typed: new rows (the column) and the example rows
    ws.column_dimensions["B"].number_format = "@"
    for cell in ws["B"][1:]:
        cell.number_format = "@"

    # A hidden sheet with each course's programmes; one named range per course
    # (Computer_Science, Business, Information_and_Communications_Technology) so the
    # Programme list can follow the Course cell
    lists = wb.create_sheet("Lists")
    lists.sheet_state = "hidden"
    by = programmes.by_course(db)
    for col, (code, course_name) in enumerate(zip(codes, names), start=1):
        letter = chr(64 + col)
        lists.cell(row=1, column=col, value=course_name)
        items = list(by.get(code, {}).values())
        for i, prog in enumerate(items, start=2):
            lists.cell(row=i, column=col, value=prog)
        ref = f"Lists!${letter}$2:${letter}${max(len(items), 1) + 1}"
        wb.defined_names[course_name.replace(" ", "_")] = DefinedName(course_name.replace(" ", "_"), attr_text=ref)

    course_dv = DataValidation(type="list", formula1=f'"{",".join(names)}"', allow_blank=False,
                               showErrorMessage=True, errorTitle="Course",
                               error=f"Choose {' or '.join(names)} from the list.")
    programme_dv = DataValidation(type="list", formula1='INDIRECT(SUBSTITUTE($E2," ","_"))', allow_blank=False,
                                  showErrorMessage=True, errorTitle="Programme",
                                  error="Choose the course first, then one of its programmes from the list.")
    ws.add_data_validation(course_dv)
    ws.add_data_validation(programme_dv)
    course_dv.add("E2:E1001")      # one row per student, up to the 1,000-student limit
    programme_dv.add("F2:F1001")
    ws.freeze_panes = "A2"

    out = io.BytesIO()
    wb.save(out)
    return Response(
        content=out.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="new_students_template.xlsx"'},
    )


# ── Advisor: upload a list ────────────────────────────────────
@router.post("/batches", status_code=201)
def upload_batch(
    request: Request,
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload new students (see REQUIRED_COLUMNS). Bad rows are skipped and listed. A student ID or
    school email used twice refuses the whole file: nothing is saved until the advisor corrects it."""
    require_advisor(current_user)
    data = file.file.read(MAX_FILE_BYTES + 1)
    if len(data) > MAX_FILE_BYTES:
        raise HTTPException(status_code=413, detail="The file is larger than 2 MB.")
    table = [r for r in read_table(file.filename, data) if any(c for c in r)]
    if len(table) < 2:
        raise HTTPException(status_code=400, detail="The file has no student rows.")
    if len(table) - 1 > MAX_ROWS:
        raise HTTPException(status_code=400, detail=f"At most {MAX_ROWS} students per file.")
    cols = find_columns(table[0])

    # Student IDs and school emails already used: value -> where
    used_ids, used_emails = {}, {}
    for number, email, where in db.execute(text("""
        SELECT student_number, lower(email), 'an existing account' FROM users
        UNION ALL
        SELECT student_number, lower(school_email), 'a student waiting on an earlier list'
        FROM student_intake_rows WHERE status = 'pending'
    """)).fetchall():
        used_ids[number] = where
        used_emails[email] = where
    rows, skipped, duplicates = [], [], []
    course_programmes = programmes.by_course(db)
    for line, cells in enumerate(table[1:], start=2):
        values, error = clean_row(cells, cols, course_programmes)
        if not error and values["course"] not in courses_of(current_user):
            error = f"you can only add {' / '.join(COURSE_NAMES[c] for c in courses_of(current_user))} students"
        if error:
            skipped.append({"line": line, "error": error})
            continue
        number, school = values["student_number"], values["school_email"]
        if number in used_ids:
            duplicates.append({"line": line, "error": f"student ID {number} is already used by {used_ids[number]}"})
            continue
        if school in used_emails:
            duplicates.append({"line": line, "error": f"school email {school} is already used by {used_emails[school]}"})
            continue
        used_ids[number] = used_emails[school] = f"row {line} of this file"
        rows.append({**values, "line": line})
    if duplicates:
        raise HTTPException(status_code=400, detail={
            "message": "This file was not saved: some student IDs or school emails are used twice. "
                       "Correct them and upload the file again.",
            "duplicates": duplicates, "skipped": skipped})
    if not rows:
        raise HTTPException(status_code=400, detail={"message": "No valid student rows.", "skipped": skipped})

    name = re.split(r"[\\/]", file.filename or "students")[-1][:255]
    batch_id = db.execute(
        text("INSERT INTO student_intake_batches (uploaded_by, file_name) VALUES (:u, :n) RETURNING batch_id"),
        {"u": str(current_user.user_id), "n": name}
    ).scalar()
    db.execute(
        text("""
            INSERT INTO student_intake_rows (batch_id, line_number, full_name, student_number, school_email,
                                             phone, course, programme)
            VALUES (:b, :line, :full_name, :student_number, :school_email, :phone, :course, :programme)
        """),
        [{"b": str(batch_id), **r} for r in rows]
    )
    audit.record(db, "intake.upload", user=current_user, request=request,
                 target_type="intake_batch", target_id=batch_id,
                 details={"file": name, "students": len(rows), "skipped": len(skipped)})
    db.commit()
    return {"batch_id": str(batch_id), "students": len(rows), "skipped": skipped}


@router.get("/batches")
def list_batches(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Uploaded lists, newest first, with how many students are pending / created / rejected"""
    require_staff(current_user)
    rows = db.execute(text("""
        SELECT b.batch_id, b.file_name, b.uploaded_at, u.full_name AS uploaded_by_name,
               COUNT(r.row_id)                                    AS total,
               COUNT(r.row_id) FILTER (WHERE r.status = 'pending')  AS pending,
               COUNT(r.row_id) FILTER (WHERE r.status = 'created')  AS created,
               COUNT(r.row_id) FILTER (WHERE r.status = 'rejected') AS rejected
        FROM student_intake_batches b
        LEFT JOIN users u ON u.user_id = b.uploaded_by
        LEFT JOIN student_intake_rows r ON r.batch_id = b.batch_id
        WHERE (:admin OR b.uploaded_by = CAST(:uid AS uuid))
        GROUP BY b.batch_id, u.full_name
        ORDER BY b.uploaded_at DESC
    """), {"admin": current_user.role == "admin", "uid": str(current_user.user_id)}).fetchall()
    return [dict(r._mapping) for r in rows]


@router.get("/batches/{batch_id}")
def get_batch_rows(batch_id: str, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    require_staff(current_user)
    batch = get_batch(db, batch_id, current_user)
    rows = db.execute(text(f"""
        SELECT {ROW_COLUMNS} FROM student_intake_rows r
        WHERE r.batch_id = :b ORDER BY r.line_number
    """), {"b": str(batch.batch_id)}).fetchall()
    return {"batch": dict(batch._mapping), "rows": [dict(r._mapping) for r in rows]}


# ── Advisor: check the list and create accounts ───────────────
def check_assignment(db, row_id, student_number, school_email):
    """Raise 400 if the number or email is malformed or already used"""
    if not STUDENT_NUMBER_RE.match(student_number or ""):
        raise HTTPException(status_code=400, detail="A student ID must be exactly 9 digits, e.g. 105967029.")
    if not (school_email or "").lower().endswith("@" + STUDENT_DOMAIN) or not EMAIL_RE.match(school_email):
        raise HTTPException(status_code=400, detail=f"The school email must end with @{STUDENT_DOMAIN}.")
    if db.execute(text("SELECT 1 FROM users WHERE student_number = :n"), {"n": student_number}).fetchone():
        raise HTTPException(status_code=400, detail=f"Student ID {student_number} already belongs to an account.")
    if db.execute(text("SELECT 1 FROM users WHERE lower(email) = lower(:e)"), {"e": school_email}).fetchone():
        raise HTTPException(status_code=400, detail=f"{school_email} already belongs to an account.")
    clash = db.execute(text("""
        SELECT 1 FROM student_intake_rows
        WHERE status = 'pending' AND row_id <> CAST(:r AS uuid)
          AND (student_number = :n OR lower(school_email) = lower(:e))
    """), {"r": str(row_id), "n": student_number, "e": school_email}).fetchone()
    if clash:
        raise HTTPException(status_code=400, detail="Another new student on a list already has this student ID or email.")


def own_row_id(db, row_id, user):
    """The id of a student on a list this advisor uploaded, else 404"""
    rid = parse_id(row_id, "Student not found")
    owner = db.execute(text("""
        SELECT b.uploaded_by FROM student_intake_rows r
        JOIN student_intake_batches b ON b.batch_id = r.batch_id
        WHERE r.row_id = :r
    """), {"r": rid}).fetchone()
    if not owner or str(owner.uploaded_by) != str(user.user_id):
        raise HTTPException(status_code=404, detail="Student not found")
    return rid


class RowUpdate(BaseModel):
    # Student ID and school email are changed together; course and programme on their own
    student_number: Optional[str] = Field(None, min_length=9, max_length=9)
    school_email: Optional[str] = Field(None, min_length=3, max_length=255)
    course: Optional[Literal["CS", "BUSINESS", "ICT"]] = None
    programme: Optional[str] = Field(None, max_length=150)


@router.patch("/rows/{row_id}")
def update_row(row_id: str, req: RowUpdate, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Correct the student ID / school email, the course or the programme of a pending student"""
    require_advisor(current_user)
    rid = own_row_id(db, row_id, current_user)
    row = db.execute(text("SELECT status, course, programme FROM student_intake_rows WHERE row_id = :r"),
                     {"r": rid}).fetchone()
    if row.status != "pending":
        raise HTTPException(status_code=400, detail="Only students still waiting for an account can be changed.")
    if req.student_number is None and req.school_email is None and req.course is None and req.programme is None:
        raise HTTPException(status_code=400, detail="Nothing to update.")
    if (req.student_number is None) != (req.school_email is None):
        raise HTTPException(status_code=400, detail="Give both the student ID and the school email.")
    if req.student_number is not None:
        number, email = req.student_number.strip(), req.school_email.strip().lower()
        check_assignment(db, rid, number, email)
        db.execute(text("UPDATE student_intake_rows SET student_number = :n, school_email = :e WHERE row_id = :r"),
                   {"n": number, "e": email, "r": rid})
    if req.course is not None or req.programme is not None:
        course = req.course or row.course
        check_course(current_user, course)
        programme = row.programme
        if req.programme is not None:
            programme = programmes.check_programme(db, req.programme, course)
        elif programme and programme not in programmes.by_course(db).get(course, {}).values():
            programme = None        # the old programme belongs to the old course: choose again
        db.execute(text("UPDATE student_intake_rows SET course = :c, programme = :p WHERE row_id = :r"),
                   {"c": course, "p": programme, "r": rid})
    db.commit()
    return dict(db.execute(text(f"SELECT {ROW_COLUMNS} FROM student_intake_rows r WHERE r.row_id = :r"),
                           {"r": rid}).fetchone()._mapping)


def temporary_password(length=12):
    """Random and readable (no 0/O, 1/l/I); meets the password rules in routers/auth.py"""
    upper = "ABCDEFGHJKLMNPQRSTUVWXYZ"
    lower = "abcdefghijkmnopqrstuvwxyz"
    digits = "23456789"
    symbols = "!@#$%&*?"
    pool = upper + lower + digits + symbols
    while True:
        pw = "".join(secrets.choice(pool) for _ in range(length))
        if password_error(pw) is None:
            return pw


class CreateAccounts(BaseModel):
    row_ids: Optional[List[UUID]] = None   # None = every pending student in the list


@router.post("/batches/{batch_id}/create-accounts")
def create_accounts(
    batch_id: str,
    req: CreateAccounts,
    request: Request,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create student accounts and email each student their login details (to the school email).

    A student whose ID or email is missing or already taken is skipped and reported;
    the others still go ahead.
    """
    require_advisor(current_user)
    batch = get_batch(db, batch_id, current_user)
    params = {"b": str(batch.batch_id)}
    only = ""
    if req.row_ids is not None:
        only = "AND row_id = ANY(CAST(:ids AS uuid[]))"
        params["ids"] = [str(i) for i in req.row_ids]
    rows = db.execute(text(f"""
        SELECT row_id, full_name, student_number, school_email, course, programme
        FROM student_intake_rows
        WHERE batch_id = :b AND status = 'pending' {only}
        ORDER BY line_number
    """), params).fetchall()

    created, failed = [], []
    for r in rows:
        if not r.course:   # lists uploaded before the Course column existed
            failed.append({"row_id": str(r.row_id), "full_name": r.full_name,
                           "error": "no course: choose Computer Science, Business or Information and Communications Technology first"})
            continue
        if not r.programme:   # lists uploaded before the Programme column existed
            failed.append({"row_id": str(r.row_id), "full_name": r.full_name,
                           "error": "no programme: choose the student's programme first"})
            continue
        number, email = r.student_number, r.school_email
        if not number or not email:   # lists uploaded before the Student ID column existed
            failed.append({"row_id": str(r.row_id), "full_name": r.full_name,
                           "error": "no student ID or school email: enter them first"})
            continue
        try:
            check_assignment(db, r.row_id, number, email)
        except HTTPException as e:
            failed.append({"row_id": str(r.row_id), "full_name": r.full_name, "error": e.detail})
            continue
        password = temporary_password()
        user_id = db.execute(text("""
            INSERT INTO users (email, password_hash, role, full_name, student_number, course, must_change_password)
            VALUES (:e, :pw, 'student', :name, :n, :course, TRUE)
            RETURNING user_id
        """), {"e": email, "pw": hash_password(password), "name": r.full_name, "n": number,
               "course": r.course}).scalar()
        programmes.set_programme(db, user_id, r.programme)
        db.execute(text("""
            UPDATE student_intake_rows
            SET status = 'created', user_id = :u, student_number = :n, school_email = :e,
                processed_by = :by, processed_at = CURRENT_TIMESTAMP
            WHERE row_id = :r
        """), {"u": str(user_id), "n": number, "e": email,
               "by": str(current_user.user_id), "r": str(r.row_id)})
        subject, body = notifications.welcome_email(r.full_name, number, email, password, COURSE_NAMES[r.course],
                                                    r.programme)
        mail = notifications.send_email(db, email, subject, body, related_user_id=user_id)
        created.append({"row_id": str(r.row_id), "full_name": r.full_name, "student_number": number,
                        "school_email": email, "email_status": mail})

    if created:
        audit.record(db, "intake.accounts_create", user=current_user, request=request,
                     target_type="intake_batch", target_id=batch.batch_id,
                     details={"created": len(created), "failed": len(failed)})
    db.commit()
    return {"created": created, "failed": failed, "mail_server": notifications.smtp_configured()}


class RowReject(BaseModel):
    note: str = Field("", max_length=500)


@router.post("/rows/{row_id}/reject")
def reject_row(row_id: str, req: RowReject, request: Request,
               current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Do not create an account for this student (duplicate, wrong person ...)"""
    require_advisor(current_user)
    rid = own_row_id(db, row_id, current_user)
    done = db.execute(text("""
        UPDATE student_intake_rows
        SET status = 'rejected', note = :note, processed_by = :by, processed_at = CURRENT_TIMESTAMP
        WHERE row_id = :r AND status = 'pending'
        RETURNING batch_id
    """), {"note": req.note.strip() or None, "by": str(current_user.user_id), "r": rid}).fetchone()
    if not done:
        raise HTTPException(status_code=404, detail="No pending student found.")
    audit.record(db, "intake.reject", user=current_user, request=request,
                 target_type="intake_row", target_id=rid, details={"note": req.note.strip()})
    db.commit()
    return {"message": "Rejected"}


# ── Emails ────────────────────────────────────────────────────
def can_resend(user, related_role, related_course):
    """Advisors: the emails of students of their courses. Admins do not touch those, only
    the account emails of the staff they create themselves (User Management)."""
    if user.role == "admin":
        return related_role != "student"
    return user.role == "advisor" and related_role == "student" and related_course in courses_of(user)


@router.get("/outbox")
def list_outbox(limit: int = 50, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Notification emails, newest first. Without a mail server they are only stored here.
    Admins see every email; advisors those of students of their courses."""
    require_staff(current_user)
    rows = db.execute(text("""
        SELECT o.email_id, o.to_address, o.subject, o.body, o.status, o.error, o.created_at,
               o.attempts, o.last_attempt_at, o.sent_at, o.related_user_id,
               u.full_name AS related_user_name, u.role AS related_role, u.course AS related_course,
               COALESCE(u.must_change_password, FALSE) AS password_still_temporary
        FROM email_outbox o LEFT JOIN users u ON u.user_id = o.related_user_id
        WHERE :admin OR (u.role = 'student' AND u.course = ANY(CAST(:courses AS VARCHAR[])))
        ORDER BY o.created_at DESC LIMIT :n
    """), {"n": max(1, min(limit, 200)), "admin": current_user.role == "admin",
           "courses": courses_of(current_user)}).fetchall()
    emails = [{**r._mapping, "can_resend": can_resend(current_user, r.related_role, r.related_course)} for r in rows]
    return {"mail_server": notifications.smtp_configured(), "emails": emails}


@router.post("/outbox/{email_id}/resend")
def resend_email(email_id: str, request: Request, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Send a stored email again. An account email with a temporary password is only
    resent while that password is still the one in use."""
    require_staff(current_user)
    eid = parse_id(email_id, "Email not found")
    row = db.execute(text("""
        SELECT o.email_id, o.body, o.related_user_id, u.must_change_password, u.role AS related_role, u.course AS related_course
        FROM email_outbox o LEFT JOIN users u ON u.user_id = o.related_user_id WHERE o.email_id = :e
    """), {"e": eid}).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Email not found")
    if not can_resend(current_user, row.related_role, row.related_course):
        raise HTTPException(status_code=403, detail="Student emails are sent by the student's advisor.")
    if not notifications.smtp_configured():
        raise HTTPException(status_code=400, detail="No mail server is set up (SMTP settings in backend/.env), so nothing can be sent yet.")
    if "Temporary password" in row.body and row.related_user_id and not row.must_change_password:
        raise HTTPException(status_code=400, detail=(
            "This person has already chosen their own password, so this temporary password no longer works. "
            "Ask an admin to reset their password in User Management."))
    status, error = notifications.resend(db, row.email_id)
    audit.record(db, "intake.email_resend", user=current_user, request=request, target_type="email",
                 target_id=row.email_id, details={"status": status})
    db.commit()
    return {"status": status, "error": error}
