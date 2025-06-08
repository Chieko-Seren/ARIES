import logging
from typing import Dict, Any, List
from datetime import datetime
import asyncpg
from asyncpg.pool import Pool

logger = logging.getLogger(__name__)

class DeviceDataStorage:
    def __init__(self, dsn: str):
        self.dsn = dsn
        self.pool: Optional[Pool] = None

    async def connect(self):
        """连接到数据库并初始化表结构"""
        try:
            self.pool = await asyncpg.create_pool(self.dsn)
            async with self.pool.acquire() as conn:
                # 创建设备表
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS devices (
                        id TEXT PRIMARY KEY,
                        type TEXT NOT NULL,
                        name TEXT,
                        capabilities JSONB,
                        created_at TIMESTAMPTZ DEFAULT NOW(),
                        updated_at TIMESTAMPTZ DEFAULT NOW()
                    )
                ''')
                
                # 创建设备状态历史表
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS device_status_history (
                        device_id TEXT REFERENCES devices(id),
                        status TEXT NOT NULL,
                        battery FLOAT,
                        signal_strength INTEGER,
                        timestamp TIMESTAMPTZ DEFAULT NOW()
                    )
                ''')
                
                # 创建设备数据表（使用 TimescaleDB 的超表功能）
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS device_data (
                        device_id TEXT REFERENCES devices(id),
                        timestamp TIMESTAMPTZ DEFAULT NOW(),
                        data JSONB NOT NULL
                    )
                ''')
                
                # 将设备数据表转换为超表
                await conn.execute('''
                    SELECT create_hypertable('device_data', 'timestamp', 
                        if_not_exists => TRUE,
                        migrate_data => TRUE
                    )
                ''')
                
                logger.info("数据库表结构初始化完成")
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            raise

    async def store_device(self, device_data: Dict[str, Any]):
        """存储或更新设备信息"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO devices (id, type, name, capabilities, updated_at)
                VALUES ($1, $2, $3, $4, NOW())
                ON CONFLICT (id) DO UPDATE
                SET type = $2,
                    name = $3,
                    capabilities = $4,
                    updated_at = NOW()
            ''', device_data['id'], device_data['type'], 
                device_data.get('name'), device_data.get('capabilities', []))

    async def store_device_status(self, device_id: str, status_data: Dict[str, Any]):
        """存储设备状态更新"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO device_status_history 
                (device_id, status, battery, signal_strength, timestamp)
                VALUES ($1, $2, $3, $4, NOW())
            ''', device_id, status_data.get('status'), 
                status_data.get('battery'), status_data.get('signal_strength'))

    async def store_device_data(self, device_id: str, data: Dict[str, Any]):
        """存储设备数据"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO device_data (device_id, data, timestamp)
                VALUES ($1, $2, NOW())
            ''', device_id, data)

    async def get_device_history(self, device_id: str, 
                               start_time: datetime = None,
                               end_time: datetime = None,
                               limit: int = 1000) -> List[Dict[str, Any]]:
        """获取设备历史数据"""
        async with self.pool.acquire() as conn:
            query = '''
                SELECT timestamp, data
                FROM device_data
                WHERE device_id = $1
            '''
            params = [device_id]
            
            if start_time:
                query += " AND timestamp >= $" + str(len(params) + 1)
                params.append(start_time)
            if end_time:
                query += " AND timestamp <= $" + str(len(params) + 1)
                params.append(end_time)
                
            query += " ORDER BY timestamp DESC LIMIT $" + str(len(params) + 1)
            params.append(limit)
            
            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]

    async def get_device_status_history(self, device_id: str,
                                      start_time: datetime = None,
                                      end_time: datetime = None,
                                      limit: int = 1000) -> List[Dict[str, Any]]:
        """获取设备状态历史"""
        async with self.pool.acquire() as conn:
            query = '''
                SELECT timestamp, status, battery, signal_strength
                FROM device_status_history
                WHERE device_id = $1
            '''
            params = [device_id]
            
            if start_time:
                query += " AND timestamp >= $" + str(len(params) + 1)
                params.append(start_time)
            if end_time:
                query += " AND timestamp <= $" + str(len(params) + 1)
                params.append(end_time)
                
            query += " ORDER BY timestamp DESC LIMIT $" + str(len(params) + 1)
            params.append(limit)
            
            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]

    async def close(self):
        """关闭数据库连接池"""
        if self.pool:
            await self.pool.close()
            logger.info("数据库连接池已关闭") 