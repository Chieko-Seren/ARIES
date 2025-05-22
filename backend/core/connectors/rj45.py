#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ARIES - RJ45连接器
实现串口通信功能，用于直接连接网络设备
"""

import serial
import time
import logging
from typing import Optional, Dict, Any, List

class RJ45Connector:
    """RJ45连接器类，用于串口通信"""
    
    def __init__(self, device_path: str, baud_rate: int = 9600, timeout: int = 5):
        """初始化RJ45连接器
        
        Args:
            device_path: 设备路径，如'/dev/ttyUSB0'
            baud_rate: 波特率，默认9600
            timeout: 超时时间，默认5秒
        """
        self.device_path = device_path
        self.baud_rate = baud_rate
        self.timeout = timeout
        self.serial = None
        self.logger = logging.getLogger("aries_rj45")
    
    def connect(self):
        """建立串口连接"""
        try:
            self.serial = serial.Serial(
                port=self.device_path,
                baudrate=self.baud_rate,
                timeout=self.timeout
            )
            
            self.logger.info(f"已连接到设备 {self.device_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"串口连接失败: {str(e)}")
            raise
    
    def disconnect(self):
        """关闭串口连接"""
        if self.serial and self.serial.is_open:
            self.serial.close()
            self.serial = None
            self.logger.info(f"已断开与设备 {self.device_path} 的连接")
    
    def execute(self, command: str) -> str:
        """执行串口命令
        
        Args:
            command: 要执行的命令
            
        Returns:
            命令执行结果
        """
        if not self.serial or not self.serial.is_open:
            raise RuntimeError("未连接到串口设备")
        
        try:
            self.logger.info(f"向设备 {self.device_path} 发送命令: {command}")
            
            # 清空输入缓冲区
            self.serial.reset_input_buffer()
            
            # 发送命令，确保以换行符结尾
            if not command.endswith('\n'):
                command += '\n'
            self.serial.write(command.encode('utf-8'))
            
            # 等待响应
            time.sleep(1)  # 给设备一些响应时间
            
            # 读取响应
            response = ""
            while self.serial.in_waiting > 0:
                line = self.serial.readline().decode('utf-8', errors='ignore')
                response += line
            
            return response
            
        except Exception as e:
            self.logger.error(f"命令执行失败: {str(e)}")
            raise
    
    def read_until(self, terminator: str = '>', timeout: int = None) -> str:
        """读取直到遇到特定终止符
        
        Args:
            terminator: 终止符，默认为'>'
            timeout: 超时时间，默认使用初始化时设置的值
            
        Returns:
            读取的数据
        """
        if not self.serial or not self.serial.is_open:
            raise RuntimeError("未连接到串口设备")
        
        try:
            # 设置超时
            old_timeout = self.serial.timeout
            if timeout is not None:
                self.serial.timeout = timeout
            
            # 读取数据直到终止符
            data = self.serial.read_until(terminator.encode('utf-8')).decode('utf-8', errors='ignore')
            
            # 恢复原超时设置
            if timeout is not None:
                self.serial.timeout = old_timeout
            
            return data
            
        except Exception as e:
            self.logger.error(f"读取数据失败: {str(e)}")
            raise