#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ARIES - 故障预测模块
基于概率论和传统机器学习的故障预测功能
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import joblib
from typing import Dict, List, Tuple, Optional, Any
import logging
from datetime import datetime, timedelta
from ..database.db import Database

logger = logging.getLogger(__name__)

class FaultPredictor:
    """故障预测器类"""
    
    def __init__(self, db: Database):
        """初始化故障预测器
        
        Args:
            db: 数据库实例
        """
        self.db = db
        self.rf_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        self.isolation_forest = IsolationForest(
            contamination=0.1,
            random_state=42
        )
        self.scaler = StandardScaler()
        self._init_models()
    
    def _init_models(self):
        """初始化模型"""
        try:
            # 从数据库加载历史数据
            historical_data = self._load_historical_data()
            if historical_data is not None and len(historical_data) > 0:
                # 准备训练数据
                X, y = self._prepare_training_data(historical_data)
                if len(X) > 0 and len(y) > 0:
                    # 训练模型
                    self._train_models(X, y)
                    logger.info("模型初始化成功")
                else:
                    logger.warning("训练数据不足，使用默认模型")
            else:
                logger.warning("无历史数据，使用默认模型")
        except Exception as e:
            logger.error(f"模型初始化失败: {str(e)}")
    
    def _load_historical_data(self) -> Optional[pd.DataFrame]:
        """从数据库加载历史数据
        
        Returns:
            历史数据DataFrame
        """
        try:
            # 获取最近30天的故障记录
            query = """
                SELECT 
                    server_id,
                    timestamp,
                    fault_type,
                    severity,
                    component,
                    status,
                    resolution_time,
                    cpu_usage,
                    memory_usage,
                    disk_usage,
                    network_usage,
                    error_count
                FROM fault_records
                WHERE timestamp >= datetime('now', '-30 days')
                ORDER BY timestamp
            """
            records = self.db.execute_query(query)
            
            if not records:
                return None
            
            # 转换为DataFrame
            df = pd.DataFrame(records)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            return df
            
        except Exception as e:
            logger.error(f"加载历史数据失败: {str(e)}")
            return None
    
    def _prepare_training_data(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """准备训练数据
        
        Args:
            df: 原始数据DataFrame
            
        Returns:
            特征矩阵X和标签y
        """
        try:
            # 特征工程
            df['hour'] = df['timestamp'].dt.hour
            df['day_of_week'] = df['timestamp'].dt.dayofweek
            df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
            
            # 计算故障率
            df['fault_rate'] = df.groupby('server_id')['fault_type'].transform('count') / 30
            
            # 选择特征
            features = [
                'hour', 'day_of_week', 'is_weekend',
                'cpu_usage', 'memory_usage', 'disk_usage', 'network_usage',
                'error_count', 'fault_rate'
            ]
            
            # 准备标签（1表示发生故障，0表示正常）
            df['fault_occurred'] = (df['fault_type'].notna()).astype(int)
            
            # 标准化特征
            X = self.scaler.fit_transform(df[features])
            y = df['fault_occurred'].values
            
            return X, y
            
        except Exception as e:
            logger.error(f"准备训练数据失败: {str(e)}")
            return np.array([]), np.array([])
    
    def _train_models(self, X: np.ndarray, y: np.ndarray):
        """训练模型
        
        Args:
            X: 特征矩阵
            y: 标签
        """
        try:
            # 分割训练集和测试集
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # 训练随机森林模型
            self.rf_model.fit(X_train, y_train)
            
            # 训练异常检测模型
            self.isolation_forest.fit(X_train)
            
            # 评估模型
            y_pred = self.rf_model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred)
            recall = recall_score(y_test, y_pred)
            f1 = f1_score(y_test, y_pred)
            
            logger.info(f"模型评估结果 - 准确率: {accuracy:.2f}, 精确率: {precision:.2f}, "
                       f"召回率: {recall:.2f}, F1分数: {f1:.2f}")
            
        except Exception as e:
            logger.error(f"训练模型失败: {str(e)}")
    
    def predict_fault_probability(self, server_data: Dict[str, Any]) -> Dict[str, Any]:
        """预测故障概率
        
        Args:
            server_data: 服务器数据，包含各种指标
            
        Returns:
            预测结果，包含故障概率和异常分数
        """
        try:
            # 准备特征
            features = self._prepare_features(server_data)
            if features is None:
                return {
                    "fault_probability": 0.0,
                    "anomaly_score": 0.0,
                    "risk_level": "unknown",
                    "confidence": 0.0
                }
            
            # 标准化特征
            X = self.scaler.transform([features])
            
            # 预测故障概率
            fault_prob = self.rf_model.predict_proba(X)[0][1]
            
            # 计算异常分数
            anomaly_score = -self.isolation_forest.score_samples(X)[0]
            
            # 确定风险等级
            risk_level = self._determine_risk_level(fault_prob, anomaly_score)
            
            # 计算置信度
            confidence = self._calculate_confidence(fault_prob, anomaly_score)
            
            return {
                "fault_probability": float(fault_prob),
                "anomaly_score": float(anomaly_score),
                "risk_level": risk_level,
                "confidence": float(confidence)
            }
            
        except Exception as e:
            logger.error(f"预测故障概率失败: {str(e)}")
            return {
                "fault_probability": 0.0,
                "anomaly_score": 0.0,
                "risk_level": "error",
                "confidence": 0.0
            }
    
    def _prepare_features(self, server_data: Dict[str, Any]) -> Optional[List[float]]:
        """准备特征数据
        
        Args:
            server_data: 服务器数据
            
        Returns:
            特征列表
        """
        try:
            # 获取当前时间特征
            now = datetime.now()
            hour = now.hour
            day_of_week = now.weekday()
            is_weekend = int(day_of_week in [5, 6])
            
            # 获取服务器指标
            cpu_usage = server_data.get('cpu_usage', 0.0)
            memory_usage = server_data.get('memory_usage', 0.0)
            disk_usage = server_data.get('disk_usage', 0.0)
            network_usage = server_data.get('network_usage', 0.0)
            error_count = server_data.get('error_count', 0)
            
            # 计算故障率
            server_id = server_data.get('server_id')
            if server_id:
                query = """
                    SELECT COUNT(*) as fault_count
                    FROM fault_records
                    WHERE server_id = ? AND timestamp >= datetime('now', '-30 days')
                """
                result = self.db.execute_query(query, (server_id,))
                fault_count = result[0]['fault_count'] if result else 0
                fault_rate = fault_count / 30
            else:
                fault_rate = 0.0
            
            return [
                hour, day_of_week, is_weekend,
                cpu_usage, memory_usage, disk_usage, network_usage,
                error_count, fault_rate
            ]
            
        except Exception as e:
            logger.error(f"准备特征数据失败: {str(e)}")
            return None
    
    def _determine_risk_level(self, fault_prob: float, anomaly_score: float) -> str:
        """确定风险等级
        
        Args:
            fault_prob: 故障概率
            anomaly_score: 异常分数
            
        Returns:
            风险等级
        """
        # 综合故障概率和异常分数
        risk_score = (fault_prob * 0.7 + anomaly_score * 0.3)
        
        if risk_score >= 0.8:
            return "critical"
        elif risk_score >= 0.6:
            return "high"
        elif risk_score >= 0.4:
            return "medium"
        elif risk_score >= 0.2:
            return "low"
        else:
            return "normal"
    
    def _calculate_confidence(self, fault_prob: float, anomaly_score: float) -> float:
        """计算预测置信度
        
        Args:
            fault_prob: 故障概率
            anomaly_score: 异常分数
            
        Returns:
            置信度分数
        """
        # 基于预测概率的分布计算置信度
        if fault_prob > 0.5:
            confidence = 1 - (1 - fault_prob) ** 2
        else:
            confidence = 1 - fault_prob ** 2
        
        # 考虑异常分数的影响
        confidence = confidence * (1 - min(anomaly_score, 1.0))
        
        return confidence
    
    def update_model(self):
        """更新模型"""
        try:
            # 重新加载历史数据
            historical_data = self._load_historical_data()
            if historical_data is not None and len(historical_data) > 0:
                # 准备训练数据
                X, y = self._prepare_training_data(historical_data)
                if len(X) > 0 and len(y) > 0:
                    # 重新训练模型
                    self._train_models(X, y)
                    logger.info("模型更新成功")
                else:
                    logger.warning("训练数据不足，模型未更新")
            else:
                logger.warning("无历史数据，模型未更新")
        except Exception as e:
            logger.error(f"更新模型失败: {str(e)}")
    
    def save_model(self, path: str):
        """保存模型
        
        Args:
            path: 保存路径
        """
        try:
            model_data = {
                'rf_model': self.rf_model,
                'isolation_forest': self.isolation_forest,
                'scaler': self.scaler
            }
            joblib.dump(model_data, path)
            logger.info(f"模型保存成功: {path}")
        except Exception as e:
            logger.error(f"保存模型失败: {str(e)}")
    
    def load_model(self, path: str):
        """加载模型
        
        Args:
            path: 模型路径
        """
        try:
            model_data = joblib.load(path)
            self.rf_model = model_data['rf_model']
            self.isolation_forest = model_data['isolation_forest']
            self.scaler = model_data['scaler']
            logger.info(f"模型加载成功: {path}")
        except Exception as e:
            logger.error(f"加载模型失败: {str(e)}") 