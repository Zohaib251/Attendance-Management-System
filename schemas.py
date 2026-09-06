from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ── Token & Auth Schemas ──────────────────────────────────────────────────────
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[int] = None


class LoginRequest(BaseModel):
    username: str
    password: str


class SignUpRequest(BaseModel):
    username: str
    password: str
    school_name: str


# ── School Schemas ─────────────────────────────────────────────────────────────
class SchoolBase(BaseModel):
    name: str
    code: str
    address: Optional[str] = None
    contact_email: Optional[str] = None


class SchoolCreate(SchoolBase):
    pass


class SchoolResponse(SchoolBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── User Schemas ───────────────────────────────────────────────────────────────
class UserBase(BaseModel):
    username: str
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_admin: bool = True
    is_student: bool = False
    is_active: bool = True


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Department Schemas ─────────────────────────────────────────────────────────
class DepartmentBase(BaseModel):
    name: str
    code: str
    description: Optional[str] = ""


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None


class DepartmentResponse(DepartmentBase):
    id: int
    school_id: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Subject Schemas ────────────────────────────────────────────────────────────
class SubjectBase(BaseModel):
    title: str
    department_id: Optional[int] = None
    credits: int = 3
    is_active: bool = True


class SubjectCreate(SubjectBase):
    pass


class SubjectUpdate(BaseModel):
    title: Optional[str] = None
    department_id: Optional[int] = None
    credits: Optional[int] = None
    is_active: Optional[bool] = None


class SubjectResponse(SubjectBase):
    subject_code: int
    school_id: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Student Schemas ────────────────────────────────────────────────────────────
class StudentBase(BaseModel):
    first_name: str
    last_name: str
    email: str
    mobile_no: str
    address: Optional[str] = ""
    department_id: Optional[int] = None
    roll_number: Optional[str] = ""
    profile_photo: Optional[str] = None
    is_active: bool = True


class StudentCreate(StudentBase):
    pass


class StudentUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    mobile_no: Optional[str] = None
    address: Optional[str] = None
    department_id: Optional[int] = None
    roll_number: Optional[str] = None
    profile_photo: Optional[str] = None
    is_active: Optional[bool] = None


class StudentResponse(StudentBase):
    student_id: str
    school_id: Optional[int] = None
    user_id: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── StudentSubject (Enrollment) Schemas ─────────────────────────────────────────
class StudentSubjectCreate(BaseModel):
    student_id: str
    subject_id: int


class StudentSubjectResponse(BaseModel):
    id: int
    school_id: Optional[int] = None
    student_id: str
    subject_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Attendance Schemas ─────────────────────────────────────────────────────────
class AttendanceBase(BaseModel):
    student_id: str
    subject_id: Optional[int] = None
    lecture_date: date
    status: str = "Present"
    remarks: Optional[str] = ""


class AttendanceCreate(AttendanceBase):
    pass


class AttendanceUpdate(BaseModel):
    status: Optional[str] = None
    remarks: Optional[str] = None


class AttendanceResponse(AttendanceBase):
    id: int
    school_id: Optional[int] = None
    marked_by_id: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
