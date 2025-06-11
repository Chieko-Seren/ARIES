from fastapi import FastAPI, Request, Response, HTTPException, Depends, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
import secrets
import os
from typing import Optional
from datetime import datetime, timedelta
import uvicorn
from pathlib import Path

# 创建 FastAPI 应用
app = FastAPI(title="ARIES Web Lite")

# 配置会话中间件
app.add_middleware(
    SessionMiddleware,
    secret_key=secrets.token_hex(32),
    session_cookie="aries_session",
    max_age=7 * 24 * 60 * 60  # 7 days
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

# 配置模板
templates = Jinja2Templates(directory="templates")

# 安全配置
security = HTTPBasic()

# 默认密码
DEFAULT_PASSWORD = os.getenv("ARIES_WEB_PASSWORD", "aries2025")

# 用户会话管理
class SessionManager:
    def __init__(self):
        self.sessions = {}

    def create_session(self, request: Request) -> str:
        session_id = secrets.token_hex(16)
        self.sessions[session_id] = {
            "created_at": datetime.now(),
            "expires_at": datetime.now() + timedelta(days=7)
        }
        return session_id

    def validate_session(self, request: Request) -> bool:
        session_id = request.session.get("session_id")
        if not session_id or session_id not in self.sessions:
            return False
        
        session = self.sessions[session_id]
        if datetime.now() > session["expires_at"]:
            del self.sessions[session_id]
            return False
        
        return True

    def remove_session(self, request: Request):
        session_id = request.session.get("session_id")
        if session_id in self.sessions:
            del self.sessions[session_id]

session_manager = SessionManager()

async def get_current_user(request: Request) -> Optional[str]:
    if not session_manager.validate_session(request):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录或会话已过期",
            headers={"WWW-Authenticate": "Basic"},
        )
    return "authenticated"

@app.get("/", response_class=HTMLResponse)
async def index(request: Request, user: str = Depends(get_current_user)):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if session_manager.validate_session(request):
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": None}
    )

@app.post("/login")
async def login(request: Request):
    form_data = await request.form()
    password = form_data.get("password")
    
    if password == DEFAULT_PASSWORD:
        session_id = session_manager.create_session(request)
        response = RedirectResponse(url="/", status_code=303)
        request.session["session_id"] = session_id
        return response
    
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": "密码错误"},
        status_code=status.HTTP_401_UNAUTHORIZED
    )

@app.get("/logout")
async def logout(request: Request):
    session_manager.remove_session(request)
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("aries_session")
    return response

# 静态文件路由
@app.get("/{path:path}")
async def serve_static(
    path: str,
    request: Request,
    user: str = Depends(get_current_user)
):
    static_path = Path(".") / path
    if static_path.exists() and static_path.is_file():
        return templates.TemplateResponse(
            str(static_path),
            {"request": request}
        )
    raise HTTPException(status_code=404, detail="文件未找到")

if __name__ == "__main__":
    print(f"ARIES Web Lite 服务器启动在 http://localhost:5000")
    print("默认密码：", DEFAULT_PASSWORD)
    print("提示：可以通过设置环境变量 ARIES_WEB_PASSWORD 来修改密码")
    
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=5000,
        workers=4,  # 根据 CPU 核心数调整
        proxy_headers=True,
        forwarded_allow_ips="*"
    ) 