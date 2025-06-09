#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ARIES - 贝叶斯分类器模块
使用贝叶斯分类器进行任务分类
"""

import logging
import numpy as np
from typing import Dict, Any, List, Tuple
from sklearn.naive_bayes import GaussianNB
from sklearn.preprocessing import LabelEncoder
from .model_classifier import TaskType, ModelType
from .text_vectorizer import TextVectorizer

class BayesTaskClassifier:
    """贝叶斯任务分类器类"""
    
    def __init__(self, config: Dict[str, Any], vectorizer: TextVectorizer):
        """初始化贝叶斯分类器
        
        Args:
            config: 配置信息
            vectorizer: 文本向量化器
        """
        self.config = config
        self.vectorizer = vectorizer
        self.logger = logging.getLogger("aries_bayes_classifier")
        
        # 初始化分类器
        self.classifier = GaussianNB()
        self.label_encoder = LabelEncoder()
        
        # 初始化训练数据
        self._init_training_data()
        
        # 训练分类器
        self._train_classifier()
    
    def _init_training_data(self):
        """初始化训练数据"""
        # 定义训练数据
        self.training_data = {
            TaskType.LONG_TEXT_LOW_REASONING: [
                "总结这篇长文档的主要内容",
                "对这篇技术文档进行分类",
                "提取这篇报告的关键信息",
                "将这篇长文本分成几个主要部分",
                "生成这篇文档的摘要"
            ],
            TaskType.SHORT_TEXT_LOW_REASONING: [
                "这个命令的作用是什么",
                "如何查看系统状态",
                "显示当前目录内容",
                "检查网络连接状态",
                "查看系统日志"
            ],
            TaskType.SHORT_TEXT_HIGH_REASONING: [
                "分析系统性能问题的原因",
                "为什么会出现这个错误",
                "如何优化数据库性能",
                "评估当前安全策略的有效性",
                "制定系统升级方案"
            ]
        }
    
    def _train_classifier(self):
        """训练分类器"""
        try:
            # 准备训练数据
            texts = []
            labels = []
            
            for task_type, examples in self.training_data.items():
                for text in examples:
                    texts.append(text)
                    labels.append(task_type.value)
            
            # 获取文本向量
            vectors = self.vectorizer.get_batch_embeddings(texts)
            
            # 编码标签
            encoded_labels = self.label_encoder.fit_transform(labels)
            
            # 训练分类器
            self.classifier.fit(vectors, encoded_labels)
            
            self.logger.info("贝叶斯分类器训练完成")
            
        except Exception as e:
            self.logger.error(f"训练分类器失败: {str(e)}")
            raise
    
    def classify(self, text: str) -> Tuple[TaskType, ModelType]:
        """分类任务
        
        Args:
            text: 输入文本
            
        Returns:
            (任务类型, 模型类型)
        """
        try:
            # 获取文本向量
            vector = self.vectorizer.get_embedding(text)
            vector = vector.reshape(1, -1)
            
            # 预测任务类型
            encoded_pred = self.classifier.predict(vector)[0]
            task_type_str = self.label_encoder.inverse_transform([encoded_pred])[0]
            task_type = TaskType(task_type_str)
            
            # 获取预测概率
            probabilities = self.classifier.predict_proba(vector)[0]
            confidence = np.max(probabilities)
            
            # 根据任务类型选择模型
            if task_type == TaskType.LONG_TEXT_LOW_REASONING:
                model_type = ModelType.RWKV
            elif task_type == TaskType.SHORT_TEXT_LOW_REASONING:
                model_type = ModelType.GPT4_MINI
            else:
                model_type = ModelType.GPT4
            
            self.logger.info(f"任务分类结果: {task_type.value}, 选择模型: {model_type.value}, 置信度: {confidence:.2f}")
            
            return task_type, model_type
            
        except Exception as e:
            self.logger.error(f"分类任务失败: {str(e)}")
            # 返回默认分类
            return TaskType.SHORT_TEXT_HIGH_REASONING, ModelType.GPT4
    
    def update_training_data(self, text: str, task_type: TaskType):
        """更新训练数据
        
        Args:
            text: 输入文本
            task_type: 任务类型
        """
        try:
            # 添加新的训练数据
            self.training_data[task_type].append(text)
            
            # 重新训练分类器
            self._train_classifier()
            
            self.logger.info(f"已更新训练数据，当前训练样本数: {sum(len(examples) for examples in self.training_data.values())}")
            
        except Exception as e:
            self.logger.error(f"更新训练数据失败: {str(e)}")
            raise 