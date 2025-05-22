#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ARIES - API数据模型
定义API请求和响应的数据模型
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

# 认证相关模型
class User(BaseModel):
    """用户模型"""
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None
    hashed_password: str

class UserInDB(User):
    """数据库中的用户模型"""
    pass

class UserCreate(BaseModel):
    """创建用户请求模型"""
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    password: str

class Token(BaseModel):
    """令牌模型"""
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """令牌数据模型"""
    username: Optional[str] = None

# 服务器相关模型
class ServerInfo(BaseModel):
    """服务器信息模型"""
    id: str
    name: str
    ip: str
    connection_type: str
    username: Optional[str] = None
    password: Optional[str] = None
    key_file: Optional[str] = None
    expected_services: Optional[List[str]] = None
    description: Optional[str] = None

class ServerStatus(BaseModel):
    """服务器状态模型"""
    id: str
    name: str
    healthy: bool
    message: str
    details: Dict[str, Any]
    last_check: datetime

# API请求模型
class ShellRequest(BaseModel):
    """Shell命令请求模型"""
    system_type: str = Field(..., description="系统类型，如linux, windows等")
    description: str = Field(..., description="命令的自然语言描述")

class TaskRequest(BaseModel):
    """运维任务请求模型"""
    description: str = Field(..., description="任务的自然语言描述")
    server_ids: Optional[List[str]] = Field(None, description="可选的服务器ID列表")

class StatisticsRequest(BaseModel):
    """统计分析请求模型"""
    query: str = Field(..., description="分析查询")

class DataRequest(BaseModel):
    """数据请求模型"""
    days: int = Field(7, description="获取最近几天的数据")

class KubeRequest(BaseModel):
    """Kubernetes管理请求模型"""
    description: str = Field(..., description="Kubernetes管理任务的自然语言描述")

class NetworkRequest(BaseModel):
    """网络管理请求模型"""
    description: str = Field(..., description="网络管理任务的自然语言描述")

# API响应模型
class ApiResponse(BaseModel):
    """API通用响应模型"""
    success: bool
    message: Optional[str] = None
    data: Optional[Any] = None
    error: Optional[str] = None