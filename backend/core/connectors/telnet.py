#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ARIES - Telnet连接器
实现Telnet远程连接和命令执行功能
"""

import telnetlib3
import asyncio
import logging
from typing import Optional, Dict, Any, List

class TelnetConnector:
    """Telnet连接器类，用于Telnet远程连接和命令执行"""
    
    def __init__(self, host: str, port: int = 23, username: str = None, password: str = None):
        """初始化Telnet连接器
        
        Args:
            host: 主机地址
            port: Telnet端口，默认23
            username: 用户名
            password: 密码
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.reader = None
        self.writer = None
        self.logger = logging.getLogger("aries_telnet")
    
    def connect(self):
        """建立Telnet连接"""
        try:
            # 使用同步方式包装异步连接
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            connect_task = loop.create_task(self._connect_async())
            loop.run_until_complete(connect_task)
            
            self.logger.info(f"已连接到 {self.host}")
            return True
            
        except Exception as e:
            self.logger.error(f"Telnet连接失败: {str(e)}")
            raise
    
    async def _connect_async(self):
        """异步建立Telnet连接"""
        self.reader, self.writer = await telnetlib3.open_connection(
            self.host, self.port
        )
        
        # 处理登录
        if self.username:
            # 等待用户名提示
            output = await self.reader.read(1024)
            if 'login' in output.lower() or 'username' in output.lower():
                self.writer.write(f"{self.username}\n")
                await self.writer.drain()
            
            # 等待密码提示
            output = await self.reader.read(1024)
            if 'password' in output.lower():
                self.writer.write(f"{self.password}\n")
                await self.writer.drain()
                
            # 等待登录完成
            output = await self.reader.read(1024)
            if 'failed' in output.lower() or 'incorrect' in output.lower():
                raise Exception("Telnet登录失败，用户名或密码错误")
    
    def disconnect(self):
        """关闭Telnet连接"""
        if self.writer:
            # 使用同步方式包装异步断开连接
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            disconnect_task = loop.create_task(self._disconnect_async())
            loop.run_until_complete(disconnect_task)
            
            self.reader = None
            self.writer = None
            self.logger.info(f"已断开与 {self.host} 的连接")
    
    async def _disconnect_async(self):
        """异步关闭Telnet连接"""
        self.writer.close()
        await self.writer.wait_closed()
    
    def execute(self, command: str) -> str:
        """执行Telnet命令
        
        Args:
            command: 要执行的命令
            
        Returns:
            命令执行结果
        """
        if not self.writer or not self.reader:
            raise RuntimeError("未连接到Telnet服务器")
        
        try:
            self.logger.info(f"在 {self.host} 上执行命令: {command}")
            
            # 使用同步方式包装异步命令执行
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            execute_task = loop.create_task(self._execute_async(command))
            result = loop.run_until_complete(execute_task)
            
            return result
            
        except Exception as e:
            self.logger.error(f"命令执行失败: {str(e)}")
            raise
    
    async def _execute_async(self, command: str) -> str:
        """异步执行Telnet命令"""
        # 发送命令
        self.writer.write(f"{command}\n")
        await self.writer.drain()
        
        # 等待命令执行完成并获取结果
        # 这里简化处理，实际应用中可能需要更复杂的输出解析
        await asyncio.sleep(1)  # 等待命令执行
        output = await self.reader.read(4096)
        
        # 移除命令本身和提示符
        lines = output.split('\n')
        if len(lines) > 1:
            # 移除第一行（命令本身）和最后一行（提示符）
            result = '\n'.join(lines[1:-1])
        else:
            result = output
        
        return result