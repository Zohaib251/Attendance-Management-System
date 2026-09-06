from datetime import date, datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from database import get_db
import models
from security import get_user_school, require_admin
from templates_config import render_template

router = APIRouter(prefix="/attendance", tags=["Attendance"])


@router.get("/", name="attendance_list")
def attendance_list(
    request: Request,
    subject: Optional[str] = "",
    date_from: Optional[str] = "",
    date_to: Optional[str] = "",
    status_val: Optional[str] = "",
    current_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    school = get_user_school(current_user, db)
    school_id = school.id if school else None

    query = db.query(models.Attendance).filter(models.Attendance.school_id == school_id)

    if subject and subject.isdigit():
        query = query.filter(models.Attendance.subject_id == int(subject))
    if date_from:
        try:
            d_from = datetime.strptime(date_from, "%Y-%m-%d").date()
            query = query.filter(models.Attendance.lecture_date >= d_from)
        except ValueError:
            pass
    if date_to:
        try:
            d_to = datetime.strptime(date_to, "%Y-%m-%d").date()
            query = query.filter(models.Attendance.lecture_date <= d_to)
        except ValueError:
            pass
    if status_val:
        query = query.filter(models.Attendance.status == status_val)

    records = query.order_by(models.Attendance.lecture_date.desc()).limit(200).all()
    subjects = db.query(models.Subject).filter(models.Subject.school_id == school_id, models.Subject.is_active == True).all()

    class FilterForm:
        def __init__(self, subj, d_from, d_to, stat):
            self.cleaned_data = {
                "subject": int(subj) if subj and subj.isdigit() else None,
                "date_from": d_from,
                "date_to": d_to,
                "status": stat
            }

    form = FilterForm(subject, date_from, date_to, status_val)

    context = {
        "records": records,
        "subjects": subjects,
        "form": form
    }
    return render_template("attendance/list.html", request, context, current_user, school)


@router.get("/mark/", name="mark_attendance")
def mark_attendance_page(
    request: Request,
    subject: Optional[str] = "",
    date_str: Optional[str] = "",
    current_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    school = get_user_school(current_user, db)
    school_id = school.id if school else None

    subjects = db.query(models.Subject).filter(
        models.Subject.school_id == school_id,
        models.Subject.is_active == True
    ).all()

    selected_subject_id = int(subject) if subject and subject.isdigit() else None
    selected_date = date_str or date.today().isoformat()
    selected_subject = None
    students = []
    existing_map = {}

    if selected_subject_id:
        selected_subject = db.query(models.Subject).filter(
            models.Subject.subject_code == selected_subject_id,
            models.Subject.school_id == school_id
        ).first()

        if selected_subject:
            enrolled_ids = [
                e.student_id for e in db.query(models.StudentSubject).filter(
                    models.StudentSubject.school_id == school_id,
                    models.StudentSubject.subject_id == selected_subject_id
                ).all()
            ]

            if enrolled_ids:
                students = db.query(models.Student).filter(
                    models.Student.school_id == school_id,
                    models.Student.student_id.in_(enrolled_ids),
                    models.Student.is_active == True
                ).order_by(models.Student.first_name).all()
            else:
                students = db.query(models.Student).filter(
                    models.Student.school_id == school_id,
                    models.Student.is_active == True
                ).order_by(models.Student.first_name).all()

            try:
                l_date = datetime.strptime(selected_date, "%Y-%m-%d").date()
                existing = db.query(models.Attendance).filter(
                    models.Attendance.school_id == school_id,
                    models.Attendance.subject_id == selected_subject_id,
                    models.Attendance.lecture_date == l_date
                ).all()
                existing_map = {a.student_id: a.status for a in existing}
            except ValueError:
                pass

    context = {
        "subjects": subjects,
        "selected_subject": selected_subject,
        "selected_date": selected_date,
        "students": students,
        "existing_map": existing_map,
    }
    return render_template("attendance/mark.html", request, context, current_user, school)


@router.post("/mark/")
async def mark_attendance_submit(
    request: Request,
    current_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    school = get_user_school(current_user, db)
    school_id = school.id if school else None

    form_data = await request.form()
    subject_id_str = form_data.get("subject")
    lecture_date_str = form_data.get("date")
    student_ids = form_data.getlist("student_ids")

    if not subject_id_str or not lecture_date_str:
        return RedirectResponse(url="/attendance/mark/", status_code=status.HTTP_302_FOUND)

    subject_id = int(subject_id_str)
    l_date = datetime.strptime(lecture_date_str, "%Y-%m-%d").date()

    for sid in student_ids:
        status_val = form_data.get(f"status_{sid}", "Absent")
        remarks_val = form_data.get(f"remarks_{sid}", "")

        att = db.query(models.Attendance).filter(
            models.Attendance.school_id == school_id,
            models.Attendance.student_id == sid,
            models.Attendance.subject_id == subject_id,
            models.Attendance.lecture_date == l_date
        ).first()

        if att:
            att.status = status_val
            att.remarks = remarks_val
            att.marked_by_id = current_user.id
        else:
            att = models.Attendance(
                school_id=school_id,
                student_id=sid,
                subject_id=subject_id,
                lecture_date=l_date,
                status=status_val,
                remarks=remarks_val,
                marked_by_id=current_user.id
            )
            db.add(att)

    db.commit()
    return RedirectResponse(url="/attendance/", status_code=status.HTTP_302_FOUND)


@router.get("/add/", name="attendance_create")
def attendance_create_page(
    request: Request,
    current_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    school = get_user_school(current_user, db)
    school_id = school.id if school else None

    students = db.query(models.Student).filter(models.Student.school_id == school_id, models.Student.is_active == True).all()
    subjects = db.query(models.Subject).filter(models.Subject.school_id == school_id, models.Subject.is_active == True).all()

    context = {
        "action": "Add",
        "students": students,
        "subjects": subjects,
        "record": None
    }
    return render_template("attendance/form.html", request, context, current_user, school)


@router.post("/add/")
def attendance_create_submit(
    request: Request,
    student_id: str = Form(...),
    subject_id: int = Form(...),
    lecture_date: str = Form(...),
    status_val: str = Form("Present", alias="status"),
    remarks: str = Form(""),
    current_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    school = get_user_school(current_user, db)
    school_id = school.id if school else None
    l_date = datetime.strptime(lecture_date, "%Y-%m-%d").date()

    record = models.Attendance(
        school_id=school_id,
        student_id=student_id,
        subject_id=subject_id,
        lecture_date=l_date,
        status=status_val,
        remarks=remarks,
        marked_by_id=current_user.id
    )
    db.add(record)
    db.commit()
    return RedirectResponse(url="/attendance/", status_code=status.HTTP_302_FOUND)


@router.get("/{pk}/edit/", name="attendance_edit")
def attendance_edit_page(
    request: Request,
    pk: int,
    current_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    school = get_user_school(current_user, db)
    school_id = school.id if school else None

    record = db.query(models.Attendance).filter(models.Attendance.id == pk, models.Attendance.school_id == school_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    students = db.query(models.Student).filter(models.Student.school_id == school_id).all()
    subjects = db.query(models.Subject).filter(models.Subject.school_id == school_id).all()

    context = {
        "action": "Edit",
        "record": record,
        "students": students,
        "subjects": subjects
    }
    return render_template("attendance/form.html", request, context, current_user, school)


@router.post("/{pk}/edit/")
def attendance_edit_submit(
    request: Request,
    pk: int,
    student_id: str = Form(...),
    subject_id: int = Form(...),
    lecture_date: str = Form(...),
    status_val: str = Form(..., alias="status"),
    remarks: str = Form(""),
    current_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    school = get_user_school(current_user, db)
    school_id = school.id if school else None

    record = db.query(models.Attendance).filter(models.Attendance.id == pk, models.Attendance.school_id == school_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    record.student_id = student_id
    record.subject_id = subject_id
    record.lecture_date = datetime.strptime(lecture_date, "%Y-%m-%d").date()
    record.status = status_val
    record.remarks = remarks

    db.commit()
    return RedirectResponse(url="/attendance/", status_code=status.HTTP_302_FOUND)


@router.get("/{pk}/delete/", name="attendance_delete")
def attendance_delete_page(
    request: Request,
    pk: int,
    current_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    school = get_user_school(current_user, db)
    school_id = school.id if school else None

    record = db.query(models.Attendance).filter(models.Attendance.id == pk, models.Attendance.school_id == school_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    context = {"record": record}
    return render_template("attendance/confirm_delete.html", request, context, current_user, school)


@router.post("/{pk}/delete/")
def attendance_delete_submit(
    request: Request,
    pk: int,
    current_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    school = get_user_school(current_user, db)
    school_id = school.id if school else None

    record = db.query(models.Attendance).filter(models.Attendance.id == pk, models.Attendance.school_id == school_id).first()
    if record:
        db.delete(record)
        db.commit()

    return RedirectResponse(url="/attendance/", status_code=status.HTTP_302_FOUND)
