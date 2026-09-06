from fastapi.templating import Jinja2Templates
from fastapi import Request
from typing import Optional
import models

templates = Jinja2Templates(directory="templates")


def render_template(
    template_name: str,
    request: Request,
    context: Optional[dict] = None,
    current_user: Optional[models.User] = None,
    school: Optional[models.School] = None
):
    if context is None:
        context = {}
    context["request"] = request
    context["user"] = current_user
    context["user_is_student"] = current_user.is_student if current_user else False
    context["current_school"] = school
    return templates.TemplateResponse(request=request, name=template_name, context=context)
