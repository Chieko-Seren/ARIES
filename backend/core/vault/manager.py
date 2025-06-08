#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ARIES - Vault 管理器
用于安全地管理敏感配置信息
"""

import os
import logging
import hvac
from typing import Optional, Dict, Any
from hvac.exceptions import VaultError

logger = logging.getLogger(__name__)

class VaultManager:
    """Vault管理器类"""
    
    def __init__(self, url: str, token: str, mount_point: str = "aries"):
        """初始化Vault管理器
        
        Args:
            url: Vault服务器URL
            token: Vault访问令牌
            mount_point: 密钥引擎挂载点
        """
        self.client = hvac.Client(url=url, token=token)
        self.mount_point = mount_point
        self._ensure_mount()
    
    def _ensure_mount(self):
        """确保密钥引擎已挂载"""
        try:
            if not self.client.sys.is_mounted(self.mount_point):
                self.client.sys.enable_secrets_engine(
                    backend_type='kv',
                    path=self.mount_point,
                    options={'version': 2}
                )
                logger.info(f"已挂载密钥引擎到 {self.mount_point}")
        except VaultError as e:
            logger.error(f"挂载密钥引擎失败: {str(e)}")
            raise
    
    async def get_secret(self, path: str) -> Optional[Dict[str, Any]]:
        """获取密钥
        
        Args:
            path: 密钥路径
            
        Returns:
            密钥值字典，如果不存在则返回None
        """
        try:
            response = self.client.secrets.kv.v2.read_secret_version(
                path=path,
                mount_point=self.mount_point
            )
            return response['data']['data']
        except VaultError as e:
            logger.error(f"获取密钥失败 {path}: {str(e)}")
            return None
    
    async def set_secret(self, path: str, data: Dict[str, Any]) -> bool:
        """设置密钥
        
        Args:
            path: 密钥路径
            data: 密钥数据
            
        Returns:
            是否成功
        """
        try:
            self.client.secrets.kv.v2.create_or_update_secret(
                path=path,
                secret=data,
                mount_point=self.mount_point
            )
            return True
        except VaultError as e:
            logger.error(f"设置密钥失败 {path}: {str(e)}")
            return False
    
    async def delete_secret(self, path: str) -> bool:
        """删除密钥
        
        Args:
            path: 密钥路径
            
        Returns:
            是否成功
        """
        try:
            self.client.secrets.kv.v2.delete_metadata_and_all_versions(
                path=path,
                mount_point=self.mount_point
            )
            return True
        except VaultError as e:
            logger.error(f"删除密钥失败 {path}: {str(e)}")
            return False
    
    async def list_secrets(self, path: str = "") -> Optional[list]:
        """列出密钥
        
        Args:
            path: 密钥路径前缀
            
        Returns:
            密钥路径列表，如果失败则返回None
        """
        try:
            response = self.client.secrets.kv.v2.list_secrets(
                path=path,
                mount_point=self.mount_point
            )
            return response['data']['keys']
        except VaultError as e:
            logger.error(f"列出密钥失败 {path}: {str(e)}")
            return None 