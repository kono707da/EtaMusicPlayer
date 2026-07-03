"""用户管理（admin）"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.plugins.local_node.database import get_db
from app.plugins.local_node.deps import require_admin
from app.plugins.local_node.models import User
from app.plugins.local_node.schemas import UserCreate, UserOut, UserUpdate
from app.security import hash_password


router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("", response_model=list[UserOut])
def list_users(
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
) -> list[UserOut]:
    """列出所有用户"""
    users = db.query(User).order_by(User.id).all()
    return [UserOut.model_validate(u) for u in users]


@router.post("", response_model=UserOut, status_code=201)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
) -> UserOut:
    """创建用户"""
    existing = db.query(User).filter(User.username == payload.username).first()
    if existing is not None:
        raise HTTPException(status_code=400, detail="用户名已存在")
    u = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        is_admin=payload.is_admin,
        is_active=True,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return UserOut.model_validate(u)


@router.put("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
) -> UserOut:
    """更新用户"""
    u = db.get(User, user_id)
    if u is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    if payload.password is not None:
        u.password_hash = hash_password(payload.password)
    if payload.is_admin is not None:
        u.is_admin = payload.is_admin
    if payload.is_active is not None:
        u.is_active = payload.is_active
    db.commit()
    db.refresh(u)
    return UserOut.model_validate(u)


@router.delete("/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    """删除用户（不可删除自己、不可删除最后一个 admin）"""
    if user.id == user_id:
        raise HTTPException(status_code=400, detail="不可删除当前登录用户")
    u = db.get(User, user_id)
    if u is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    if u.is_admin:
        admin_count = db.query(User).filter(User.is_admin.is_(True)).count()
        if admin_count <= 1:
            raise HTTPException(status_code=400, detail="不可删除最后一个管理员")
    db.delete(u)
    db.commit()
