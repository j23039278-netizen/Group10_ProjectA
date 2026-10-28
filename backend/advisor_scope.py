"""
SEAGAS — Advisor positions and the students each advisor may see

Every advisor is a Dean or a Head of Programme (HOP), set by the admin:

    Dean, Computing   CS + ICT    staff ID 10xxx
    HOP, CS           CS          staff ID 11xxx
    HOP, ICT          ICT         staff ID 12xxx
    Dean, Business    BUSINESS    staff ID 20xxx
    HOP, Business     BUSINESS    staff ID 21xxx

An advisor only sees, and only adds (new-student lists), students of their
courses. Admins see every course. The same table is in database/schema.sql
(staff_number_prefix), which also checks it.
"""

from fastapi import HTTPException

ALL_COURSES = ("CS", "BUSINESS", "ICT")
# Course names shown to people (emails, Excel template, messages); the codes stay CS / BUSINESS / ICT
COURSE_NAMES = {"CS": "Computer Science", "BUSINESS": "Business", "ICT": "Information and Communications Technology"}
COMPUTING = f"{COURSE_NAMES['CS']} and {COURSE_NAMES['ICT']}"     # the Computing office's courses

# (position, courses) -> staff ID prefix. Courses are kept sorted.
STAFF_PREFIX = {
    ("dean", ("CS", "ICT")): "10",
    ("hop", ("CS",)):        "11",
    ("hop", ("ICT",)):       "12",
    ("dean", ("BUSINESS",)): "20",
    ("hop", ("BUSINESS",)):  "21",
}


def staff_prefix(position, courses):
    """The two-digit staff ID prefix, or 400 for a combination that does not exist"""
    key = (position, tuple(sorted(set(courses or []))))
    if key not in STAFF_PREFIX:
        raise HTTPException(status_code=400, detail=(
            f"An advisor is the Dean of Computing ({COMPUTING}), the Dean of Business, "
            "or the Head of Programme of one course."))
    return STAFF_PREFIX[key]


def position_label(position, courses):
    courses = sorted(courses or [])
    if position == "dean":
        return f"Dean, Computing ({COMPUTING})" if courses == ["CS", "ICT"] else "Dean, Business"
    if position == "hop" and courses:
        return f"Head of Programme, {COURSE_NAMES[courses[0]]}"
    return None


def courses_of(user):
    """The courses whose students this staff member may see"""
    if user.role == "admin":
        return list(ALL_COURSES)
    return list(user.advisor_courses or [])


def check_course(user, course):
    """403 unless the staff member may see students of this course"""
    if course not in courses_of(user):
        raise HTTPException(status_code=403, detail=(
            f"You can only manage students of {', '.join(COURSE_NAMES[c] for c in courses_of(user))}."))
