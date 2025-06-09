#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ARIES - 模型分类器模块
使用贝叶斯分类器和文本向量化进行任务分类
"""

import logging
from enum import Enum
from typing import Dict, Any, Tuple
from .bayes_classifier import BayesTaskClassifier
from .text_vectorizer import TextVectorizer

class TaskType(str, Enum):
    """任务类型枚举"""
    LONG_TEXT_LOW_REASONING = "long_text_low_reasoning"  # 长文本低推理
    SHORT_TEXT_LOW_REASONING = "short_text_low_reasoning"  # 短文本低推理
    SHORT_TEXT_HIGH_REASONING = "short_text_high_reasoning"  # 短文本高推理

class ModelType(str, Enum):
    """模型类型枚举"""
    GPT4 = "gpt4"  # GPT-4模型
    GPT4_MINI = "gpt4-mini"  # GPT-4-mini模型
    RWKV = "rwkv"  # RWKV模型

class ModelClassifier:
    """模型分类器类"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化模型分类器
        
        Args:
            config: 配置信息
        """
        self.config = config
        self.logger = logging.getLogger("aries_model_classifier")
        
        # 初始化文本向量化器
        self.vectorizer = TextVectorizer(config)
        
        # 初始化贝叶斯分类器
        self.classifier = BayesTaskClassifier(config, self.vectorizer)
    
    def classify_task(self, text: str) -> Tuple[TaskType, ModelType]:
        """分类任务并选择合适的模型
        
        Args:
            text: 输入文本
            
        Returns:
            (任务类型, 模型类型)
        """
        try:
            # 使用贝叶斯分类器进行分类
            task_type, model_type = self.classifier.classify(text)
            
            self.logger.info(f"任务分类完成: {task_type.value} -> {model_type.value}")
            
            return task_type, model_type
            
        except Exception as e:
            self.logger.error(f"任务分类失败: {str(e)}")
            # 返回默认分类
            return TaskType.SHORT_TEXT_HIGH_REASONING, ModelType.GPT4
    
    def update_classifier(self, text: str, task_type: TaskType):
        """更新分类器训练数据
        
        Args:
            text: 输入文本
            task_type: 任务类型
        """
        try:
            self.classifier.update_training_data(text, task_type)
            self.logger.info(f"分类器训练数据已更新: {task_type.value}")
        except Exception as e:
            self.logger.error(f"更新分类器失败: {str(e)}")
            raise 