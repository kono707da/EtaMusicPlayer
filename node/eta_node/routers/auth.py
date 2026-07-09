"""认证路由"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from eta_node.database import get_db
from eta_node.deps import get_current_user_dependency
from eta_node.models import User
from eta_node.schemas import LoginRequest, TokenResponse, UserOut
from eta_node.security import create_access_token, decode_token, hash_password, verify_password


router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """用户名密码登录，返回 JWT"""
    user = db.query(User).filter(User.username == payload.username).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="用户已被禁用")
    token = create_access_token(
        subject=user.id,
        extra={"username": user.username, "is_admin": user.is_admin},
    )
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db),
) -> TokenResponse:
    """刷新 token：返回新的 access_token"""
    token = create_access_token(
        subject=user.id,
        extra={"username": user.username, "is_admin": user.is_admin},
    )
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user_dependency)) -> UserOut:
    """获取当前登录用户信息"""
    return UserOut.model_validate(user)
