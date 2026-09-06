# Attendance Mangement System

A modern, B2B Multi-Tenant SaaS platform for managing student attendance, built with FastAPI and PostgreSQL, and deployed for free on Render.

## Key Features
* **B2B Multi-Tenancy:** Completely isolated database rows for different schools/organizations.
* **Role-Based Access:** Distinct privileges for Admins (full management) and Students (read-only analytics).
* **FastAPI Backend:** High-performance async API with strict Pydantic data validation.
* **Database:** PostgreSQL hosted securely on Supabase.
* **Deployment:** Automated CI/CD deployment on Render (Web Service).
* **Security:** JWT stateless authentication, bcrypt password hashing, and hidden environment credentials.

## Tech Stack
* **Framework:** FastAPI (Python 3)
* **ORM & Migrations:** SQLAlchemy 2.0 & Alembic
* **Database:** PostgreSQL (Supabase) / SQLite (Local fallback)
* **Frontend:** Jinja2 Templates, Bootstrap 5, Chart.js

## Local Setup Instructions
1. Clone the repository and open it in VS Code.
2. Create a virtual environment and run `pip install -r requirements.txt`.
3. Create a `.env` file and add your Supabase connection string as `DATABASE_URL=`. (If left empty, the system safely falls back to local SQLite).
4. Run database migrations: `alembic upgrade head`
5. Start the local server: `uvicorn main:app --reload`
6. Visit `http://127.0.0.1:8000` to sign up and view your isolated dashboard.
