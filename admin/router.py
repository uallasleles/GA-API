import os
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pwdlib import PasswordHash
from sqlmodel import Session, select

from auth.Auth import authenticate_user
from auth.database import get_session
from auth.models.role import RoleDB
from auth.models.user import UserDB
from auth.scopes import AVAILABLE_SCOPES
from auth.session import SignedSession

COOKIE_NAME = "admin_session"
SESSION_MAX_AGE = 8 * 60 * 60  # 8 horas

session = SignedSession(secret=os.getenv("ADMIN_SESSION_SECRET"), max_age_seconds=SESSION_MAX_AGE)

router = APIRouter(prefix="/admin", include_in_schema=False)

templates = Jinja2Templates(directory="admin/templates")

password_hash = PasswordHash.recommended()


async def require_admin_session(request: Request):
    token = request.cookies.get(COOKIE_NAME)
    if not session.verify(token):
        raise HTTPException(status_code=status.HTTP_303_SEE_OTHER, headers={"Location": "/admin/login"})


@router.get("", include_in_schema=False)
async def admin_root():
    return RedirectResponse(url="/admin/users")


@router.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    return templates.TemplateResponse(request, "login.html", {"error": None})


@router.post("/login")
async def login_submit(
    request: Request,
    db_session: Annotated[Session, Depends(get_session)],
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
):
    user = authenticate_user(db_session, username, password)
    if not user or user.disabled or "admin" not in user.scopes:
        return templates.TemplateResponse(
            request,
            "login.html",
            {"error": "Usuário, senha inválidos ou sem permissão de administrador."},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    response = RedirectResponse(url="/admin/users", status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        COOKIE_NAME,
        session.issue(),
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=SESSION_MAX_AGE,
    )
    return response


@router.post("/logout")
async def logout():
    response = RedirectResponse(url="/admin/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie(COOKIE_NAME)
    return response


# ---- Usuários ----

@router.get("/users", dependencies=[Depends(require_admin_session)])
async def list_users(request: Request, db_session: Annotated[Session, Depends(get_session)]):
    users = db_session.exec(select(UserDB)).all()
    return templates.TemplateResponse(request, "users_list.html", {"users": users})


@router.get("/users/new", dependencies=[Depends(require_admin_session)])
async def new_user_form(request: Request, db_session: Annotated[Session, Depends(get_session)]):
    roles = db_session.exec(select(RoleDB)).all()
    return templates.TemplateResponse(
        request, "user_form.html", {"user": None, "roles": roles, "selected_role_ids": set(), "error": None}
    )


@router.post("/users/new", dependencies=[Depends(require_admin_session)])
async def create_user(
    request: Request,
    db_session: Annotated[Session, Depends(get_session)],
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
    full_name: Annotated[str, Form()] = "",
    email: Annotated[str, Form()] = "",
    role_ids: Annotated[List[int], Form()] = [],
    active: Annotated[bool, Form()] = False,
):
    existing = db_session.exec(select(UserDB).where(UserDB.username == username)).first()
    if existing:
        roles = db_session.exec(select(RoleDB)).all()
        return templates.TemplateResponse(
            request,
            "user_form.html",
            {
                "user": None,
                "roles": roles,
                "selected_role_ids": set(role_ids),
                "error": "Já existe um usuário com esse login.",
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    user = UserDB(
        username=username,
        full_name=full_name or None,
        email=email or None,
        hashed_password=password_hash.hash(password),
        disabled=not active,
    )
    if role_ids:
        user.roles = db_session.exec(select(RoleDB).where(RoleDB.id.in_(role_ids))).all()
    db_session.add(user)
    db_session.commit()
    return RedirectResponse(url="/admin/users", status_code=status.HTTP_302_FOUND)


@router.get("/users/{user_id}/edit", dependencies=[Depends(require_admin_session)])
async def edit_user_form(user_id: int, request: Request, db_session: Annotated[Session, Depends(get_session)]):
    user = db_session.get(UserDB, user_id)
    if not user:
        raise HTTPException(status_code=404)
    roles = db_session.exec(select(RoleDB)).all()
    return templates.TemplateResponse(
        request,
        "user_form.html",
        {"user": user, "roles": roles, "selected_role_ids": {r.id for r in user.roles}, "error": None},
    )


@router.post("/users/{user_id}/edit", dependencies=[Depends(require_admin_session)])
async def update_user(
    user_id: int,
    request: Request,
    db_session: Annotated[Session, Depends(get_session)],
    full_name: Annotated[str, Form()] = "",
    email: Annotated[str, Form()] = "",
    password: Annotated[str, Form()] = "",
    role_ids: Annotated[List[int], Form()] = [],
    active: Annotated[bool, Form()] = False,
):
    user = db_session.get(UserDB, user_id)
    if not user:
        raise HTTPException(status_code=404)

    user.full_name = full_name or None
    user.email = email or None
    user.disabled = not active
    if password:
        user.hashed_password = password_hash.hash(password)
    user.roles = db_session.exec(select(RoleDB).where(RoleDB.id.in_(role_ids))).all() if role_ids else []

    db_session.add(user)
    db_session.commit()
    return RedirectResponse(url="/admin/users", status_code=status.HTTP_302_FOUND)


@router.post("/users/{user_id}/toggle", dependencies=[Depends(require_admin_session)])
async def toggle_user(user_id: int, db_session: Annotated[Session, Depends(get_session)]):
    user = db_session.get(UserDB, user_id)
    if not user:
        raise HTTPException(status_code=404)
    user.disabled = not user.disabled
    db_session.add(user)
    db_session.commit()
    return RedirectResponse(url="/admin/users", status_code=status.HTTP_302_FOUND)


# ---- Papéis (roles) ----

@router.get("/roles", dependencies=[Depends(require_admin_session)])
async def list_roles(request: Request, db_session: Annotated[Session, Depends(get_session)]):
    roles = db_session.exec(select(RoleDB)).all()
    return templates.TemplateResponse(request, "roles_list.html", {"roles": roles})


@router.get("/roles/new", dependencies=[Depends(require_admin_session)])
async def new_role_form(request: Request):
    return templates.TemplateResponse(
        request,
        "role_form.html",
        {"role": None, "available_scopes": AVAILABLE_SCOPES, "selected_scopes": set(), "error": None},
    )


@router.post("/roles/new", dependencies=[Depends(require_admin_session)])
async def create_role(
    request: Request,
    db_session: Annotated[Session, Depends(get_session)],
    name: Annotated[str, Form()],
    description: Annotated[str, Form()] = "",
    scopes: Annotated[List[str], Form()] = [],
):
    existing = db_session.exec(select(RoleDB).where(RoleDB.name == name)).first()
    if existing:
        return templates.TemplateResponse(
            request,
            "role_form.html",
            {
                "role": None,
                "available_scopes": AVAILABLE_SCOPES,
                "selected_scopes": set(scopes),
                "error": "Já existe um papel com esse nome.",
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    role = RoleDB(name=name, description=description or None, scopes=scopes)
    db_session.add(role)
    db_session.commit()
    return RedirectResponse(url="/admin/roles", status_code=status.HTTP_302_FOUND)


@router.get("/roles/{role_id}/edit", dependencies=[Depends(require_admin_session)])
async def edit_role_form(role_id: int, request: Request, db_session: Annotated[Session, Depends(get_session)]):
    role = db_session.get(RoleDB, role_id)
    if not role:
        raise HTTPException(status_code=404)
    return templates.TemplateResponse(
        request,
        "role_form.html",
        {"role": role, "available_scopes": AVAILABLE_SCOPES, "selected_scopes": set(role.scopes), "error": None},
    )


@router.post("/roles/{role_id}/edit", dependencies=[Depends(require_admin_session)])
async def update_role(
    role_id: int,
    request: Request,
    db_session: Annotated[Session, Depends(get_session)],
    name: Annotated[str, Form()],
    description: Annotated[str, Form()] = "",
    scopes: Annotated[List[str], Form()] = [],
):
    role = db_session.get(RoleDB, role_id)
    if not role:
        raise HTTPException(status_code=404)
    role.name = name
    role.description = description or None
    role.scopes = scopes
    db_session.add(role)
    db_session.commit()
    return RedirectResponse(url="/admin/roles", status_code=status.HTTP_302_FOUND)


@router.post("/roles/{role_id}/delete", dependencies=[Depends(require_admin_session)])
async def delete_role(role_id: int, db_session: Annotated[Session, Depends(get_session)]):
    role = db_session.get(RoleDB, role_id)
    if not role:
        raise HTTPException(status_code=404)
    if role.users:
        raise HTTPException(status_code=400, detail="Não é possível excluir um papel com usuários vinculados.")
    db_session.delete(role)
    db_session.commit()
    return RedirectResponse(url="/admin/roles", status_code=status.HTTP_302_FOUND)
