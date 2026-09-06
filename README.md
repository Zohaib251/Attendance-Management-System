# Attendance Management System

A multi-tenant B2B student attendance management system built with **FastAPI** (Python 3.12), **SQLAlchemy**, **Pydantic v2**, and **SQLite**.

---

## Table of Contents

1. [Features](#features)
2. [Architecture & Tech Stack](#architecture--tech-stack)
3. [Project Structure](#project-structure)
4. [Local Setup & Quick Start](#local-setup--quick-start)
5. [Multi-Tenant Data Isolation](#multi-tenant-data-isolation)
6. [Email Notifications (Console Output)](#email-notifications-console-output)
7. [REST API Reference](#rest-api-reference)

---

## Features

| Feature | Description |
|---------|-------------|
| **B2B Multi-Tenancy** | Full multi-school tenant isolation for Schools, Admins, Students, Departments, Subjects, and Attendance |
| **Self-Service Sign Up** | School registration and Admin user onboarding via `/signup/` |
| **Role-Based Access** | Admin & Student authentication with JWT cookies and Bearer tokens |
| **Bulk Attendance Marking** | Mark entire class attendance in one screen with Present / Absent / Late toggles |
| **Analytics Dashboard** | Attendance charts (Chart.js), weekly trends, and subject breakdown |
| **Console Email Output** | Automatic welcome credentials printed directly to server console for testing |
| **FastAPI REST API v1** | Interactive Swagger UI (`/docs`) and ReDoc (`/redoc`) |
| **Modern UI** | Responsive glassmorphism UI built with Jinja2 and Bootstrap 5 |

---

## Architecture & Tech Stack

This application is 100% local and offline, powered by **FastAPI** and **SQLAlchemy** with zero Django dependencies.

| Layer | Technology | Usage Details |
|-------|-----------|----------------|
| **Language** | Python 3.12 | Core execution environment |
| **Framework** | FastAPI | Async HTTP routing, request validation, and OpenAPI documentation |
| **ORM & DB** | SQLAlchemy 2, SQLite (`attendance.db`) | Relational ORM with file-based SQLite database |
| **Migrations** | Alembic | Database schema migrations |
| **Validation** | Pydantic v2 | Data schemas for API request and response validation |
| **Security** | passlib[bcrypt], python-jose | Bcrypt password hashing and JWT token management |
| **Templating** | Jinja2 | Server-side web page rendering |
| **Frontend** | Bootstrap 5.3, Chart.js 4, Font Awesome 6 | Responsive design and analytics visualization |

---

## Project Structure

```
Attendance_Management_System/
├── routes/                     # FastAPI APIRouters
│   ├── auth.py                 # Login, Sign-up, Logout
│   ├── dashboard.py            # Admin & Student dashboards
│   ├── students.py             # Student management & welcome emails
│   ├── attendance.py           # Bulk & individual attendance marking
│   ├── subjects.py             # Subject management
│   ├── departments.py          # Department management
│   ├── reports.py              # Export & analytics reports
│   └── api.py                  # JSON REST API endpoints
│
├── templates/                  # Jinja2 HTML templates
│   ├── base.html               # Shared layout & navigation
│   ├── registration/           # Login & Signup pages
│   ├── dashboard/              # Admin & Student dashboards
│   ├── students/               # Student views
│   ├── attendance/             # Attendance marking views
│   ├── subjects/               # Subject views
│   ├── departments/            # Department views
│   └── reports/                # Report views
│
├── database.py                 # SQLAlchemy engine & SessionLocal setup
├── models.py                   # SQLAlchemy models (School, User, Student, Attendance, etc.)
├── schemas.py                  # Pydantic v2 schemas
├── security.py                  # Password hashing, JWT token decode/encode, FastAPI dependencies
├── templates_config.py         # Jinja2 template renderer helper
├── main.py                     # Main FastAPI application entrypoint
├── requirements.txt            # Python dependencies
└── attendance.db               # Local SQLite database file
```

---

## Local Setup & Quick Start

### Prerequisites

- Python 3.12+
- `pip`

### 1 — Clone and Activate Virtual Environment

```bash
git clone https://github.com/Zohaib251/Attendance_Management_System.git
cd Attendance_Management_System

python -m venv venv
# Windows PowerShell:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate
```

### 2 — Install Dependencies

```bash
pip install -r requirements.txt
```

### 3 — Run Application

```bash
python main.py
# Or using Uvicorn directly:
uvicorn main:app --reload --port 8000
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

---

## Multi-Tenant Data Isolation

- Admin registration at `/signup/` creates a new **School** tenant and an **Admin** user.
- All querysets filter data strictly by `school_id` derived from the logged-in user's profile.
- Students are automatically bound to their school upon registration.

---

## Email Notifications (Console Output)

When a student is registered by an Admin, credentials are automatically logged to the terminal:

```text
--- [WELCOME EMAIL OUTPUT] ---
To: jane@apex.edu
Username: aa97624e-067e-490a-9a2b-f5f7e7
Password: Student@edf9
------------------------------
```

---

## REST API Reference

Access interactive API docs:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### Authentication

```bash
curl -X POST http://localhost:8000/api-token-auth/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin1", "password": "password123"}'
```

Returns a JWT token:
```json
{
  "access_token": "<jwt-token-string>",
  "token_type": "bearer"
}
```

### Endpoints

Include `Authorization: Bearer <jwt-token-string>` in headers:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET, POST | `/api/v1/students/` | List / Create students |
| GET, PATCH, DELETE | `/api/v1/students/{student_id}/` | Retrieve / Update / Delete student |
| GET, POST | `/api/v1/attendance/` | List / Create attendance records |
| GET, POST | `/api/v1/subjects/` | List / Create subjects |
| GET, POST | `/api/v1/departments/` | List / Create departments |
