#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import numpy as np
import pandas as pd
from datetime import datetime
import logging
from sklearn.preprocessing import StandardScaler
import argparse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('preprocessing.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

def load_raw_data(data_dir):
    """加载原始数据"""
    data = []
    for root, _, files in os.walk(data_dir):
        for file in files:
            if file.endswith('.pcap'):
                file_path = os.path.join(root, file)
                logging.info(f'处理文件: {file_path}')
                # 这里应该调用C++程序处理pcap文件
                # 暂时使用模拟数据
                features = generate_mock_features()
                labels = generate_mock_labels(len(features))
                data.append({
                    'file': file,
                    'features': features,
                    'labels': labels
                })
    return data

def generate_mock_features(num_samples=1000):
    """生成模拟特征数据（仅用于测试）"""
    np.random.seed(42)
    features = []
    for _ in range(num_samples):
        # 生成50维特征向量
        feature_vector = np.random.normal(0, 1, 50)
        features.append(feature_vector.tolist())
    return features

def generate_mock_labels(num_samples, anomaly_ratio=0.1):
    """生成模拟标签（仅用于测试）"""
    np.random.seed(42)
    labels = np.zeros(num_samples)
    num_anomalies = int(num_samples * anomaly_ratio)
    anomaly_indices = np.random.choice(num_samples, num_anomalies, replace=False)
    labels[anomaly_indices] = 1
    return labels.tolist()

def preprocess_features(features):
    """特征预处理"""
    # 转换为numpy数组
    features_array = np.array(features)
    
    # 标准化
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features_array)
    
    return features_scaled, scaler

def save_processed_data(data, output_dir):
    """保存处理后的数据"""
    os.makedirs(output_dir, exist_ok=True)
    
    # 保存处理后的数据
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f'processed_data_{timestamp}.json')
    
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    logging.info(f'处理后的数据已保存到: {output_file}')

def main():
    parser = argparse.ArgumentParser(description='网络流量数据预处理')
    parser.add_argument('--input_dir', type=str, required=True,
                      help='原始数据目录路径')
    parser.add_argument('--output_dir', type=str, required=True,
                      help='处理后数据保存目录路径')
    args = parser.parse_args()
    
    # 加载原始数据
    logging.info('加载原始数据...')
    raw_data = load_raw_data(args.input_dir)
    
    # 处理每个文件的数据
    processed_data = []
    for item in raw_data:
        # 预处理特征
        features_scaled, scaler = preprocess_features(item['features'])
        
        processed_item = {
            'file': item['file'],
            'features': features_scaled.tolist(),
            'labels': item['labels'],
            'feature_stats': {
                'mean': scaler.mean_.tolist(),
                'scale': scaler.scale_.tolist()
            }
        }
        processed_data.append(processed_item)
    
    # 保存处理后的数据
    save_processed_data(processed_data, args.output_dir)
    
    logging.info('数据预处理完成！')

if __name__ == '__main__':
    main() 