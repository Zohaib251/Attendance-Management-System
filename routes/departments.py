from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from database import get_db
import models
from security import get_user_school, require_admin
from templates_config import render_template

router = APIRouter(prefix="/departments", tags=["Departments"])


@router.get("/", name="department_list")
def department_list(
    request: Request,
    current_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    school = get_user_school(current_user, db)
    school_id = school.id if school else None

    departments = db.query(models.Department).filter(
        models.Department.school_id == school_id
    ).order_by(models.Department.name).all()

    for d in departments:
        d.student_count = len(d.students)
        d.subject_count = len(d.subjects)

    context = {"departments": departments}
    return render_template("departments/list.html", request, context, current_user, school)


@router.get("/add/", name="department_create")
def department_create_page(
    request: Request,
    current_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    school = get_user_school(current_user, db)

    context = {
        "action": "Add New",
        "dept": None
    }
    return render_template("departments/form.html", request, context, current_user, school)


@router.post("/add/")
def department_create_submit(
    request: Request,
    name: str = Form(...),
    code: str = Form(...),
    description: str = Form(""),
    current_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    school = get_user_school(current_user, db)
    school_id = school.id if school else None

    dept = models.Department(
        school_id=school_id,
        name=name,
        code=code,
        description=description
    )
    db.add(dept)
    db.commit()
    return RedirectResponse(url="/departments/", status_code=status.HTTP_302_FOUND)


@router.get("/{pk}/edit/", name="department_edit")
def department_edit_page(
    request: Request,
    pk: int,
    current_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    school = get_user_school(current_user, db)
    school_id = school.id if school else None

    dept = db.query(models.Department).filter(
        models.Department.id == pk,
        models.Department.school_id == school_id
    ).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")

    context = {
        "action": "Edit",
        "dept": dept
    }
    return render_template("departments/form.html", request, context, current_user, school)


@router.post("/{pk}/edit/")
def department_edit_submit(
    request: Request,
    pk: int,
    name: str = Form(...),
    code: str = Form(...),
    description: str = Form(""),
    current_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    school = get_user_school(current_user, db)
    school_id = school.id if school else None

    dept = db.query(models.Department).filter(
        models.Department.id == pk,
        models.Department.school_id == school_id
    ).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")

    dept.name = name
    dept.code = code
    dept.description = description

    db.commit()
    return RedirectResponse(url="/departments/", status_code=status.HTTP_302_FOUND)
