from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
from datetime import datetime
from pydantic import BaseModel

from core.mqtt.manager import MQTTManager
from core.mqtt.storage import DeviceDataStorage

router = APIRouter(prefix="/devices", tags=["devices"])

# 数据模型
class DeviceInfo(BaseModel):
    id: str
    type: str
    name: str
    capabilities: List[str]
    status: str
    last_seen: datetime
    battery: float = None
    signal_strength: int = None

class DeviceCommand(BaseModel):
    command: str
    parameters: Dict[str, Any] = {}

class DeviceDataQuery(BaseModel):
    start_time: datetime = None
    end_time: datetime = None
    limit: int = 1000

# 依赖注入
async def get_mqtt_manager() -> MQTTManager:
    # 这里应该从应用状态获取 MQTT 管理器实例
    # 实际实现时需要通过依赖注入系统获取
    raise NotImplementedError()

async def get_storage() -> DeviceDataStorage:
    # 这里应该从应用状态获取存储实例
    # 实际实现时需要通过依赖注入系统获取
    raise NotImplementedError()

@router.get("/", response_model=List[DeviceInfo])
async def list_devices(mqtt_manager: MQTTManager = Depends(get_mqtt_manager)):
    """获取所有设备列表"""
    devices = await mqtt_manager.get_all_devices()
    return [DeviceInfo(**device) for device in devices.values()]

@router.get("/{device_id}", response_model=DeviceInfo)
async def get_device(device_id: str, mqtt_manager: MQTTManager = Depends(get_mqtt_manager)):
    """获取指定设备信息"""
    device = await mqtt_manager.get_device_info(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="设备未找到")
    return DeviceInfo(**device)

@router.post("/{device_id}/command")
async def send_command(
    device_id: str,
    command: DeviceCommand,
    mqtt_manager: MQTTManager = Depends(get_mqtt_manager)
):
    """向设备发送命令"""
    device = await mqtt_manager.get_device_info(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="设备未找到")
    
    try:
        await mqtt_manager.publish(
            f"devices/{device_id}/command",
            {
                "command": command.command,
                "parameters": command.parameters,
                "timestamp": datetime.now().isoformat()
            }
        )
        return {"status": "command_sent"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{device_id}/data")
async def get_device_data(
    device_id: str,
    query: DeviceDataQuery = Depends(),
    storage: DeviceDataStorage = Depends(get_storage)
):
    """获取设备历史数据"""
    try:
        data = await storage.get_device_history(
            device_id,
            query.start_time,
            query.end_time,
            query.limit
        )
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{device_id}/status/history")
async def get_device_status_history(
    device_id: str,
    query: DeviceDataQuery = Depends(),
    storage: DeviceDataStorage = Depends(get_storage)
):
    """获取设备状态历史"""
    try:
        history = await storage.get_device_status_history(
            device_id,
            query.start_time,
            query.end_time,
            query.limit
        )
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{device_id}")
async def remove_device(
    device_id: str,
    mqtt_manager: MQTTManager = Depends(get_mqtt_manager)
):
    """移除设备"""
    device = await mqtt_manager.get_device_info(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="设备未找到")
    
    try:
        # 发送设备移除命令
        await mqtt_manager.publish(
            f"devices/{device_id}/remove",
            {"timestamp": datetime.now().isoformat()}
        )
        # 注销设备处理器
        await mqtt_manager.unregister_device_handler(device_id)
        return {"status": "device_removed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 