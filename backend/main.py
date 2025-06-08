#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ARIES - AI Native 自动运维系统主程序
"""

import os
import logging
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import schedule
import time
import threading
from contextlib import asynccontextmanager
import requests

# 导入内部模块
from config.settings import Settings
from core.agent import Agent
from core.auth.router import router as auth_router
from core.auth.init_db import init_db
from core.database import SessionLocal
from api.routes import router as api_router, devices
from core.mqtt.manager import MQTTManager
from core.mqtt.storage import DeviceDataStorage

# 加载配置
settings = Settings()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 全局状态
mqtt_manager = None
device_storage = None
scheduler_thread = None
stop_scheduler = threading.Event()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global mqtt_manager, device_storage
    
    try:
        # 初始化 MQTT 管理器
        mqtt_manager = MQTTManager(
            broker=os.getenv("MQTT_BROKER", "mqtt"),
            port=int(os.getenv("MQTT_PORT", "1883")),
            username=os.getenv("MQTT_USERNAME"),
            password=os.getenv("MQTT_PASSWORD")
        )
        await mqtt_manager.connect()
        
        # 初始化数据存储
        device_storage = DeviceDataStorage(
            dsn=os.getenv("TIMESCALE_URL", "postgresql://aries:aries@timescaledb:5432/aries_tsdb")
        )
        await device_storage.connect()
        
        # 注册设备数据处理器
        async def device_data_handler(device_id: str, data: dict):
            try:
                await device_storage.store_device_data(device_id, data)
            except Exception as e:
                logger.error(f"存储设备数据失败: {str(e)}")
        
        # 注册设备状态处理器
        async def device_status_handler(device_id: str, status: dict):
            try:
                await device_storage.store_device_status(device_id, status)
            except Exception as e:
                logger.error(f"存储设备状态失败: {str(e)}")
        
        # 为所有设备注册处理器
        mqtt_manager.register_device_handler("+", device_data_handler)
        
    except Exception as e:
        logger.error(f"初始化服务失败: {str(e)}")
        raise
    
    yield
    
    # 清理资源
    try:
        if mqtt_manager:
            await mqtt_manager.disconnect()
        if device_storage:
            await device_storage.close()
        if scheduler_thread and scheduler_thread.is_alive():
            stop_scheduler.set()
            scheduler_thread.join(timeout=5)
    except Exception as e:
        logger.error(f"清理资源失败: {str(e)}")

# 创建FastAPI应用
app = FastAPI(
    title="ARIES API",
    description="AI Native 自动运维系统API",
    version="1.0.0",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
)

# 包含API路由
app.include_router(auth_router)  # 添加认证和授权路由
app.include_router(api_router)
app.include_router(devices.router)

# 创建Agent实例
agent = Agent(settings)

# 监控任务
def monitoring_task():
    """定时监控任务，每分钟执行一次"""
    try:
        logger.info(f"执行监控任务...")
        agent.monitor()
    except Exception as e:
        logger.error(f"监控任务执行失败: {str(e)}")
        # 发送告警通知
        if settings.webhook_url:
            try:
                requests.post(settings.webhook_url, json={
                    "level": "error",
                    "message": f"监控任务执行失败: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as notify_error:
                logger.error(f"发送告警通知失败: {str(notify_error)}")

# 启动定时任务
def start_scheduler():
    while not stop_scheduler.is_set():
        try:
            schedule.run_pending()
            time.sleep(1)
        except Exception as e:
            logger.error(f"调度器运行错误: {str(e)}")
            time.sleep(5)  # 发生错误时等待一段时间再继续

@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    try:
        # 初始化数据库
        db = SessionLocal()
        try:
            init_db(db)
        finally:
            db.close()
        
        # 启动定时任务线程
        global scheduler_thread
        scheduler_thread = threading.Thread(target=start_scheduler, daemon=True)
        scheduler_thread.start()
        logger.info("ARIES 自动运维系统已启动")
    except Exception as e:
        logger.error(f"系统启动失败: {str(e)}")
        raise

# 依赖注入函数
async def get_mqtt_manager() -> MQTTManager:
    return mqtt_manager

async def get_storage() -> DeviceDataStorage:
    return device_storage

# 覆盖路由中的依赖注入函数
devices.get_mqtt_manager = get_mqtt_manager
devices.get_storage = get_storage

@app.get("/health")
async def health_check():
    """健康检查接口"""
    try:
        mqtt_status = mqtt_manager.connected if mqtt_manager else False
        storage_status = device_storage.pool is not None if device_storage else False
        scheduler_status = scheduler_thread.is_alive() if scheduler_thread else False
        
        status = "healthy" if all([mqtt_status, storage_status, scheduler_status]) else "degraded"
        
        return {
            "status": status,
            "mqtt_connected": mqtt_status,
            "storage_connected": storage_status,
            "scheduler_running": scheduler_status,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/")
async def root():
    """API根路径"""
    return {"message": "欢迎使用ARIES自动运维系统API"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)