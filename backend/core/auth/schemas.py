from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, constr

# 基础模型
class PermissionBase(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    resource_type: str
    resource_id: str
    action: str

class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None

class UserBase(BaseModel):
    username: constr(min_length=3, max_length=50)
    email: EmailStr
    is_active: bool = True
    is_superuser: bool = False

# 创建模型
class PermissionCreate(PermissionBase):
    pass

class RoleCreate(RoleBase):
    permission_ids: Optional[List[int]] = None

class UserCreate(UserBase):
    password: constr(min_length=8)
    role_ids: Optional[List[int]] = None

# 更新模型
class PermissionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    action: Optional[str] = None

class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permission_ids: Optional[List[int]] = None

class UserUpdate(BaseModel):
    username: Optional[constr(min_length=3, max_length=50)] = None
    email: Optional[EmailStr] = None
    password: Optional[constr(min_length=8)] = None
    is_active: Optional[bool] = None
    role_ids: Optional[List[int]] = None

# 响应模型
class Permission(PermissionBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class Role(RoleBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    permissions: List[Permission] = []

    class Config:
        from_attributes = True

class User(UserBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    roles: List[Role] = []

    class Config:
        from_attributes = True

# Token 模型
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class TokenPayload(BaseModel):
    sub: int  # user id
    exp: int  # expiration time
    roles: List[str] = []
    permissions: List[str] = []

# 用户权限检查响应
class PermissionCheck(BaseModel):
    has_permission: bool
    required_permission: str
    user_permissions: List[str] 