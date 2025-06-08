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
            历史数据DataFrame，如果加载失败则返回None
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
                self.logger.warning("没有找到历史故障记录")
                return None
            
            # 转换为DataFrame
            df = pd.DataFrame(records)
            
            # 数据验证
            required_columns = [
                'server_id', 'timestamp', 'fault_type', 'severity',
                'component', 'status', 'cpu_usage', 'memory_usage',
                'disk_usage', 'network_usage', 'error_count'
            ]
            
            # 检查必需列是否存在
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"数据缺少必需列: {missing_columns}")
            
            # 数据类型转换和验证
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['server_id'] = df['server_id'].astype(str)
            df['fault_type'] = df['fault_type'].astype(str)
            df['severity'] = pd.to_numeric(df['severity'], errors='coerce')
            df['component'] = df['component'].astype(str)
            df['status'] = df['status'].astype(str)
            
            # 验证数值列的范围
            numeric_columns = ['cpu_usage', 'memory_usage', 'disk_usage', 'network_usage', 'error_count']
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                # 检查是否在合理范围内
                if col.endswith('_usage'):
                    invalid_mask = (df[col] < 0) | (df[col] > 100)
                    if invalid_mask.any():
                        self.logger.warning(f"列 {col} 包含超出范围的值 (0-100): {df[invalid_mask][col].tolist()}")
                        df.loc[invalid_mask, col] = df.loc[invalid_mask, col].clip(0, 100)
                elif col == 'error_count':
                    invalid_mask = df[col] < 0
                    if invalid_mask.any():
                        self.logger.warning(f"列 {col} 包含负值: {df[invalid_mask][col].tolist()}")
                        df.loc[invalid_mask, col] = 0
            
            # 检查时间戳的连续性
            df = df.sort_values('timestamp')
            time_diff = df['timestamp'].diff()
            large_gaps = time_diff[time_diff > pd.Timedelta(hours=24)]
            if not large_gaps.empty:
                self.logger.warning(f"数据中存在时间间隔超过24小时的记录: {large_gaps.index.tolist()}")
            
            # 检查重复记录
            duplicates = df.duplicated(subset=['server_id', 'timestamp', 'fault_type'], keep=False)
            if duplicates.any():
                self.logger.warning(f"发现重复记录: {df[duplicates].index.tolist()}")
                df = df.drop_duplicates(subset=['server_id', 'timestamp', 'fault_type'], keep='first')
            
            return df
            
        except Exception as e:
            self.logger.error(f"加载历史数据失败: {str(e)}")
            return None
    
    def _prepare_training_data(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """准备训练数据
        
        Args:
            df: 原始数据DataFrame
            
        Returns:
            特征矩阵X和标签y
            
        Raises:
            ValueError: 当数据准备失败时抛出
        """
        try:
            if df is None or df.empty:
                raise ValueError("输入数据为空")
            
            # 特征工程
            df['hour'] = df['timestamp'].dt.hour
            df['day_of_week'] = df['timestamp'].dt.dayofweek
            df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
            
            # 计算故障率（使用滑动窗口）
            df['fault_rate'] = df.groupby('server_id')['fault_type'].transform(
                lambda x: x.rolling(window=24, min_periods=1).count() / 24
            )
            
            # 选择特征
            features = [
                'hour', 'day_of_week', 'is_weekend',
                'cpu_usage', 'memory_usage', 'disk_usage', 'network_usage',
                'error_count', 'fault_rate'
            ]
            
            # 检查特征是否存在
            missing_features = [f for f in features if f not in df.columns]
            if missing_features:
                raise ValueError(f"缺少必需特征: {missing_features}")
            
            # 处理缺失值
            for feature in features:
                if df[feature].isnull().any():
                    if feature in ['cpu_usage', 'memory_usage', 'disk_usage', 'network_usage']:
                        # 使用前向填充和后向填充的组合
                        df[feature] = df[feature].fillna(method='ffill').fillna(method='bfill')
                    else:
                        # 对于其他特征，使用中位数填充
                        df[feature] = df[feature].fillna(df[feature].median())
            
            # 准备标签（1表示发生故障，0表示正常）
            df['fault_occurred'] = (df['fault_type'].notna()).astype(int)
            
            # 标准化特征
            X = self.scaler.fit_transform(df[features])
            y = df['fault_occurred'].values
            
            # 验证数据
            if np.isnan(X).any() or np.isinf(X).any():
                raise ValueError("特征矩阵包含无效值 (NaN 或 Inf)")
            
            if not np.all(np.isfinite(y)):
                raise ValueError("标签包含无效值")
            
            return X, y
            
        except Exception as e:
            self.logger.error(f"准备训练数据失败: {str(e)}")
            raise ValueError(f"数据准备失败: {str(e)}")
    
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