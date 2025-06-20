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
import logging
from core.vault.manager import VaultManager
import asyncio
from functools import wraps

logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

def async_init(func):
    """异步初始化装饰器"""
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        return await func(self, *args, **kwargs)
    return wrapper

class Settings(BaseSettings):
    """ARIES系统配置类"""
    
    # Vault配置
    vault_url: str = Field(..., env="VAULT_URL")
    vault_token: str = Field(..., env="VAULT_TOKEN")
    vault_mount_point: str = Field(default="aries", env="VAULT_MOUNT_POINT")
    
    # 基本配置
    app_name: str = "ARIES"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    log_dir: str = Field(default="./logs", env="LOG_DIR")
    
    # API配置
    api_prefix: str = "/api"
    secret_key: str = Field(default="", env="SECRET_KEY")  # 将从Vault获取
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # 数据库配置
    db_path: str = Field(default="./data/aries.db", env="DB_PATH")
    timescale_url: str = Field(default="", env="TIMESCALE_URL")  # 将从Vault获取
    
    # LLM配置
    llm_provider: str = Field(default="openai", env="LLM_PROVIDER")
    llm_api_key: str = Field(default="", env="LLM_API_KEY")  # 将从Vault获取
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
    
    # MQTT配置
    mqtt_broker: str = Field(default="mqtt", env="MQTT_BROKER")
    mqtt_port: int = Field(default=1883, env="MQTT_PORT")
    mqtt_username: str = Field(default="", env="MQTT_USERNAME")  # 将从Vault获取
    mqtt_password: str = Field(default="", env="MQTT_PASSWORD")  # 将从Vault获取
    
    # CORS配置
    allowed_origins: List[str] = Field(default=["http://localhost:3000"], env="ALLOWED_ORIGINS")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._init_directories()
        # 同步初始化Vault
        asyncio.run(self._init_vault())
        self._load_llm_config()
    
    def _init_directories(self):
        """初始化必要的目录"""
        os.makedirs(self.log_dir, exist_ok=True)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        os.makedirs(os.path.dirname(self.vector_db_path), exist_ok=True)
        os.makedirs(os.path.dirname(self.kg_path), exist_ok=True)
        os.makedirs(os.path.dirname(self.servers_config_path), exist_ok=True)
    
    @async_init
    async def _init_vault(self):
        """初始化Vault并加载敏感配置"""
        try:
            vault = VaultManager(
                url=self.vault_url,
                token=self.vault_token,
                mount_point=self.vault_mount_point
            )
            
            # 加载敏感配置
            secrets = {
                "api": await vault.get_secret("api"),
                "database": await vault.get_secret("database"),
                "llm": await vault.get_secret("llm"),
                "mqtt": await vault.get_secret("mqtt")
            }
            
            # 更新配置
            if secrets["api"]:
                self.secret_key = secrets["api"].get("secret_key", self.secret_key)
            
            if secrets["database"]:
                self.timescale_url = secrets["database"].get("url", self.timescale_url)
            
            if secrets["llm"]:
                self.llm_api_key = secrets["llm"].get("api_key", self.llm_api_key)
                self.llm_config.update(secrets["llm"])
            
            if secrets["mqtt"]:
                self.mqtt_username = secrets["mqtt"].get("username", self.mqtt_username)
                self.mqtt_password = secrets["mqtt"].get("password", self.mqtt_password)
            
            # 验证必需配置
            self._validate_required_configs()
            
        except Exception as e:
            logger.error(f"初始化Vault失败: {str(e)}")
            raise
    
    def _validate_required_configs(self):
        """验证必需配置是否存在"""
        required_configs = {
            "secret_key": self.secret_key,
            "timescale_url": self.timescale_url,
            "llm_api_key": self.llm_api_key
        }
        
        missing_configs = [k for k, v in required_configs.items() if not v]
        if missing_configs:
            raise ValueError(f"缺少必需配置: {', '.join(missing_configs)}")
    
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
            "password": None,  # 生产环境应使用密钥认证
            "key_file": "~/.ssh/id_rsa",
            "expected_services": ["nginx", "mysql"],
            "description": "主要Web服务器",
            "tags": ["web", "production"]
        },
        {
            "id": "server2",
            "name": "数据库服务器",
            "ip": "192.168.1.101",
            "connection_type": "ssh",
            "username": "admin",
            "password": None,
            "key_file": "~/.ssh/id_rsa",
            "expected_services": ["postgresql", "redis"],
            "description": "主数据库服务器",
            "tags": ["database", "production"]
        },
        {
            "id": "switch1",
            "name": "核心交换机",
            "ip": "192.168.1.1",
            "connection_type": "telnet",
            "username": "admin",
            "password": None,  # 生产环境应使用更安全的认证方式
            "device_type": "network",
            "description": "核心交换机",
            "tags": ["network", "core"]
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
    
    logger.info(f"已创建默认服务器配置文件: {config_path}")
    logger.warning("请确保在生产环境中修改默认配置，特别是密码和认证信息！")

# 创建默认LLM配置文件模板
def create_default_llm_config(config_path: str):
    """创建默认的LLM配置文件模板
    
    Args:
        config_path: 配置文件路径
    """
    if os.path.exists(config_path):
        return
        
    default_config = {
        # 基础配置
        "api_key": "",  # OpenAI API密钥
        
        # RWKV配置
        "rwkv_model_path": "",  # RWKV模型路径
        "context_length": 2048,  # 上下文窗口大小
        "batch_size": 512,  # 批处理大小
        "threads": 4,  # CPU线程数
        "gpu_layers": 0,  # 使用GPU的层数
        
        # 通用生成参数
        "temperature": 0.1,
        "max_tokens": 2000,
        "top_p": 1,
        "frequency_penalty": 0,
        "presence_penalty": 0,
        
        # 任务分类阈值
        "long_text_threshold": 1000,  # 长文本阈值（字符数）
        
        # 模型特定配置
        "models": {
            "gpt4": {
                "model": "gpt-4",
                "max_tokens": 2000,
                "temperature": 0.1
            },
            "gpt4-mini": {
                "model": "gpt-4-mini",
                "max_tokens": 1000,
                "temperature": 0.1
            },
            "rwkv": {
                "model_path": "",  # 将在运行时设置
                "context_length": 2048,
                "batch_size": 512,
                "threads": 4,
                "gpu_layers": 0
            }
        },
        
        # 分类器配置
        "classifier": {
            # 文本向量化配置
            "vectorizer": {
                "model_path": "",  # RWKV-7模型路径
                "context_length": 2048,
                "batch_size": 512,
                "threads": 4,
                "gpu_layers": 0
            },
            
            # 贝叶斯分类器配置
            "bayes": {
                "min_samples": 5,  # 每个类别最小样本数
                "confidence_threshold": 0.7,  # 分类置信度阈值
                "update_threshold": 0.8  # 更新训练数据阈值
            },
            
            # 任务分类阈值
            "thresholds": {
                "long_text": 1000,  # 长文本阈值（字符数）
                "high_reasoning_keywords": [
                    "分析", "推理", "解释", "为什么", "如何", "原因", "影响",
                    "比较", "评估", "预测", "建议", "策略", "方案", "决策",
                    "analyze", "reason", "explain", "why", "how", "cause",
                    "compare", "evaluate", "predict", "suggest", "strategy"
                ]
            }
        }
    }
    
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    
    with open(config_path, 'w') as f:
        json.dump(default_config, f, indent=2, ensure_ascii=False)
    
    print(f"已创建默认LLM配置文件: {config_path}")

# 创建全局配置实例
settings = Settings()