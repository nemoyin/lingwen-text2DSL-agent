"""RBAC API — roles, permissions, user role assignment."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.api.deps import get_db, get_current_user
from app.utils.response import success

router = APIRouter()

AVAILABLE_PERMISSIONS = [
    {"key": "dashboard", "label": "仪表盘"},
    {"key": "chat", "label": "对话问数"},
    {"key": "alerts", "label": "预警列表"},
    {"key": "alert_create", "label": "创建预警"},
    {"key": "case_manage", "label": "问题线索"},
    {"key": "history", "label": "对话历史"},
    {"key": "profile", "label": "个人中心"},
    {"key": "admin", "label": "管理后台"},
    {"key": "admin_datasources", "label": "数据源管理"},
    {"key": "admin_metadata", "label": "元数据管理"},
    {"key": "admin_skills", "label": "Skill模板"},
    {"key": "admin_fewshot", "label": "Few-shot"},
    {"key": "admin_roles", "label": "角色管理"},
    {"key": "admin_users", "label": "用户管理"},
]


@router.get("/permissions")
async def list_permissions(user: dict = Depends(get_current_user)) -> dict:
    """Return all available permissions and current user's permissions."""
    return success(data=AVAILABLE_PERMISSIONS)


@router.get("/roles")
async def list_roles(db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)) -> dict:
    result = await db.execute(text("SELECT * FROM roles ORDER BY id"))
    roles = [dict(zip(result.keys(), r)) for r in result.fetchall()]
    for role in roles:
        pr = await db.execute(text("SELECT permission_key FROM role_permissions WHERE role_id=:rid"), {"rid": role["id"]})
        role["permissions"] = [r[0] for r in pr.fetchall()]
        ur = await db.execute(text("SELECT user_id FROM user_roles WHERE role_id=:rid"), {"rid": role["id"]})
        role["user_ids"] = [r[0] for r in ur.fetchall()]
    return success(data=roles)


@router.post("/roles")
async def create_role(name: str = "", description: str = "", db: AsyncSession = Depends(get_db)) -> dict:
    result = await db.execute(text("INSERT INTO roles (name, description) VALUES (:n,:d)"), {"n": name, "d": description})
    await db.commit()
    return success(data={"id": result.lastrowid})


@router.put("/roles/{role_id}/permissions")
async def update_role_permissions(role_id: int, permissions: str = "", db: AsyncSession = Depends(get_db)) -> dict:
    perms = [p.strip() for p in permissions.split(",") if p.strip()]
    await db.execute(text("DELETE FROM role_permissions WHERE role_id=:rid"), {"rid": role_id})
    for p in perms:
        await db.execute(text("INSERT INTO role_permissions (role_id, permission_key) VALUES (:rid,:p)"), {"rid": role_id, "p": p})
    await db.commit()
    return success(message="权限已更新")


@router.delete("/roles/{role_id}")
async def delete_role(role_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    await db.execute(text("DELETE FROM roles WHERE id=:rid"), {"rid": role_id})
    await db.commit()
    return success(message="角色已删除")


@router.get("/users")
async def list_users(db: AsyncSession = Depends(get_db)) -> dict:
    result = await db.execute(text("SELECT id, username, role, is_active, created_at FROM users ORDER BY id"))
    users = [dict(zip(result.keys(), r)) for r in result.fetchall()]
    for u in users:
        ur = await db.execute(text("SELECT r.id, r.name FROM user_roles ur JOIN roles r ON ur.role_id=r.id WHERE ur.user_id=:uid"), {"uid": u["id"]})
        u["roles"] = [dict(zip(ur.keys(), r)) for r in ur.fetchall()]
        if u.get("created_at"):
            u["created_at"] = str(u["created_at"])
    return success(data=users)


@router.post("/users")
async def create_user(
    username: str = "",
    password: str = "",
    role_name: str = "viewer",
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create a new user with defaults."""
    from app.services.auth_service import hash_password
    import bcrypt
    pwd_hash = hash_password(password)
    try:
        result = await db.execute(
            text("INSERT INTO users (username, password_hash, role) VALUES (:u, :p, :r)"),
            {"u": username, "p": pwd_hash, "r": role_name}
        )
        await db.commit()
        user_id = result.lastrowid
        # Assign default viewer role
        role_result = await db.execute(text("SELECT id FROM roles WHERE name=:rn"), {"rn": role_name})
        role_row = role_result.fetchone()
        if role_row:
            await db.execute(text("INSERT IGNORE INTO user_roles (user_id, role_id) VALUES (:uid, :rid)"), {"uid": user_id, "rid": role_row[0]})
            await db.commit()
        return success(data={"id": user_id, "username": username})
    except Exception as e:
        if "Duplicate" in str(e):
            raise HTTPException(409, "用户名已存在")
        raise HTTPException(500, str(e))


@router.put("/users/{user_id}/reset-password")
async def reset_password(user_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    from app.services.auth_service import hash_password
    pwd_hash = hash_password("123456")
    await db.execute(text("UPDATE users SET password_hash=:p WHERE id=:uid"), {"p": pwd_hash, "uid": user_id})
    await db.commit()
    return success(message="密码已重置为 123456")

@router.put("/users/{user_id}/roles")
async def update_user_roles(user_id: int, role_ids: str = "", db: AsyncSession = Depends(get_db)) -> dict:
    ids = [int(x) for x in role_ids.split(",") if x.strip().isdigit()]
    await db.execute(text("DELETE FROM user_roles WHERE user_id=:uid"), {"uid": user_id})
    for rid in ids:
        await db.execute(text("INSERT INTO user_roles (user_id, role_id) VALUES (:uid,:rid)"), {"uid": user_id, "rid": rid})
    await db.commit()
    return success(message="用户角色已更新")


@router.get("/my-permissions")
async def my_permissions(db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)) -> dict:
    result = await db.execute(text(
        "SELECT DISTINCT rp.permission_key FROM user_roles ur JOIN role_permissions rp ON ur.role_id=rp.role_id WHERE ur.user_id=:uid"
    ), {"uid": user["user_id"]})
    perms = [r[0] for r in result.fetchall()]
    if user["user_id"] == 1:  # admin has all
        perms = [p["key"] for p in AVAILABLE_PERMISSIONS]
    return success(data=perms)
