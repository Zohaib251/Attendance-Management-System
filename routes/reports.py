from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from database import get_db
import models
from security import get_user_school, require_admin
from templates_config import render_template

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/", name="reports")
def reports(
    request: Request,
    subject: Optional[str] = "",
    date_from: Optional[str] = "",
    date_to: Optional[str] = "",
    current_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    school = get_user_school(current_user, db)
    school_id = school.id if school else None

    subjects = db.query(models.Subject).filter(
        models.Subject.school_id == school_id,
        models.Subject.is_active == True
    ).all()

    report_data = []
    selected_subject = None

    if subject and subject.isdigit():
        subject_id = int(subject)
        selected_subject = db.query(models.Subject).filter(
            models.Subject.subject_code == subject_id,
            models.Subject.school_id == school_id
        ).first()

        if selected_subject:
            query = db.query(models.Attendance).filter(
                models.Attendance.school_id == school_id,
                models.Attendance.subject_id == subject_id
            )

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

            attendances = query.all()
            student_map = {}
            for a in attendances:
                sid = a.student_id
                if sid not in student_map:
                    student_map[sid] = {
                        "student__student_id": sid,
                        "student__first_name": a.student.first_name if a.student else "",
                        "student__last_name": a.student.last_name if a.student else "",
                        "total": 0,
                        "present": 0,
                        "absent": 0,
                        "late": 0
                    }
                student_map[sid]["total"] += 1
                if a.status == "Present":
                    student_map[sid]["present"] += 1
                elif a.status == "Absent":
                    student_map[sid]["absent"] += 1
                elif a.status == "Late":
                    student_map[sid]["late"] += 1

            for sid, data in student_map.items():
                t = data["total"]
                data["pct"] = round((data["present"] / t) * 100, 1) if t else 0.0
                report_data.append(data)

            report_data.sort(key=lambda x: x["student__first_name"])

    context = {
        "subjects": subjects,
        "selected_subject": selected_subject,
        "report_data": report_data,
        "date_from": date_from or "",
        "date_to": date_to or "",
    }
    return render_template("reports/index.html", request, context, current_user, school)
