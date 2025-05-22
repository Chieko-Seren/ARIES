#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ARIES - AI Native 自动运维系统主程序
"""

import os
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import schedule
import time
import threading

# 导入内部模块
from config.settings import Settings
from core.agent import Agent
from api.auth import create_access_token, get_current_user, verify_password, get_password_hash
from api.models import User, Token, ServerInfo, TaskRequest, ShellRequest, KubeRequest, NetworkRequest
from api.routes import router as api_router

# 加载配置
settings = Settings()

# 创建FastAPI应用
app = FastAPI(
    title="ARIES API",
    description="AI Native 自动运维系统API",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置为特定域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含API路由
app.include_router(api_router)

# 创建Agent实例
agent = Agent(settings)

# 监控任务
def monitoring_task():
    """定时监控任务，每分钟执行一次"""
    print(f"[{datetime.now()}] 执行监控任务...")
    agent.monitor()

# 启动定时任务
def start_scheduler():
    schedule.every(1).minutes.do(monitoring_task)
    while True:
        schedule.run_pending()
        time.sleep(1)

@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    # 启动定时任务线程
    scheduler_thread = threading.Thread(target=start_scheduler, daemon=True)
    scheduler_thread.start()
    print("ARIES 自动运维系统已启动")

@app.get("/")
async def root():
    """API根路径"""
    return {"message": "欢迎使用ARIES自动运维系统API"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)