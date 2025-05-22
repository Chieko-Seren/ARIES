#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ARIES - SSH连接器
实现SSH远程连接和命令执行功能
"""

import os
import paramiko
import logging
from typing import Optional, Dict, Any, List

class SSHConnector:
    """SSH连接器类，用于SSH远程连接和命令执行"""
    
    def __init__(self, host: str, port: int = 22, username: str = None, 
                 password: str = None, key_file: str = None):
        """初始化SSH连接器
        
        Args:
            host: 主机地址
            port: SSH端口，默认22
            username: 用户名
            password: 密码，与key_file至少提供一个
            key_file: 密钥文件路径
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.key_file = key_file
        self.client = None
        self.logger = logging.getLogger("aries_ssh")
    
    def connect(self):
        """建立SSH连接"""
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # 处理密钥文件路径
            if self.key_file and self.key_file.startswith("~"):
                self.key_file = os.path.expanduser(self.key_file)
            
            # 使用密钥文件或密码连接
            if self.key_file and os.path.exists(self.key_file):
                self.client.connect(
                    hostname=self.host,
                    port=self.port,
                    username=self.username,
                    key_filename=self.key_file
                )
                self.logger.info(f"使用密钥文件连接到 {self.host}")
            else:
                self.client.connect(
                    hostname=self.host,
                    port=self.port,
                    username=self.username,
                    password=self.password
                )
                self.logger.info(f"使用密码连接到 {self.host}")
                
            return True
            
        except Exception as e:
            self.logger.error(f"SSH连接失败: {str(e)}")
            raise
    
    def disconnect(self):
        """关闭SSH连接"""
        if self.client:
            self.client.close()
            self.client = None
            self.logger.info(f"已断开与 {self.host} 的连接")
    
    def execute(self, command: str) -> str:
        """执行SSH命令
        
        Args:
            command: 要执行的命令
            
        Returns:
            命令执行结果
        """
        if not self.client:
            raise RuntimeError("未连接到SSH服务器")
        
        try:
            self.logger.info(f"在 {self.host} 上执行命令: {command}")
            stdin, stdout, stderr = self.client.exec_command(command)
            
            # 获取命令输出
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            
            if error:
                self.logger.warning(f"命令执行产生错误: {error}")
            
            return output if output else error
            
        except Exception as e:
            self.logger.error(f"命令执行失败: {str(e)}")
            raise
    
    def upload_file(self, local_path: str, remote_path: str):
        """上传文件到远程服务器
        
        Args:
            local_path: 本地文件路径
            remote_path: 远程文件路径
        """
        if not self.client:
            raise RuntimeError("未连接到SSH服务器")
        
        try:
            sftp = self.client.open_sftp()
            sftp.put(local_path, remote_path)
            sftp.close()
            self.logger.info(f"文件上传成功: {local_path} -> {remote_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"文件上传失败: {str(e)}")
            raise
    
    def download_file(self, remote_path: str, local_path: str):
        """从远程服务器下载文件
        
        Args:
            remote_path: 远程文件路径
            local_path: 本地文件路径
        """
        if not self.client:
            raise RuntimeError("未连接到SSH服务器")
        
        try:
            sftp = self.client.open_sftp()
            sftp.get(remote_path, local_path)
            sftp.close()
            self.logger.info(f"文件下载成功: {remote_path} -> {local_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"文件下载失败: {str(e)}")
            raise