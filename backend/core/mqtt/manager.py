import asyncio
import json
import logging
from typing import Dict, Any, Callable, Optional
from asyncio_mqtt import Client, MqttError
from datetime import datetime

logger = logging.getLogger(__name__)

class MQTTManager:
    def __init__(self, broker: str, port: int, client_id: str = "aries-mqtt-manager"):
        self.broker = broker
        self.port = port
        self.client_id = client_id
        self.client: Optional[Client] = None
        self.connected = False
        self.devices: Dict[str, Dict[str, Any]] = {}
        self.message_handlers: Dict[str, Callable] = {}
        self._reconnect_delay = 1
        self._max_reconnect_delay = 60

    async def connect(self):
        """连接到 MQTT Broker"""
        try:
            self.client = Client(
                hostname=self.broker,
                port=self.port,
                client_id=self.client_id,
                keepalive=60
            )
            await self.client.connect()
            self.connected = True
            self._reconnect_delay = 1
            logger.info(f"已连接到 MQTT Broker: {self.broker}:{self.port}")
            
            # 订阅设备发现主题
            await self.client.subscribe("devices/+/discovery")
            # 订阅设备状态主题
            await self.client.subscribe("devices/+/status")
            # 订阅设备数据主题
            await self.client.subscribe("devices/+/data")
            
            # 启动消息处理循环
            asyncio.create_task(self._message_loop())
            
        except MqttError as e:
            logger.error(f"MQTT 连接失败: {e}")
            self.connected = False
            await self._handle_reconnect()

    async def _handle_reconnect(self):
        """处理重连逻辑"""
        while not self.connected:
            try:
                logger.info(f"尝试重新连接 MQTT Broker，延迟 {self._reconnect_delay} 秒")
                await asyncio.sleep(self._reconnect_delay)
                await self.connect()
            except Exception as e:
                logger.error(f"重连失败: {e}")
                self._reconnect_delay = min(self._reconnect_delay * 2, self._max_reconnect_delay)

    async def _message_loop(self):
        """消息处理循环"""
        try:
            async with self.client.messages() as messages:
                async for message in messages:
                    await self._handle_message(message)
        except Exception as e:
            logger.error(f"消息处理循环异常: {e}")
            self.connected = False
            await self._handle_reconnect()

    async def _handle_message(self, message):
        """处理接收到的消息"""
        try:
            topic = message.topic.value
            payload = json.loads(message.payload.decode())
            
            # 解析设备 ID
            device_id = topic.split('/')[1]
            
            if topic.endswith('/discovery'):
                await self._handle_device_discovery(device_id, payload)
            elif topic.endswith('/status'):
                await self._handle_device_status(device_id, payload)
            elif topic.endswith('/data'):
                await self._handle_device_data(device_id, payload)
                
        except json.JSONDecodeError:
            logger.error(f"无效的 JSON 消息: {message.payload}")
        except Exception as e:
            logger.error(f"消息处理异常: {e}")

    async def _handle_device_discovery(self, device_id: str, payload: Dict[str, Any]):
        """处理设备发现消息"""
        if device_id not in self.devices:
            self.devices[device_id] = {
                'id': device_id,
                'type': payload.get('type'),
                'name': payload.get('name'),
                'capabilities': payload.get('capabilities', []),
                'last_seen': datetime.now().isoformat(),
                'status': 'online'
            }
            logger.info(f"发现新设备: {device_id}")
            # 发送设备注册确认
            await self.publish(f"devices/{device_id}/register", {'status': 'registered'})

    async def _handle_device_status(self, device_id: str, payload: Dict[str, Any]):
        """处理设备状态更新"""
        if device_id in self.devices:
            self.devices[device_id].update({
                'status': payload.get('status', 'unknown'),
                'last_seen': datetime.now().isoformat(),
                'battery': payload.get('battery'),
                'signal_strength': payload.get('signal_strength')
            })
            logger.info(f"设备状态更新: {device_id} - {payload.get('status')}")

    async def _handle_device_data(self, device_id: str, payload: Dict[str, Any]):
        """处理设备数据"""
        if device_id in self.devices:
            # 更新设备数据
            self.devices[device_id]['last_data'] = payload
            self.devices[device_id]['last_seen'] = datetime.now().isoformat()
            
            # 调用注册的数据处理器
            if device_id in self.message_handlers:
                try:
                    await self.message_handlers[device_id](device_id, payload)
                except Exception as e:
                    logger.error(f"设备数据处理异常: {e}")

    async def publish(self, topic: str, payload: Dict[str, Any], qos: int = 1):
        """发布消息到指定主题"""
        if not self.connected:
            raise ConnectionError("MQTT 客户端未连接")
        try:
            await self.client.publish(
                topic,
                payload=json.dumps(payload).encode(),
                qos=qos
            )
        except Exception as e:
            logger.error(f"消息发布失败: {e}")
            raise

    async def register_device_handler(self, device_id: str, handler: Callable):
        """注册设备数据处理器"""
        self.message_handlers[device_id] = handler

    async def unregister_device_handler(self, device_id: str):
        """注销设备数据处理器"""
        if device_id in self.message_handlers:
            del self.message_handlers[device_id]

    async def get_device_info(self, device_id: str) -> Optional[Dict[str, Any]]:
        """获取设备信息"""
        return self.devices.get(device_id)

    async def get_all_devices(self) -> Dict[str, Dict[str, Any]]:
        """获取所有设备信息"""
        return self.devices

    async def disconnect(self):
        """断开 MQTT 连接"""
        if self.client and self.connected:
            await self.client.disconnect()
            self.connected = False
            logger.info("已断开 MQTT 连接") 