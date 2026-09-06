from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import re

def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return re.sub(r'^-+|-+$', '', text)

from database import get_db
import models
from security import (
    create_access_token,
    get_current_user_optional,
    get_password_hash,
    get_user_school,
    verify_password,
)
from templates_config import render_template

router = APIRouter(tags=["Authentication"])


@router.get("/accounts/login/", name="login")
@router.get("/login/", name="login_alt")
def login_page(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user_optional(request, db)
    if current_user:
        return RedirectResponse(url="/dashboard/", status_code=status.HTTP_302_FOUND)
    return render_template("registration/login.html", request, {"form": {}})


@router.post("/accounts/login/")
@router.post("/login/")
def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    next: str = Form("/dashboard/"),
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        context = {
            "form": {"errors": True},
            "error_msg": "Invalid credentials. Please try again."
        }
        return render_template("registration/login.html", request, context)

    access_token = create_access_token(data={"sub": user.username})
    target_url = next if next and next.startswith("/") else "/dashboard/"
    response = RedirectResponse(url=target_url, status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    return response


@router.get("/signup/", name="signup")
def signup_page(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user_optional(request, db)
    if current_user:
        return RedirectResponse(url="/dashboard/", status_code=status.HTTP_302_FOUND)
    return render_template("registration/signup.html", request, {"form": {}})


@router.post("/signup/")
def signup_submit(
    request: Request,
    school_name: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    existing_user = db.query(models.User).filter(models.User.username == username).first()
    if existing_user:
        context = {
            "form": {"errors": True},
            "errors": [f"Username '{username}' is already taken."]
        }
        return render_template("registration/signup.html", request, context)

    code = slugify(school_name)
    if not code:
        code = f"school-{models.generate_uuid()[:8]}"

    school = db.query(models.School).filter(models.School.name == school_name).first()
    if not school:
        school = models.School(name=school_name, code=code)
        db.add(school)
        db.commit()
        db.refresh(school)

    hashed_pw = get_password_hash(password)
    new_user = models.User(
        username=username,
        hashed_password=hashed_pw,
        is_admin=True,
        is_student=False
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    user_profile = models.UserProfile(user_id=new_user.id, school_id=school.id)
    db.add(user_profile)
    db.commit()

    access_token = create_access_token(data={"sub": new_user.username})
    response = RedirectResponse(url="/dashboard/", status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    return response


@router.get("/logout/", name="logout")
@router.post("/logout/")
def logout(request: Request):
    response = RedirectResponse(url="/accounts/login/", status_code=status.HTTP_302_FOUND)
    response.delete_cookie(key="access_token")
    return response
