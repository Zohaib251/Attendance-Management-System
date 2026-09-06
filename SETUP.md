# Attendance Management System — Setup & Deployment Guide

## Requirements
- Python 3.12+
- pip

---

## Quick Start (Local Development)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run application
python main.py
# Or with uvicorn:
uvicorn main:app --reload --port 8000
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

---

## Deployment to Render (Free PostgreSQL with Supabase)

### 1. Database Setup (Supabase)
1. Create a free PostgreSQL database on [Supabase](https://supabase.com/).
2. Copy your Connection String (`DATABASE_URL`) from project settings.

### 2. Environment Configuration on Render
1. Push your repository to GitHub (ensure `.env` and `attendance.db` are ignored).
2. Create a new **Web Service** on [Render](https://render.com/).
3. Set **Build Command**: `./build.sh`
4. Set **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add Environment Variable:
   - `DATABASE_URL`: `postgresql://user:password@host:port/db` (from Supabase)
   - `SECRET_KEY`: `<your-random-secret-key>`
