#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ARIES - Shell连接器
实现本地Shell命令执行功能
"""

import subprocess
import logging
from typing import Optional, Dict, Any, List

class ShellConnector:
    """Shell连接器类，用于执行本地Shell命令"""
    
    def __init__(self):
        """初始化Shell连接器"""
        self.logger = logging.getLogger("aries_shell")
    
    def connect(self):
        """Shell连接器不需要连接操作，但保留此方法以统一接口"""
        return True
    
    def disconnect(self):
        """Shell连接器不需要断开连接操作，但保留此方法以统一接口"""
        pass
    
    def execute(self, command: str) -> str:
        """执行Shell命令
        
        Args:
            command: 要执行的命令
            
        Returns:
            命令执行结果
        """
        try:
            self.logger.info(f"执行Shell命令: {command}")
            
            # 执行命令并获取输出
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            stdout, stderr = process.communicate()
            exit_code = process.returncode
            
            if exit_code != 0:
                self.logger.warning(f"命令执行返回非零状态码: {exit_code}, 错误: {stderr}")
                return stderr if stderr else f"命令执行失败，状态码: {exit_code}"
            
            return stdout
            
        except Exception as e:
            self.logger.error(f"命令执行失败: {str(e)}")
            raise