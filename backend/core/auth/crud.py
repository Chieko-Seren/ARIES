from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from core.auth import models, schemas
from core.auth.security import get_password_hash

# User CRUD
def get_user(db: Session, user_id: int) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.username == username).first()

def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.email == email).first()

def get_users(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    filters: Dict[str, Any] = None
) -> List[models.User]:
    query = db.query(models.User)
    if filters:
        for key, value in filters.items():
            if hasattr(models.User, key):
                query = query.filter(getattr(models.User, key) == value)
    return query.offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        is_active=user.is_active,
        is_superuser=user.is_superuser
    )
    
    if user.role_ids:
        roles = db.query(models.Role).filter(models.Role.id.in_(user.role_ids)).all()
        db_user.roles = roles
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(
    db: Session,
    user_id: int,
    user_update: schemas.UserUpdate
) -> Optional[models.User]:
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    
    update_data = user_update.dict(exclude_unset=True)
    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    
    if "role_ids" in update_data:
        role_ids = update_data.pop("role_ids")
        if role_ids is not None:
            roles = db.query(models.Role).filter(models.Role.id.in_(role_ids)).all()
            db_user.roles = roles
    
    for key, value in update_data.items():
        setattr(db_user, key, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: int) -> bool:
    db_user = get_user(db, user_id)
    if not db_user:
        return False
    db.delete(db_user)
    db.commit()
    return True

# Role CRUD
def get_role(db: Session, role_id: int) -> Optional[models.Role]:
    return db.query(models.Role).filter(models.Role.id == role_id).first()

def get_role_by_name(db: Session, name: str) -> Optional[models.Role]:
    return db.query(models.Role).filter(models.Role.name == name).first()

def get_roles(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    filters: Dict[str, Any] = None
) -> List[models.Role]:
    query = db.query(models.Role)
    if filters:
        for key, value in filters.items():
            if hasattr(models.Role, key):
                query = query.filter(getattr(models.Role, key) == value)
    return query.offset(skip).limit(limit).all()

def create_role(db: Session, role: schemas.RoleCreate) -> models.Role:
    db_role = models.Role(
        name=role.name,
        description=role.description
    )
    
    if role.permission_ids:
        permissions = db.query(models.Permission).filter(
            models.Permission.id.in_(role.permission_ids)
        ).all()
        db_role.permissions = permissions
    
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role

def update_role(
    db: Session,
    role_id: int,
    role_update: schemas.RoleUpdate
) -> Optional[models.Role]:
    db_role = get_role(db, role_id)
    if not db_role:
        return None
    
    update_data = role_update.dict(exclude_unset=True)
    if "permission_ids" in update_data:
        permission_ids = update_data.pop("permission_ids")
        if permission_ids is not None:
            permissions = db.query(models.Permission).filter(
                models.Permission.id.in_(permission_ids)
            ).all()
            db_role.permissions = permissions
    
    for key, value in update_data.items():
        setattr(db_role, key, value)
    
    db.commit()
    db.refresh(db_role)
    return db_role

def delete_role(db: Session, role_id: int) -> bool:
    db_role = get_role(db, role_id)
    if not db_role:
        return False
    db.delete(db_role)
    db.commit()
    return True

# Permission CRUD
def get_permission(db: Session, permission_id: int) -> Optional[models.Permission]:
    return db.query(models.Permission).filter(models.Permission.id == permission_id).first()

def get_permission_by_code(db: Session, code: str) -> Optional[models.Permission]:
    return db.query(models.Permission).filter(models.Permission.code == code).first()

def get_permissions(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    filters: Dict[str, Any] = None
) -> List[models.Permission]:
    query = db.query(models.Permission)
    if filters:
        for key, value in filters.items():
            if hasattr(models.Permission, key):
                query = query.filter(getattr(models.Permission, key) == value)
    return query.offset(skip).limit(limit).all()

def create_permission(
    db: Session,
    permission: schemas.PermissionCreate
) -> models.Permission:
    db_permission = models.Permission(**permission.dict())
    db.add(db_permission)
    db.commit()
    db.refresh(db_permission)
    return db_permission

def update_permission(
    db: Session,
    permission_id: int,
    permission_update: schemas.PermissionUpdate
) -> Optional[models.Permission]:
    db_permission = get_permission(db, permission_id)
    if not db_permission:
        return None
    
    update_data = permission_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_permission, key, value)
    
    db.commit()
    db.refresh(db_permission)
    return db_permission

def delete_permission(db: Session, permission_id: int) -> bool:
    db_permission = get_permission(db, permission_id)
    if not db_permission:
        return False
    db.delete(db_permission)
    db.commit()
    return True

# User Permission CRUD
def get_user_permission(
    db: Session,
    user_id: int,
    permission_id: int
) -> Optional[models.UserPermission]:
    return db.query(models.UserPermission).filter(
        and_(
            models.UserPermission.user_id == user_id,
            models.UserPermission.permission_id == permission_id
        )
    ).first()

def grant_user_permission(
    db: Session,
    user_id: int,
    permission_id: int,
    is_granted: bool = True
) -> models.UserPermission:
    db_user_permission = get_user_permission(db, user_id, permission_id)
    if db_user_permission:
        db_user_permission.is_granted = is_granted
    else:
        db_user_permission = models.UserPermission(
            user_id=user_id,
            permission_id=permission_id,
            is_granted=is_granted
        )
        db.add(db_user_permission)
    
    db.commit()
    db.refresh(db_user_permission)
    return db_user_permission

def revoke_user_permission(
    db: Session,
    user_id: int,
    permission_id: int
) -> bool:
    db_user_permission = get_user_permission(db, user_id, permission_id)
    if not db_user_permission:
        return False
    db.delete(db_user_permission)
    db.commit()
    return True 