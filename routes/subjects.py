from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from database import get_db
import models
from security import get_user_school, require_admin
from templates_config import render_template

router = APIRouter(prefix="/subjects", tags=["Subjects"])


@router.get("/", name="subject_list")
def subject_list(
    request: Request,
    current_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    school = get_user_school(current_user, db)
    school_id = school.id if school else None

    subjects = db.query(models.Subject).filter(models.Subject.school_id == school_id).order_by(models.Subject.title).all()
    
    # Attach student count property for Jinja2 template compatibility
    for s in subjects:
        s.student_count = len(s.enrollments)

    context = {"subjects": subjects}
    return render_template("subjects/list.html", request, context, current_user, school)


@router.get("/add/", name="subject_create")
def subject_create_page(
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
        "subject": None
    }
    return render_template("subjects/form.html", request, context, current_user, school)


@router.post("/add/")
def subject_create_submit(
    request: Request,
    title: str = Form(...),
    department_id: Optional[str] = Form(None),
    credits: int = Form(3),
    is_active: bool = Form(True),
    current_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    school = get_user_school(current_user, db)
    school_id = school.id if school else None

    dept_id_int = int(department_id) if department_id and department_id.isdigit() else None

    subject = models.Subject(
        school_id=school_id,
        title=title,
        department_id=dept_id_int,
        credits=credits,
        is_active=is_active
    )
    db.add(subject)
    db.commit()
    return RedirectResponse(url="/subjects/", status_code=status.HTTP_302_FOUND)


@router.get("/{subject_code}/edit/", name="subject_edit")
def subject_edit_page(
    request: Request,
    subject_code: int,
    current_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    school = get_user_school(current_user, db)
    school_id = school.id if school else None

    subject = db.query(models.Subject).filter(
        models.Subject.subject_code == subject_code,
        models.Subject.school_id == school_id
    ).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    departments = db.query(models.Department).filter(models.Department.school_id == school_id).all()

    context = {
        "action": "Edit",
        "subject": subject,
        "departments": departments
    }
    return render_template("subjects/form.html", request, context, current_user, school)


@router.post("/{subject_code}/edit/")
def subject_edit_submit(
    request: Request,
    subject_code: int,
    title: str = Form(...),
    department_id: Optional[str] = Form(None),
    credits: int = Form(3),
    is_active: bool = Form(True),
    current_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    school = get_user_school(current_user, db)
    school_id = school.id if school else None

    subject = db.query(models.Subject).filter(
        models.Subject.subject_code == subject_code,
        models.Subject.school_id == school_id
    ).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    dept_id_int = int(department_id) if department_id and department_id.isdigit() else None

    subject.title = title
    subject.department_id = dept_id_int
    subject.credits = credits
    subject.is_active = is_active

    db.commit()
    return RedirectResponse(url="/subjects/", status_code=status.HTTP_302_FOUND)
