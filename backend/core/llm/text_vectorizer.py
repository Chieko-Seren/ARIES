#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ARIES - 文本向量化模块
使用 RWKV-7 模型进行文本向量化
"""

import logging
import numpy as np
from typing import List, Dict, Any
from llama_cpp import Llama

class TextVectorizer:
    """文本向量化类，使用 RWKV-7 模型进行文本向量化"""
    
    def __init__(self, model_path: str, config: Dict[str, Any]):
        """初始化向量化器
        
        Args:
            model_path: RWKV-7 模型路径
            config: 模型配置
        """
        self.model_path = model_path
        self.config = config
        self.logger = logging.getLogger("aries_vectorizer")
        
        # 初始化模型
        self.model = None
        self._init_model()
        
        # 向量维度
        self.vector_dim = 4096  # RWKV-7 的隐藏层维度
    
    def _init_model(self):
        """初始化 RWKV-7 模型"""
        try:
            self.model = Llama(
                model_path=self.model_path,
                n_ctx=self.config.get("context_length", 2048),
                n_batch=self.config.get("batch_size", 512),
                n_threads=self.config.get("threads", 4),
                n_gpu_layers=self.config.get("gpu_layers", 0),
                embedding=True,  # 启用嵌入模式
                verbose=False
            )
            self.logger.info(f"已加载 RWKV-7 模型: {self.model_path}")
        except Exception as e:
            self.logger.error(f"加载 RWKV-7 模型失败: {str(e)}")
            raise
    
    def get_embedding(self, text: str) -> np.ndarray:
        """获取文本的向量表示
        
        Args:
            text: 输入文本
            
        Returns:
            文本的向量表示
        """
        try:
            # 使用 RWKV-7 获取文本嵌入
            embedding = self.model.embed(text)
            
            # 转换为numpy数组并归一化
            vector = np.array(embedding)
            vector = vector / np.linalg.norm(vector)
            
            return vector
        except Exception as e:
            self.logger.error(f"获取文本向量失败: {str(e)}")
            raise
    
    def get_batch_embeddings(self, texts: List[str]) -> np.ndarray:
        """批量获取文本的向量表示
        
        Args:
            texts: 输入文本列表
            
        Returns:
            文本向量矩阵
        """
        try:
            vectors = []
            for text in texts:
                vector = self.get_embedding(text)
                vectors.append(vector)
            return np.array(vectors)
        except Exception as e:
            self.logger.error(f"批量获取文本向量失败: {str(e)}")
            raise 