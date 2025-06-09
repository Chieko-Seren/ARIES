#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ARIES - RWKV模型管理模块
使用 llama.cpp 实现 RWKV 模型的加载和推理功能
"""

import os
import json
import logging
from typing import Dict, Any, Optional
import ctypes
from llama_cpp import Llama

class RWKVManager:
    """RWKV模型管理类，用于处理RWKV模型的加载和推理"""
    
    def __init__(self, model_path: str, config: Dict[str, Any]):
        """初始化RWKV管理器
        
        Args:
            model_path: RWKV模型路径
            config: 模型配置
        """
        self.model_path = model_path
        self.config = config
        self.logger = logging.getLogger("aries_rwkv")
        
        # 初始化模型
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """加载RWKV模型"""
        try:
            # 检查模型文件是否存在
            if not os.path.exists(self.model_path):
                raise FileNotFoundError(f"RWKV模型文件不存在: {self.model_path}")
            
            # 设置模型参数
            n_ctx = self.config.get("context_length", 2048)
            n_batch = self.config.get("batch_size", 512)
            n_threads = self.config.get("threads", 4)
            n_gpu_layers = self.config.get("gpu_layers", 0)
            
            # 加载模型
            self.model = Llama(
                model_path=self.model_path,
                n_ctx=n_ctx,
                n_batch=n_batch,
                n_threads=n_threads,
                n_gpu_layers=n_gpu_layers,
                verbose=False
            )
            
            self.logger.info(f"已加载RWKV模型: {self.model_path}")
            self.logger.info(f"上下文长度: {n_ctx}, 批处理大小: {n_batch}, 线程数: {n_threads}, GPU层数: {n_gpu_layers}")
            
        except Exception as e:
            self.logger.error(f"加载RWKV模型失败: {str(e)}")
            raise
    
    def generate(self, prompt: str, system_message: Optional[str] = None) -> Dict[str, Any]:
        """生成文本
        
        Args:
            prompt: 提示词
            system_message: 系统消息
            
        Returns:
            生成的文本响应
        """
        try:
            # 构建完整提示词
            full_prompt = ""
            if system_message:
                full_prompt += f"System: {system_message}\n\n"
            full_prompt += f"User: {prompt}\n\nAssistant:"
            
            # 设置生成参数
            temperature = self.config.get("temperature", 0.7)
            top_p = self.config.get("top_p", 0.9)
            max_tokens = self.config.get("max_tokens", 2000)
            stop = ["\n\n", "User:", "System:"]
            
            # 生成文本
            response = self.model(
                full_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                stop=stop,
                echo=False
            )
            
            # 提取生成的文本
            generated_text = response["choices"][0]["text"].strip()
            
            # 构建响应
            response = {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": generated_text
                    }
                }]
            }
            
            return response
            
        except Exception as e:
            self.logger.error(f"生成文本失败: {str(e)}")
            raise 