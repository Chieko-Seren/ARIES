#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ARIES - 系统配置模块
定义系统设置和配置加载逻辑
"""

import os
import json
from typing import Dict, List, Any, Optional
from pydantic import BaseSettings, Field
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Settings(BaseSettings):
    """ARIES系统配置类"""
    
    # 基本配置
    app_name: str = "ARIES"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    log_dir: str = Field(default="./logs", env="LOG_DIR")
    
    # API配置
    api_prefix: str = "/api"
    secret_key: str = Field(default="", env="SECRET_KEY")
    access_token_expire_minutes: int = 30
    
    # 数据库配置
    db_path: str = Field(default="./data/aries.db", env="DB_PATH")
    
    # LLM配置
    llm_provider: str = Field(default="openai", env="LLM_PROVIDER")
    llm_api_key: str = Field(default="", env="LLM_API_KEY")
    llm_model: str = Field(default="gpt-4", env="LLM_MODEL")
    llm_config: Dict[str, Any] = {}
    
    # 知识库配置
    vector_db_path: str = Field(default="./data/vector_store", env="VECTOR_DB_PATH")
    kg_path: str = Field(default="./data/knowledge_graph", env="KG_PATH")
    
    # 服务器配置
    servers_config_path: str = Field(default="./config/servers.json", env="SERVERS_CONFIG_PATH")
    
    # Kubernetes配置
    kube_config_path: str = Field(default="~/.kube/config", env="KUBE_CONFIG_PATH")
    
    # 通知配置
    webhook_url: str = Field(default="", env="WEBHOOK_URL")
    
    # 搜索API配置
    search_api_key: str = Field(default="", env="SEARCH_API_KEY")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._init_directories()
        self._load_llm_config()
    
    def _init_directories(self):
        """初始化必要的目录"""
        os.makedirs(self.log_dir, exist_ok=True)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        os.makedirs(os.path.dirname(self.vector_db_path), exist_ok=True)
        os.makedirs(os.path.dirname(self.kg_path), exist_ok=True)
        os.makedirs(os.path.dirname(self.servers_config_path), exist_ok=True)
    
    def _load_llm_config(self):
        """加载LLM配置"""
        self.llm_config = {
            "provider": self.llm_provider,
            "api_key": self.llm_api_key,
            "model": self.llm_model,
            "temperature": 0.1,
            "max_tokens": 2000
        }
        
        # 如果存在配置文件，从文件加载额外配置
        llm_config_path = os.path.join(os.path.dirname(self.servers_config_path), "llm_config.json")
        if os.path.exists(llm_config_path):
            try:
                with open(llm_config_path, 'r') as f:
                    file_config = json.load(f)
                    self.llm_config.update(file_config)
            except Exception as e:
                print(f"加载LLM配置文件失败: {str(e)}")

# 创建默认服务器配置文件模板
def create_default_servers_config(config_path: str):
    """创建默认的服务器配置文件模板
    
    Args:
        config_path: 配置文件路径
    """
    if os.path.exists(config_path):
        return
        
    default_config = [
        {
            "id": "server1",
            "name": "Web服务器",
            "ip": "192.168.1.100",
            "connection_type": "ssh",
            "username": "admin",
            "password": "",  # 生产环境应使用密钥认证
            "key_file": "~/.ssh/id_rsa",
            "expected_services": ["nginx", "mysql"],
            "description": "主要Web服务器"
        },
        {
            "id": "server2",
            "name": "数据库服务器",
            "ip": "192.168.1.101",
            "connection_type": "ssh",
            "username": "admin",
            "password": "",
            "key_file": "~/.ssh/id_rsa",
            "expected_services": ["postgresql", "redis"],
            "description": "主数据库服务器"
        },
        {
            "id": "switch1",
            "name": "核心交换机",
            "ip": "192.168.1.1",
            "connection_type": "telnet",
            "username": "admin",
            "password": "admin",
            "device_type": "network",
            "description": "核心交换机"
        },
        {
            "id": "cisco_ap_1",
            "name": "Cisco AP (Serial)",
            "ip": null, # 对于串口连接，IP可能不直接使用
            "connection_type": "cisco_serial",
            "port": "/dev/ttyUSB0", # 串口设备路径，例如 /dev/ttyUSB0 (Linux) 或 COM3 (Windows)
            "username": "admin",
            "password": "your_password",
            "device_type": "cisco_ios_serial", # Netmiko等库使用的设备类型
            "description": "通过RJ-45连接的Cisco AP"
        },
        {
            "id": "cisco_router_1",
            "name": "Cisco Router (Serial)",
            "ip": null,
            "connection_type": "cisco_serial",
            "port": "/dev/ttyUSB1",
            "username": "admin",
            "password": "your_password",
            "device_type": "cisco_ios_serial",
            "description": "通过RJ-45连接的Cisco路由器"
        }
    ]
    
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    
    with open(config_path, 'w') as f:
        json.dump(default_config, f, indent=2, ensure_ascii=False)
    
    print(f"已创建默认服务器配置文件: {config_path}")

# 创建默认LLM配置文件模板
def create_default_llm_config(config_path: str):
    """创建默认的LLM配置文件模板
    
    Args:
        config_path: 配置文件路径
    """
    if os.path.exists(config_path):
        return
        
    default_config = {
        "provider": "openai",
        "model": "gpt-4",
        "temperature": 0.1,
        "max_tokens": 2000,
        "top_p": 1,
        "frequency_penalty": 0,
        "presence_penalty": 0
    }
    
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    
    with open(config_path, 'w') as f:
        json.dump(default_config, f, indent=2, ensure_ascii=False)
    
    print(f"已创建默认LLM配置文件: {config_path}")

# 创建全局配置实例
settings = Settings()