import logging
from typing import Optional

from fastapi import APIRouter, Depends, Form, File, UploadFile, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_

from database import get_db
import models
from security import get_password_hash, get_user_school, require_admin
from templates_config import render_template

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/students", tags=["Students"])


@router.get("/", name="student_list")
def student_list(
    request: Request,
    q: Optional[str] = "",
    dept: Optional[str] = "",
    current_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    school = get_user_school(current_user, db)
    school_id = school.id if school else None

    query = db.query(models.Student).filter(
        models.Student.school_id == school_id,
        models.Student.is_active == True
    )
    if q:
        search_pattern = f"%{q}%"
        query = query.filter(
            or_(
                models.Student.first_name.ilike(search_pattern),
                models.Student.last_name.ilike(search_pattern),
                models.Student.email.ilike(search_pattern),
                models.Student.roll_number.ilike(search_pattern)
            )
        )
    if dept:
        try:
            dept_id = int(dept)
            query = query.filter(models.Student.department_id == dept_id)
        except ValueError:
            pass

    students = query.all()
    departments = db.query(models.Department).filter(models.Department.school_id == school_id).all()

    context = {
        "students": students,
        "departments": departments,
        "q": q or "",
        "dept": dept or ""
    }
    return render_template("students/list.html", request, context, current_user, school)


@router.get("/add/", name="student_create")
def student_create_page(
    request: Request,
    current_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    school = get_user_school(current_user, db)
    school_id = school.id if school else None
    departments = db.query(models.Department).filter(models.Department.school_id == school_id).all()

    context = {
        "action": "Add New",
        "departments": departments,
        "student": None
    }
    return render_template("students/form.html", request, context, current_user, school)


@router.post("/add/")
def student_create_submit(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    mobile_no: str = Form(""),
    address: str = Form(""),
    department_id: Optional[str] = Form(None),
    roll_number: str = Form(""),
    is_active: bool = Form(True),
    current_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    school = get_user_school(current_user, db)
    school_id = school.id if school else None

    dept_id_int = int(department_id) if department_id and department_id.isdigit() else None

    student = models.Student(
        school_id=school_id,
        first_name=first_name,
        last_name=last_name,
        email=email,
        mobile_no=mobile_no,
        address=address,
        department_id=dept_id_int,
        roll_number=roll_number,
        is_active=is_active
    )
    db.add(student)
    db.commit()
    db.refresh(student)

    # Auto-create User account for Student
    username = student.student_id[:30]
    password_plain = f"Student@{student.student_id[-4:]}"
    hashed_pw = get_password_hash(password_plain)

    user = models.User(
        username=username,
        email=email,
        first_name=first_name,
        last_name=last_name,
        hashed_password=hashed_pw,
        is_admin=False,
        is_student=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    student.user_id = user.id
    user_profile = models.UserProfile(user_id=user.id, school_id=school_id)
    db.add(user_profile)
    db.commit()

    logger.info("Console Email Output | To: %s | Username: %s | Password: %s", email, username, password_plain)
    print(f"\n--- [WELCOME EMAIL OUTPUT] ---\nTo: {email}\nUsername: {username}\nPassword: {password_plain}\n------------------------------\n")

    return RedirectResponse(url="/students/", status_code=status.HTTP_302_FOUND)


@router.get("/{student_id}/", name="student_detail")
def student_detail(
    request: Request,
    student_id: str,
    current_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    school = get_user_school(current_user, db)
    school_id = school.id if school else None

    student = db.query(models.Student).filter(
        models.Student.student_id == student_id,
        models.Student.school_id == school_id
    ).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    attendance_records = db.query(models.Attendance).filter(
        models.Attendance.student_id == student_id
    ).order_by(models.Attendance.lecture_date.desc()).all()

    enrollments = db.query(models.StudentSubject).filter(
        models.StudentSubject.student_id == student_id
    ).all()

    context = {
        "student": student,
        "attendance_records": attendance_records,
        "enrollments": enrollments,
        "attendance_pct": student.attendance_percentage(),
    }
    return render_template("students/detail.html", request, context, current_user, school)


@router.get("/{student_id}/edit/", name="student_edit")
def student_edit_page(
    request: Request,
    student_id: str,
    current_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    school = get_user_school(current_user, db)
    school_id = school.id if school else None

    student = db.query(models.Student).filter(
        models.Student.student_id == student_id,
        models.Student.school_id == school_id
    ).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    departments = db.query(models.Department).filter(models.Department.school_id == school_id).all()

    context = {
        "action": "Edit",
        "student": student,
        "departments": departments
    }
    return render_template("students/form.html", request, context, current_user, school)


@router.post("/{student_id}/edit/")
def student_edit_submit(
    request: Request,
    student_id: str,
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    mobile_no: str = Form(...),
    address: str = Form(""),
    department_id: Optional[str] = Form(None),
    roll_number: str = Form(""),
    is_active: bool = Form(True),
    current_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    school = get_user_school(current_user, db)
    school_id = school.id if school else None

    student = db.query(models.Student).filter(
        models.Student.student_id == student_id,
        models.Student.school_id == school_id
    ).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    dept_id_int = int(department_id) if department_id and department_id.isdigit() else None

    student.first_name = first_name
    student.last_name = last_name
    student.email = email
    student.mobile_no = mobile_no
    student.address = address
    student.department_id = dept_id_int
    student.roll_number = roll_number
    student.is_active = is_active

    db.commit()
    return RedirectResponse(url=f"/students/{student_id}/", status_code=status.HTTP_302_FOUND)


@router.get("/{student_id}/delete/", name="student_delete")
def student_delete_page(
    request: Request,
    student_id: str,
    current_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    school = get_user_school(current_user, db)
    school_id = school.id if school else None

    student = db.query(models.Student).filter(
        models.Student.student_id == student_id,
        models.Student.school_id == school_id
    ).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    context = {"student": student}
    return render_template("students/confirm_delete.html", request, context, current_user, school)


@router.post("/{student_id}/delete/")
def student_delete_submit(
    request: Request,
    student_id: str,
    current_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    school = get_user_school(current_user, db)
    school_id = school.id if school else None

    student = db.query(models.Student).filter(
        models.Student.student_id == student_id,
        models.Student.school_id == school_id
    ).first()
    if student:
        student.is_active = False
        db.commit()

    return RedirectResponse(url="/students/", status_code=status.HTTP_302_FOUND)


@router.post("/{student_id}/resend-email/", name="resend_welcome_email")
def resend_welcome_email(
    request: Request,
    student_id: str,
    current_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    school = get_user_school(current_user, db)
    school_id = school.id if school else None

    student = db.query(models.Student).filter(
        models.Student.student_id == student_id,
        models.Student.school_id == school_id
    ).first()
    if student:
        username = student.student_id[:30]
        password_plain = f"Student@{student.student_id[-4:]}"
        print(f"\n--- [RESENT WELCOME EMAIL] ---\nTo: {student.email}\nUsername: {username}\nPassword: {password_plain}\n------------------------------\n")

    return RedirectResponse(url=f"/students/{student_id}/", status_code=status.HTTP_302_FOUND)
