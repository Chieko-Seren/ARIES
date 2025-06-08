from datetime import datetime, timedelta
from typing import Any, Optional, Union, List
from jose import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from core.config import settings
from core.auth import models, schemas
from core.auth.crud import get_user_by_username

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """获取密码哈希值"""
    return pwd_context.hash(password)

def create_access_token(
    subject: Union[str, Any],
    expires_delta: Optional[timedelta] = None,
    roles: List[str] = None,
    permissions: List[str] = None
) -> str:
    """创建访问令牌"""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "roles": roles or [],
        "permissions": permissions or []
    }
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt

def authenticate_user(
    db: Session,
    username: str,
    password: str
) -> Optional[models.User]:
    """验证用户"""
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def get_user_permissions(user: models.User) -> List[str]:
    """获取用户所有权限"""
    permissions = set()
    
    # 获取角色权限
    for role in user.roles:
        for permission in role.permissions:
            permissions.add(f"{permission.resource_type}:{permission.resource_id}:{permission.action}")
    
    # 获取直接授予的权限
    for user_permission in user.user_permissions:
        if user_permission.is_granted:
            permission = user_permission.permission
            permissions.add(f"{permission.resource_type}:{permission.resource_id}:{permission.action}")
    
    return list(permissions)

def check_permission(
    required_permission: str,
    user_permissions: List[str]
) -> bool:
    """检查用户是否具有所需权限"""
    # 支持通配符权限检查
    # 例如：如果用户有 "api:*:read" 权限，则可以访问所有 API 的读操作
    for user_permission in user_permissions:
        if user_permission == required_permission:
            return True
        if "*" in user_permission:
            # 将通配符转换为正则表达式模式
            pattern = user_permission.replace("*", ".*")
            import re
            if re.match(pattern, required_permission):
                return True
    return False

def get_current_user_permissions(
    token: str = None,
    db: Session = None
) -> List[str]:
    """获取当前用户的权限列表"""
    if not token or not db:
        return []
    
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            return []
        
        user = db.query(models.User).filter(models.User.id == int(user_id)).first()
        if not user:
            return []
        
        return get_user_permissions(user)
    except jwt.JWTError:
        return []

def verify_token(token: str) -> schemas.TokenPayload:
    """验证令牌"""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return schemas.TokenPayload(**payload)
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        ) 