#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ARIES - 故障预测器测试模块
测试故障预测功能
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from ..core.prediction.fault_predictor import FaultPredictor

def test_predictor_initialization(test_db):
    """测试预测器初始化"""
    predictor = FaultPredictor(test_db)
    assert predictor.rf_model is not None, "随机森林模型未初始化"
    assert predictor.isolation_forest is not None, "异常检测模型未初始化"
    assert predictor.scaler is not None, "标准化器未初始化"

def test_prepare_features(test_db):
    """测试特征准备"""
    predictor = FaultPredictor(test_db)
    
    # 测试数据
    server_data = {
        'server_id': 'test_server',
        'cpu_usage': 75.5,
        'memory_usage': 60.0,
        'disk_usage': 80.0,
        'network_usage': 45.0,
        'error_count': 5
    }
    
    features = predictor._prepare_features(server_data)
    assert features is not None, "特征准备失败"
    assert len(features) == 9, "特征数量错误"
    assert all(isinstance(x, (int, float)) for x in features), "特征类型错误"

def test_risk_level_determination(test_db):
    """测试风险等级确定"""
    predictor = FaultPredictor(test_db)
    
    # 测试不同场景
    test_cases = [
        (0.9, 0.8, "critical"),
        (0.7, 0.5, "high"),
        (0.5, 0.3, "medium"),
        (0.3, 0.2, "low"),
        (0.1, 0.1, "normal")
    ]
    
    for fault_prob, anomaly_score, expected_level in test_cases:
        risk_level = predictor._determine_risk_level(fault_prob, anomaly_score)
        assert risk_level == expected_level, f"风险等级判断错误: {fault_prob}, {anomaly_score}"

def test_confidence_calculation(test_db):
    """测试置信度计算"""
    predictor = FaultPredictor(test_db)
    
    # 测试不同场景
    test_cases = [
        (0.9, 0.1, 0.99),  # 高故障概率，低异常分数
        (0.5, 0.5, 0.375),  # 中等故障概率，中等异常分数
        (0.1, 0.9, 0.01)   # 低故障概率，高异常分数
    ]
    
    for fault_prob, anomaly_score, expected_confidence in test_cases:
        confidence = predictor._calculate_confidence(fault_prob, anomaly_score)
        assert abs(confidence - expected_confidence) < 0.01, f"置信度计算错误: {fault_prob}, {anomaly_score}"

def test_fault_prediction(test_db):
    """测试故障预测"""
    predictor = FaultPredictor(test_db)
    
    # 测试数据
    server_data = {
        'server_id': 'test_server',
        'cpu_usage': 90.0,  # 高CPU使用率
        'memory_usage': 85.0,  # 高内存使用率
        'disk_usage': 95.0,  # 高磁盘使用率
        'network_usage': 80.0,  # 高网络使用率
        'error_count': 10  # 高错误计数
    }
    
    # 预测故障概率
    prediction = predictor.predict_fault_probability(server_data)
    
    # 验证预测结果
    assert "fault_probability" in prediction, "预测结果缺少故障概率"
    assert "anomaly_score" in prediction, "预测结果缺少异常分数"
    assert "risk_level" in prediction, "预测结果缺少风险等级"
    assert "confidence" in prediction, "预测结果缺少置信度"
    
    # 验证数值范围
    assert 0 <= prediction["fault_probability"] <= 1, "故障概率超出范围"
    assert 0 <= prediction["anomaly_score"] <= 1, "异常分数超出范围"
    assert 0 <= prediction["confidence"] <= 1, "置信度超出范围"
    assert prediction["risk_level"] in ["normal", "low", "medium", "high", "critical", "unknown", "error"], "无效的风险等级"

def test_model_update(test_db):
    """测试模型更新"""
    predictor = FaultPredictor(test_db)
    
    # 添加一些测试数据
    test_data = [
        {
            'server_id': 'test_server',
            'timestamp': datetime.now() - timedelta(days=i),
            'fault_type': 'cpu_high' if i % 2 == 0 else None,
            'severity': 'high' if i % 2 == 0 else 'normal',
            'component': 'cpu',
            'status': 'resolved',
            'resolution_time': 3600,
            'cpu_usage': 90.0 if i % 2 == 0 else 50.0,
            'memory_usage': 80.0 if i % 2 == 0 else 60.0,
            'disk_usage': 70.0 if i % 2 == 0 else 50.0,
            'network_usage': 60.0 if i % 2 == 0 else 40.0,
            'error_count': 10 if i % 2 == 0 else 2
        }
        for i in range(30)
    ]
    
    # 插入测试数据
    for data in test_data:
        test_db.execute_update("""
            INSERT INTO fault_records (
                server_id, timestamp, fault_type, severity, component,
                status, resolution_time, cpu_usage, memory_usage,
                disk_usage, network_usage, error_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data['server_id'], data['timestamp'], data['fault_type'],
            data['severity'], data['component'], data['status'],
            data['resolution_time'], data['cpu_usage'], data['memory_usage'],
            data['disk_usage'], data['network_usage'], data['error_count']
        ))
    
    # 更新模型
    predictor.update_model()
    
    # 验证模型是否更新
    server_data = {
        'server_id': 'test_server',
        'cpu_usage': 90.0,
        'memory_usage': 85.0,
        'disk_usage': 95.0,
        'network_usage': 80.0,
        'error_count': 10
    }
    
    prediction = predictor.predict_fault_probability(server_data)
    assert prediction["fault_probability"] > 0, "更新后的模型预测失败"

def test_model_persistence(test_db, tmp_path):
    """测试模型持久化"""
    predictor = FaultPredictor(test_db)
    
    # 保存模型
    model_path = tmp_path / "test_model.joblib"
    predictor.save_model(str(model_path))
    assert model_path.exists(), "模型文件未保存"
    
    # 创建新的预测器实例
    new_predictor = FaultPredictor(test_db)
    
    # 加载模型
    new_predictor.load_model(str(model_path))
    
    # 验证模型是否一致
    server_data = {
        'server_id': 'test_server',
        'cpu_usage': 90.0,
        'memory_usage': 85.0,
        'disk_usage': 95.0,
        'network_usage': 80.0,
        'error_count': 10
    }
    
    original_prediction = predictor.predict_fault_probability(server_data)
    loaded_prediction = new_predictor.predict_fault_probability(server_data)
    
    assert abs(original_prediction["fault_probability"] - loaded_prediction["fault_probability"]) < 0.01, "模型加载后预测不一致"
    assert original_prediction["risk_level"] == loaded_prediction["risk_level"], "模型加载后风险等级不一致"

def test_error_handling(test_db):
    """测试错误处理"""
    predictor = FaultPredictor(test_db)
    
    # 测试无效数据
    invalid_data = {
        'server_id': 'test_server',
        'cpu_usage': 'invalid',  # 无效的CPU使用率
        'memory_usage': None,    # 缺失的内存使用率
        'disk_usage': -1,        # 无效的磁盘使用率
        'network_usage': 101,    # 超出范围的网络使用率
        'error_count': 'many'    # 无效的错误计数
    }
    
    prediction = predictor.predict_fault_probability(invalid_data)
    assert prediction["risk_level"] in ["unknown", "error"], "无效数据处理错误"
    assert prediction["confidence"] == 0.0, "无效数据置信度错误"
    
    # 测试数据库错误
    with pytest.raises(Exception):
        predictor._load_historical_data()
        # 模拟数据库错误
 