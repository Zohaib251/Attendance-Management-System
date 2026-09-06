import uuid
from datetime import datetime, date
from sqlalchemy import (
    Column, String, Integer, SmallInteger, Boolean, Text, Date, DateTime, ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import relationship
from database import Base


def generate_uuid():
    return str(uuid.uuid4())


class School(Base):
    __tablename__ = "schools"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), unique=True, index=True, nullable=False)
    code = Column(String(50), unique=True, index=True, nullable=False)
    address = Column(Text, nullable=True)
    contact_email = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    users = relationship("UserProfile", back_populates="school")
    departments = relationship("Department", back_populates="school", cascade="all, delete-orphan")
    subjects = relationship("Subject", back_populates="school", cascade="all, delete-orphan")
    students = relationship("Student", back_populates="school", cascade="all, delete-orphan")
    attendances = relationship("Attendance", back_populates="school", cascade="all, delete-orphan")
    enrollments = relationship("StudentSubject", back_populates="school", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<School {self.name}>"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(150), unique=True, index=True, nullable=False)
    email = Column(String(254), nullable=True)
    first_name = Column(String(150), nullable=True, default="")
    last_name = Column(String(150), nullable=True, default="")
    hashed_password = Column(String(255), nullable=False)
    is_admin = Column(Boolean, default=True)
    is_student = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    student_profile = relationship("Student", back_populates="user", uselist=False)

    def __repr__(self):
        return f"<User {self.username}>"


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="profile")
    school = relationship("School", back_populates="users")


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=True)
    name = Column(String(100), nullable=False)
    code = Column(String(20), nullable=False)
    description = Column(Text, nullable=True, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    school = relationship("School", back_populates="departments")
    subjects = relationship("Subject", back_populates="department")
    students = relationship("Student", back_populates="department")

    def __repr__(self):
        return f"<Department {self.name}>"


class Subject(Base):
    __tablename__ = "subjects"

    subject_code = Column(Integer, primary_key=True, index=True, autoincrement=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=True)
    title = Column(String(200), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    credits = Column(SmallInteger, default=3)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    school = relationship("School", back_populates="subjects")
    department = relationship("Department", back_populates="subjects")
    attendances = relationship("Attendance", back_populates="subject")
    enrollments = relationship("StudentSubject", back_populates="subject")

    @property
    def subjectCode(self):
        return self.subject_code

    def __repr__(self):
        return f"<Subject {self.title}>"


class Student(Base):
    __tablename__ = "students"

    student_id = Column(String(200), primary_key=True, default=generate_uuid)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), unique=True, nullable=True)
    first_name = Column(String(200), nullable=False)
    last_name = Column(String(200), nullable=False)
    address = Column(Text, nullable=True, default="")
    email = Column(String(254), nullable=False)
    mobile_no = Column(String(15), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    roll_number = Column(String(50), nullable=True, default="")
    profile_photo = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    school = relationship("School", back_populates="students")
    user = relationship("User", back_populates="student_profile")
    department = relationship("Department", back_populates="students")
    attendances = relationship("Attendance", back_populates="student", cascade="all, delete-orphan")
    enrollments = relationship("StudentSubject", back_populates="student", cascade="all, delete-orphan")

    @property
    def studentId(self):
        return self.student_id

    @property
    def firstName(self):
        return self.first_name

    @property
    def lastName(self):
        return self.last_name

    @property
    def mobileNo(self):
        return self.mobile_no

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def attendance_percentage(self):
        total = len(self.attendances)
        if not total:
            return 0.0
        present = sum(1 for a in self.attendances if a.status == "Present")
        return round((present / total) * 100, 1)

    def __repr__(self):
        return f"<Student {self.full_name}>"


class StudentSubject(Base):
    __tablename__ = "student_subjects"

    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=True)
    student_id = Column(String(200), ForeignKey("students.student_id", ondelete="CASCADE"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.subject_code", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (UniqueConstraint("student_id", "subject_id", name="uix_student_subject"),)

    school = relationship("School", back_populates="enrollments")
    student = relationship("Student", back_populates="enrollments")
    subject = relationship("Subject", back_populates="enrollments")


class Attendance(Base):
    __tablename__ = "attendances"

    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=True)
    student_id = Column(String(200), ForeignKey("students.student_id", ondelete="CASCADE"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.subject_code", ondelete="SET NULL"), nullable=True)
    lecture_date = Column(Date, nullable=False)
    status = Column(String(20), default="Present")
    remarks = Column(Text, nullable=True, default="")
    marked_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (UniqueConstraint("student_id", "subject_id", "lecture_date", name="uix_attendance_record"),)

    school = relationship("School", back_populates="attendances")
    student = relationship("Student", back_populates="attendances")
    subject = relationship("Subject", back_populates="attendances")
    marked_by = relationship("User")

    @property
    def studentId(self):
        return self.student_id

    @property
    def subjectCode(self):
        return str(self.subject_id) if self.subject_id else ""

    @property
    def lectureDate(self):
        return str(self.lecture_date)

    def __repr__(self):
        return f"<Attendance {self.student_id} {self.lecture_date} {self.status}>"
