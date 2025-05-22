#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ARIES - API路由
实现RESTful API接口
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

# 导入内部模块
from config.settings import Settings
from core.agent import Agent
from api.auth import create_access_token, get_current_user, get_current_active_user
from api.models import (
    User, Token, ServerInfo, ServerStatus, 
    ShellRequest, TaskRequest, StatisticsRequest, 
    DataRequest, KubeRequest, NetworkRequest, ApiResponse
)

# 创建路由
router = APIRouter(prefix="/api")

# 获取配置和Agent实例
settings = Settings()
agent = None  # 将在应用启动时初始化

# 初始化Agent
def init_agent(settings_instance: Settings):
    """初始化Agent实例"""
    global agent
    agent = Agent(settings_instance)
    return agent

# 认证相关路由
@router.post("/auth/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """获取访问令牌"""
    from api.auth import authenticate_user, get_user
    
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码不正确",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

# 服务器相关路由
@router.get("/servers", response_model=List[ServerInfo])
async def get_servers(current_user: User = Depends(get_current_active_user)):
    """获取所有服务器信息"""
    return agent.servers

@router.get("/servers/status", response_model=List[ServerStatus])
async def get_servers_status(current_user: User = Depends(get_current_active_user)):
    """获取所有服务器状态"""
    statuses = []
    for server in agent.servers:
        status = agent._check_server_status(server)
        statuses.append({
            "id": server["id"],
            "name": server.get("name", server["id"]),
            "healthy": status["healthy"],
            "message": status["message"],
            "details": status["details"],
            "last_check": datetime.now()
        })
    return statuses

@router.get("/servers/{server_id}", response_model=ServerInfo)
async def get_server(server_id: str, current_user: User = Depends(get_current_active_user)):
    """获取指定服务器信息"""
    server = next((s for s in agent.servers if s["id"] == server_id), None)
    if not server:
        raise HTTPException(status_code=404, detail=f"服务器 {server_id} 不存在")
    return server

@router.get("/servers/{server_id}/status", response_model=ServerStatus)
async def get_server_status(server_id: str, current_user: User = Depends(get_current_active_user)):
    """获取指定服务器状态"""
    server = next((s for s in agent.servers if s["id"] == server_id), None)
    if not server:
        raise HTTPException(status_code=404, detail=f"服务器 {server_id} 不存在")
    
    status = agent._check_server_status(server)
    return {
        "id": server["id"],
        "name": server.get("name", server["id"]),
        "healthy": status["healthy"],
        "message": status["message"],
        "details": status["details"],
        "last_check": datetime.now()
    }

# Shell命令路由
@router.post("/shell", response_model=ApiResponse)
async def execute_shell(request: ShellRequest, current_user: User = Depends(get_current_active_user)):
    """执行Shell命令"""
    result = agent.execute_shell(request.system_type, request.description)
    
    if result.get("success", False):
        return {
            "success": True,
            "message": "命令执行成功",
            "data": result
        }
    else:
        return {
            "success": False,
            "message": "命令执行失败",
            "error": result.get("error", "未知错误")
        }

# 运维任务路由
@router.post("/eval", response_model=ApiResponse)
async def execute_task(request: TaskRequest, current_user: User = Depends(get_current_active_user)):
    """执行运维任务"""
    result = agent.execute_task(request.description, request.server_ids)
    
    if result.get("success", False):
        return {
            "success": True,
            "message": "任务执行成功",
            "data": result
        }
    else:
        return {
            "success": False,
            "message": "任务执行失败",
            "error": result.get("error", "未知错误")
        }

# 统计分析路由
@router.post("/statistics", response_model=ApiResponse)
async def analyze_statistics(request: StatisticsRequest, current_user: User = Depends(get_current_active_user)):
    """分析系统数据"""
    result = agent.analyze_statistics(request.query)
    
    if result.get("success", False):
        return {
            "success": True,
            "message": "分析完成",
            "data": result
        }
    else:
        return {
            "success": False,
            "message": "分析失败",
            "error": result.get("error", "未知错误")
        }

# 数据获取路由
@router.post("/data", response_model=ApiResponse)
async def get_data(request: DataRequest, current_user: User = Depends(get_current_active_user)):
    """获取系统数据"""
    result = agent.get_recent_data(request.days)
    
    return {
        "success": True,
        "message": f"获取最近{request.days}天的数据",
        "data": result
    }

# Kubernetes管理路由
@router.post("/kube", response_model=ApiResponse)
async def manage_kubernetes(request: KubeRequest, current_user: User = Depends(get_current_active_user)):
    """执行Kubernetes管理任务"""
    result = agent.manage_kubernetes(request.description)
    
    if result.get("success", False):
        return {
            "success": True,
            "message": "Kubernetes任务执行成功",
            "data": result
        }
    else:
        return {
            "success": False,
            "message": "Kubernetes任务执行失败",
            "error": result.get("error", "未知错误")
        }

# 网络管理路由
@router.post("/network", response_model=ApiResponse)
async def manage_network(request: NetworkRequest, current_user: User = Depends(get_current_active_user)):
    """执行网络管理任务"""
    result = agent.manage_network(request.description)
    
    if result.get("success", False):
        return {
            "success": True,
            "message": "网络任务执行成功",
            "data": result
        }
    else:
        return {
            "success": False,
            "message": "网络任务执行失败",
            "error": result.get("error", "未知错误")
        }