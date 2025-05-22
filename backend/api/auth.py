#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ARIES - 认证模块
实现用户认证和令牌生成功能
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import json
import os

# 导入内部模块
from api.models import User, TokenData
from config.settings import Settings

# 获取配置
settings = Settings()

# 密码上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2密码Bearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

# 用户数据文件路径
USERS_FILE = os.path.join(os.path.dirname(settings.servers_config_path), "users.json")

def verify_password(plain_password, hashed_password):
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """获取密码哈希"""
    return pwd_context.hash(password)

def get_users():
    """获取所有用户"""
    if not os.path.exists(USERS_FILE):
        # 创建默认用户
        create_default_users()
    
    try:
        with open(USERS_FILE, 'r') as f:
            users = json.load(f)
        return users
    except Exception as e:
        print(f"读取用户数据失败: {str(e)}")
        return {}

def create_default_users():
    """创建默认用户"""
    default_users = {
        "admin": {
            "username": "admin",
            "email": "admin@example.com",
            "full_name": "管理员",
            "disabled": False,
            "hashed_password": get_password_hash("admin")
        }
    }
    
    os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
    
    with open(USERS_FILE, 'w') as f:
        json.dump(default_users, f, indent=2, ensure_ascii=False)
    
    print(f"已创建默认用户文件: {USERS_FILE}")

def get_user(username: str):
    """获取用户"""
    users = get_users()
    if username in users:
        user_dict = users[username]
        return User(**user_dict)
    return None

def authenticate_user(username: str, password: str):
    """认证用户"""
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """创建访问令牌"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm="HS256")
    
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """获取当前用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    user = get_user(token_data.username)
    if user is None:
        raise credentials_exception
    
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    """获取当前活跃用户"""
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="用户已禁用")
    return current_user