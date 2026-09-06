import json
from datetime import datetime, date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
import models
from security import get_current_user, get_user_school, require_admin, require_student
from templates_config import render_template

router = APIRouter(tags=["Dashboard"])


@router.get("/", name="home")
@router.get("/home")
def home(request: Request, current_user: Optional[models.User] = Depends(get_current_user)):
    if current_user.is_student:
        return RedirectResponse(url="/dashboard/student/", status_code=status.HTTP_302_FOUND)
    return RedirectResponse(url="/dashboard/admin/", status_code=status.HTTP_302_FOUND)


@router.get("/dashboard/", name="dashboard")
def dashboard(request: Request, current_user: models.User = Depends(get_current_user)):
    if current_user.is_student:
        return RedirectResponse(url="/dashboard/student/", status_code=status.HTTP_302_FOUND)
    return RedirectResponse(url="/dashboard/admin/", status_code=status.HTTP_302_FOUND)


@router.get("/dashboard/admin/", name="admin_dashboard")
def admin_dashboard(
    request: Request,
    current_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    school = get_user_school(current_user, db)
    school_id = school.id if school else None
    today = date.today()

    total_students = db.query(models.Student).filter(
        models.Student.school_id == school_id,
        models.Student.is_active == True
    ).count()

    total_subjects = db.query(models.Subject).filter(
        models.Subject.school_id == school_id,
        models.Subject.is_active == True
    ).count()

    total_departments = db.query(models.Department).filter(
        models.Department.school_id == school_id
    ).count()

    today_qs = db.query(models.Attendance).filter(
        models.Attendance.school_id == school_id,
        models.Attendance.lecture_date == today
    )
    today_present = today_qs.filter(models.Attendance.status == "Present").count()
    today_absent = today_qs.filter(models.Attendance.status == "Absent").count()
    today_late = today_qs.filter(models.Attendance.status == "Late").count()

    # Weekly trend
    weekly = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        p = db.query(models.Attendance).filter(
            models.Attendance.school_id == school_id,
            models.Attendance.lecture_date == d,
            models.Attendance.status == "Present"
        ).count()
        a = db.query(models.Attendance).filter(
            models.Attendance.school_id == school_id,
            models.Attendance.lecture_date == d,
            models.Attendance.status == "Absent"
        ).count()
        l = db.query(models.Attendance).filter(
            models.Attendance.school_id == school_id,
            models.Attendance.lecture_date == d,
            models.Attendance.status == "Late"
        ).count()
        weekly.append({"label": d.strftime("%a %d"), "present": p, "absent": a, "late": l})

    chart_labels = json.dumps([w["label"] for w in weekly])
    chart_present = json.dumps([w["present"] for w in weekly])
    chart_absent = json.dumps([w["absent"] for w in weekly])
    chart_late = json.dumps([w["late"] for w in weekly])

    # Status distribution
    status_counts_raw = db.query(
        models.Attendance.status,
        func.count(models.Attendance.id)
    ).filter(models.Attendance.school_id == school_id).group_by(models.Attendance.status).all()

    status_labels = json.dumps([s[0] for s in status_counts_raw])
    status_counts = json.dumps([s[1] for s in status_counts_raw])

    # Subjects stats
    subjects = db.query(models.Subject).filter(
        models.Subject.school_id == school_id,
        models.Subject.is_active == True
    ).all()
    subjects_stats = []
    for subj in subjects:
        total_att = len(subj.attendances)
        if total_att > 0:
            present_att = sum(1 for att in subj.attendances if att.status == "Present")
            subjects_stats.append({
                "title": subj.title,
                "total": total_att,
                "present": present_att,
                "pct": round((present_att / total_att) * 100, 1)
            })
    subjects_stats.sort(key=lambda x: x["present"], reverse=True)
    subjects_stats = subjects_stats[:8]

    # Recent attendance
    recent_attendance = db.query(models.Attendance).filter(
        models.Attendance.school_id == school_id
    ).order_by(models.Attendance.lecture_date.desc(), models.Attendance.created_at.desc()).limit(15).all()

    context = {
        "total_students": total_students,
        "total_subjects": total_subjects,
        "total_departments": total_departments,
        "today_present": today_present,
        "today_absent": today_absent,
        "today_late": today_late,
        "chart_labels": chart_labels,
        "chart_present": chart_present,
        "chart_absent": chart_absent,
        "chart_late": chart_late,
        "status_labels": status_labels,
        "status_counts": status_counts,
        "subjects_stats": subjects_stats,
        "recent_attendance": recent_attendance,
        "today": today,
    }
    return render_template("dashboard/admin.html", request, context, current_user, school)


@router.get("/dashboard/student/", name="student_dashboard")
def student_dashboard(
    request: Request,
    current_user: models.User = Depends(require_student),
    db: Session = Depends(get_db)
):
    school = get_user_school(current_user, db)
    school_id = school.id if school else None

    student = db.query(models.Student).filter(
        models.Student.user_id == current_user.id
    ).first()

    if not student:
        return RedirectResponse(url="/accounts/login/", status_code=status.HTTP_302_FOUND)

    all_attendance = db.query(models.Attendance).filter(
        models.Attendance.student_id == student.student_id
    ).order_by(models.Attendance.lecture_date.desc()).all()

    total = len(all_attendance)
    present = sum(1 for a in all_attendance if a.status == "Present")
    absent = sum(1 for a in all_attendance if a.status == "Absent")
    late = sum(1 for a in all_attendance if a.status == "Late")
    pct = round((present / total) * 100, 1) if total else 0.0

    # Per-subject breakdown
    subject_map = {}
    for a in all_attendance:
        title = a.subject.title if a.subject else "Unassigned"
        if title not in subject_map:
            subject_map[title] = {"total": 0, "present": 0, "absent": 0}
        subject_map[title]["total"] += 1
        if a.status == "Present":
            subject_map[title]["present"] += 1
        elif a.status == "Absent":
            subject_map[title]["absent"] += 1

    subject_stats = []
    for title, data in subject_map.items():
        t = data["total"]
        pct_s = round((data["present"] / t) * 100, 1) if t else 0.0
        subject_stats.append({
            "subject__title": title,
            "total": t,
            "present": data["present"],
            "absent": data["absent"],
            "pct": pct_s
        })

    recent = all_attendance[:10]

    context = {
        "student": student,
        "total": total,
        "present": present,
        "absent": absent,
        "late": late,
        "pct": pct,
        "subject_stats": subject_stats,
        "recent": recent,
    }
    return render_template("dashboard/student.html", request, context, current_user, school)
