from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from ..db import db_cursor
from ..auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterIn(BaseModel):
    username: str
    password: str


class LoginIn(BaseModel):
    username: str
    password: str


class ChangePasswordIn(BaseModel):
    old_password: str
    new_password: str


@router.post("/register")
def register(data: RegisterIn):
    username = data.username.strip()
    password = data.password.strip()

    if not username or not password:
        raise HTTPException(status_code=400, detail="用户名和密码不能为空")
    if len(username) < 3:
        raise HTTPException(status_code=400, detail="用户名至少3位")
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="密码至少6位")

    with db_cursor() as (_, cur):
        cur.execute("SELECT id FROM users WHERE username=%s", (username,))
        if cur.fetchone():
            raise HTTPException(status_code=400, detail="用户名已存在")

        cur.execute(
            "INSERT INTO users(username, password_hash, role, is_active) VALUES(%s,%s,%s,%s)",
            (username, hash_password(password), "analyst", 1),
        )
        user_id = cur.lastrowid

    token = create_access_token({"uid": user_id, "username": username, "role": "analyst"})
    return {
        "token": token,
        "user": {
            "id": user_id,
            "username": username,
            "role": "analyst",
        },
    }


@router.post("/login")
def login(data: LoginIn):
    username = data.username.strip()
    password = data.password.strip()

    with db_cursor() as (_, cur):
        cur.execute(
            "SELECT id, username, password_hash, role, is_active FROM users WHERE username=%s",
            (username,),
        )
        user = cur.fetchone()

    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    if not int(user["is_active"]):
        raise HTTPException(status_code=403, detail="账号已停用")
    if not verify_password(password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    token = create_access_token(
        {"uid": user["id"], "username": user["username"], "role": user["role"]}
    )
    return {
        "token": token,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "role": user["role"],
        },
    }


@router.get("/me")
def me(current=Depends(get_current_user)):
    with db_cursor() as (_, cur):
        cur.execute(
            "SELECT id, username, role, is_active, created_at FROM users WHERE id=%s",
            (current["uid"],),
        )
        user = cur.fetchone()

    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    return {
        "id": user["id"],
        "username": user["username"],
        "role": user["role"],
        "is_active": user["is_active"],
        "created_at": str(user["created_at"]),
    }


@router.post("/change_password")
def change_password(data: ChangePasswordIn, current=Depends(get_current_user)):
    old_password = data.old_password.strip()
    new_password = data.new_password.strip()

    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="新密码至少6位")

    with db_cursor() as (_, cur):
        cur.execute(
            "SELECT id, password_hash FROM users WHERE id=%s",
            (current["uid"],),
        )
        user = cur.fetchone()

        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")

        if not verify_password(old_password, user["password_hash"]):
            raise HTTPException(status_code=400, detail="原密码错误")

        cur.execute(
            "UPDATE users SET password_hash=%s WHERE id=%s",
            (hash_password(new_password), current["uid"]),
        )

    return {"ok": True, "message": "密码修改成功"}