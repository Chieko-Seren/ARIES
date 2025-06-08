from sqlalchemy.orm import Session
from core.auth import crud, schemas, security
from core.database import Base, engine

def init_db(db: Session) -> None:
    """初始化数据库"""
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    
    # 创建超级管理员角色
    admin_role = crud.get_role_by_name(db, name="超级管理员")
    if not admin_role:
        admin_role = crud.create_role(
            db,
            schemas.RoleCreate(
                name="超级管理员",
                description="系统超级管理员，拥有所有权限"
            )
        )
    
    # 创建基础权限
    base_permissions = [
        {
            "name": "用户管理",
            "code": "user_manage",
            "description": "用户管理相关权限",
            "resource_type": "api",
            "resource_id": "users",
            "action": "*"
        },
        {
            "name": "角色管理",
            "code": "role_manage",
            "description": "角色管理相关权限",
            "resource_type": "api",
            "resource_id": "roles",
            "action": "*"
        },
        {
            "name": "权限管理",
            "code": "permission_manage",
            "description": "权限管理相关权限",
            "resource_type": "api",
            "resource_id": "permissions",
            "action": "*"
        }
    ]
    
    for perm_data in base_permissions:
        permission = crud.get_permission_by_code(db, code=perm_data["code"])
        if not permission:
            permission = crud.create_permission(
                db,
                schemas.PermissionCreate(**perm_data)
            )
            # 将权限授予超级管理员角色
            admin_role.permissions.append(permission)
    
    db.commit()
    
    # 创建超级管理员用户
    admin_user = crud.get_user_by_username(db, username="admin")
    if not admin_user:
        admin_user = crud.create_user(
            db,
            schemas.UserCreate(
                username="admin",
                email="admin@example.com",
                password="admin123",  # 请在生产环境中修改此密码
                is_active=True,
                is_superuser=True,
                role_ids=[admin_role.id]
            )
        )
    
    db.commit()

if __name__ == "__main__":
    from core.database import SessionLocal
    db = SessionLocal()
    init_db(db)
    db.close() 