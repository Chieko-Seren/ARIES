from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.auth import models, schemas, crud, deps, security
from core.database import get_db

router = APIRouter(prefix="/auth", tags=["认证与授权"])

# 认证相关路由
@router.post("/login", response_model=schemas.Token)
def login(
    db: Session = Depends(get_db),
    username: str = None,
    password: str = None
):
    """用户登录"""
    user = security.authenticate_user(db, username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户已被禁用"
        )
    
    # 获取用户权限
    user_permissions = security.get_user_permissions(user)
    user_roles = [role.name for role in user.roles]
    
    # 创建访问令牌
    access_token = security.create_access_token(
        subject=user.id,
        roles=user_roles,
        permissions=user_permissions
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

# 用户管理路由
@router.post("/users", response_model=schemas.User)
def create_user(
    user: schemas.UserCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_superuser)
):
    """创建新用户"""
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已被注册"
        )
    return crud.create_user(db=db, user=user)

@router.get("/users", response_model=List[schemas.User])
def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_superuser)
):
    """获取用户列表"""
    users = crud.get_users(db, skip=skip, limit=limit)
    return users

@router.get("/users/me", response_model=schemas.User)
def read_user_me(
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """获取当前用户信息"""
    return current_user

@router.get("/users/{user_id}", response_model=schemas.User)
def read_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_superuser)
):
    """获取指定用户信息"""
    db_user = crud.get_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    return db_user

@router.put("/users/{user_id}", response_model=schemas.User)
def update_user(
    user_id: int,
    user_update: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_superuser)
):
    """更新用户信息"""
    db_user = crud.update_user(db, user_id=user_id, user_update=user_update)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    return db_user

@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_superuser)
):
    """删除用户"""
    if not crud.delete_user(db, user_id=user_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    return {"message": "用户已删除"}

# 角色管理路由
@router.post("/roles", response_model=schemas.Role)
def create_role(
    role: schemas.RoleCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_superuser)
):
    """创建新角色"""
    db_role = crud.get_role_by_name(db, name=role.name)
    if db_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="角色名已存在"
        )
    return crud.create_role(db=db, role=role)

@router.get("/roles", response_model=List[schemas.Role])
def read_roles(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_superuser)
):
    """获取角色列表"""
    roles = crud.get_roles(db, skip=skip, limit=limit)
    return roles

@router.get("/roles/{role_id}", response_model=schemas.Role)
def read_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_superuser)
):
    """获取指定角色信息"""
    db_role = crud.get_role(db, role_id=role_id)
    if not db_role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在"
        )
    return db_role

@router.put("/roles/{role_id}", response_model=schemas.Role)
def update_role(
    role_id: int,
    role_update: schemas.RoleUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_superuser)
):
    """更新角色信息"""
    db_role = crud.update_role(db, role_id=role_id, role_update=role_update)
    if not db_role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在"
        )
    return db_role

@router.delete("/roles/{role_id}")
def delete_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_superuser)
):
    """删除角色"""
    if not crud.delete_role(db, role_id=role_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在"
        )
    return {"message": "角色已删除"}

# 权限管理路由
@router.post("/permissions", response_model=schemas.Permission)
def create_permission(
    permission: schemas.PermissionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_superuser)
):
    """创建新权限"""
    db_permission = crud.get_permission_by_code(db, code=permission.code)
    if db_permission:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="权限代码已存在"
        )
    return crud.create_permission(db=db, permission=permission)

@router.get("/permissions", response_model=List[schemas.Permission])
def read_permissions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_superuser)
):
    """获取权限列表"""
    permissions = crud.get_permissions(db, skip=skip, limit=limit)
    return permissions

@router.get("/permissions/{permission_id}", response_model=schemas.Permission)
def read_permission(
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_superuser)
):
    """获取指定权限信息"""
    db_permission = crud.get_permission(db, permission_id=permission_id)
    if not db_permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="权限不存在"
        )
    return db_permission

@router.put("/permissions/{permission_id}", response_model=schemas.Permission)
def update_permission(
    permission_id: int,
    permission_update: schemas.PermissionUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_superuser)
):
    """更新权限信息"""
    db_permission = crud.update_permission(
        db,
        permission_id=permission_id,
        permission_update=permission_update
    )
    if not db_permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="权限不存在"
        )
    return db_permission

@router.delete("/permissions/{permission_id}")
def delete_permission(
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_superuser)
):
    """删除权限"""
    if not crud.delete_permission(db, permission_id=permission_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="权限不存在"
        )
    return {"message": "权限已删除"}

# 用户权限管理路由
@router.post("/users/{user_id}/permissions/{permission_id}")
def grant_user_permission(
    user_id: int,
    permission_id: int,
    is_granted: bool = True,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_superuser)
):
    """授予或撤销用户权限"""
    db_user = crud.get_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    db_permission = crud.get_permission(db, permission_id=permission_id)
    if not db_permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="权限不存在"
        )
    
    db_user_permission = crud.grant_user_permission(
        db,
        user_id=user_id,
        permission_id=permission_id,
        is_granted=is_granted
    )
    return {
        "message": "权限已更新",
        "user_id": user_id,
        "permission_id": permission_id,
        "is_granted": is_granted
    }

@router.delete("/users/{user_id}/permissions/{permission_id}")
def revoke_user_permission(
    user_id: int,
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_superuser)
):
    """撤销用户权限"""
    if not crud.revoke_user_permission(db, user_id=user_id, permission_id=permission_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户权限不存在"
        )
    return {"message": "权限已撤销"}

# 权限检查路由
@router.get("/check-permission", response_model=schemas.PermissionCheck)
def check_user_permission(
    permission: str,
    current_user: models.User = Depends(deps.get_current_user)
):
    """检查当前用户是否具有指定权限"""
    user_permissions = security.get_user_permissions(current_user)
    has_permission = security.check_permission(permission, user_permissions)
    return {
        "has_permission": has_permission,
        "required_permission": permission,
        "user_permissions": user_permissions
    } 