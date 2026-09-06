from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
import models
import schemas
from security import (
    create_access_token,
    get_current_user,
    get_user_school,
    verify_password,
)

router = APIRouter(tags=["REST API v1"])


@router.post("/api-token-auth/")
def api_token_auth(data: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == data.username).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to log in with provided credentials."
        )
    token = create_access_token(data={"sub": user.username})
    return {"token": token, "access_token": token, "token_type": "bearer"}


# ── Students API ──────────────────────────────────────────────────────────────
@router.get("/api/v1/students/", response_model=List[schemas.StudentResponse])
def api_list_students(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    school = get_user_school(current_user, db)
    school_id = school.id if school else None
    return db.query(models.Student).filter(models.Student.school_id == school_id).all()


@router.post("/api/v1/students/", response_model=schemas.StudentResponse, status_code=status.HTTP_201_CREATED)
def api_create_student(
    student_in: schemas.StudentCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    school = get_user_school(current_user, db)
    school_id = school.id if school else None

    student = models.Student(**student_in.model_dump(), school_id=school_id)
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


@router.get("/api/v1/students/{student_id}/", response_model=schemas.StudentResponse)
def api_get_student(
    student_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    school = get_user_school(current_user, db)
    school_id = school.id if school else None
    student = db.query(models.Student).filter(models.Student.student_id == student_id, models.Student.school_id == school_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@router.patch("/api/v1/students/{student_id}/", response_model=schemas.StudentResponse)
def api_update_student(
    student_id: str,
    student_in: schemas.StudentUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    school = get_user_school(current_user, db)
    school_id = school.id if school else None
    student = db.query(models.Student).filter(models.Student.student_id == student_id, models.Student.school_id == school_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    for key, val in student_in.model_dump(exclude_unset=True).items():
        setattr(student, key, val)

    db.commit()
    db.refresh(student)
    return student


@router.delete("/api/v1/students/{student_id}/", status_code=status.HTTP_204_NO_CONTENT)
def api_delete_student(
    student_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    school = get_user_school(current_user, db)
    school_id = school.id if school else None
    student = db.query(models.Student).filter(models.Student.student_id == student_id, models.Student.school_id == school_id).first()
    if student:
        db.delete(student)
        db.commit()
    return None


# ── Attendance API ─────────────────────────────────────────────────────────────
@router.get("/api/v1/attendance/", response_model=List[schemas.AttendanceResponse])
def api_list_attendance(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    school = get_user_school(current_user, db)
    school_id = school.id if school else None
    return db.query(models.Attendance).filter(models.Attendance.school_id == school_id).all()


@router.post("/api/v1/attendance/", response_model=schemas.AttendanceResponse, status_code=status.HTTP_201_CREATED)
def api_create_attendance(
    att_in: schemas.AttendanceCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    school = get_user_school(current_user, db)
    school_id = school.id if school else None
    att = models.Attendance(**att_in.model_dump(), school_id=school_id, marked_by_id=current_user.id)
    db.add(att)
    db.commit()
    db.refresh(att)
    return att


# ── Subjects API ───────────────────────────────────────────────────────────────
@router.get("/api/v1/subjects/", response_model=List[schemas.SubjectResponse])
def api_list_subjects(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    school = get_user_school(current_user, db)
    school_id = school.id if school else None
    return db.query(models.Subject).filter(models.Subject.school_id == school_id).all()


@router.post("/api/v1/subjects/", response_model=schemas.SubjectResponse, status_code=status.HTTP_201_CREATED)
def api_create_subject(
    subj_in: schemas.SubjectCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    school = get_user_school(current_user, db)
    school_id = school.id if school else None
    subj = models.Subject(**subj_in.model_dump(), school_id=school_id)
    db.add(subj)
    db.commit()
    db.refresh(subj)
    return subj


# ── Departments API ────────────────────────────────────────────────────────────
@router.get("/api/v1/departments/", response_model=List[schemas.DepartmentResponse])
def api_list_departments(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    school = get_user_school(current_user, db)
    school_id = school.id if school else None
    return db.query(models.Department).filter(models.Department.school_id == school_id).all()


@router.post("/api/v1/departments/", response_model=schemas.DepartmentResponse, status_code=status.HTTP_201_CREATED)
def api_create_department(
    dept_in: schemas.DepartmentCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    school = get_user_school(current_user, db)
    school_id = school.id if school else None
    dept = models.Department(**dept_in.model_dump(), school_id=school_id)
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return dept


# ── Enrollments API ────────────────────────────────────────────────────────────
@router.get("/api/v1/enrollments/", response_model=List[schemas.StudentSubjectResponse])
def api_list_enrollments(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    school = get_user_school(current_user, db)
    school_id = school.id if school else None
    return db.query(models.StudentSubject).filter(models.StudentSubject.school_id == school_id).all()


@router.post("/api/v1/enrollments/", response_model=schemas.StudentSubjectResponse, status_code=status.HTTP_201_CREATED)
def api_create_enrollment(
    enr_in: schemas.StudentSubjectCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    school = get_user_school(current_user, db)
    school_id = school.id if school else None
    enr = models.StudentSubject(**enr_in.model_dump(), school_id=school_id)
    db.add(enr)
    db.commit()
    db.refresh(enr)
    return enr
