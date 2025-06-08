#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import torch
import numpy as np
import pandas as pd
from sklearn.metrics import precision_recall_curve, average_precision_score
from sklearn.metrics import roc_curve, auc, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
import logging
import argparse
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('evaluation.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

def load_model(model_path, input_dim, device):
    """加载模型"""
    from train_model import AnomalyDetector
    
    model = AnomalyDetector(input_dim).to(device)
    checkpoint = torch.load(model_path, map_location=device)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.eval()
    return model

def load_data(data_path):
    """加载测试数据"""
    with open(data_path, 'r') as f:
        data = json.load(f)
    return data

def evaluate_model(model, features, labels, device, threshold=0.5):
    """评估模型性能"""
    model.eval()
    features_tensor = torch.FloatTensor(features).to(device)
    
    with torch.no_grad():
        _, anomaly_scores = model(features_tensor)
        anomaly_scores = anomaly_scores.cpu().numpy()
    
    # 计算各种评估指标
    precision, recall, thresholds = precision_recall_curve(labels, anomaly_scores)
    avg_precision = average_precision_score(labels, anomaly_scores)
    
    fpr, tpr, _ = roc_curve(labels, anomaly_scores)
    roc_auc = auc(fpr, tpr)
    
    # 使用阈值进行分类
    predictions = (anomaly_scores >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(labels, predictions).ravel()
    
    # 计算其他指标
    accuracy = (tp + tn) / (tp + tn + fp + fn)
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    return {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1_score': f1_score,
        'avg_precision': avg_precision,
        'roc_auc': roc_auc,
        'confusion_matrix': {
            'tn': int(tn),
            'fp': int(fp),
            'fn': int(fn),
            'tp': int(tp)
        },
        'anomaly_scores': anomaly_scores.tolist()
    }

def plot_metrics(results, output_dir):
    """绘制评估指标图表"""
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 绘制ROC曲线
    plt.figure(figsize=(10, 6))
    plt.plot([0, 1], [0, 1], 'k--')
    plt.plot(fpr, tpr, label=f'ROC (AUC = {results["roc_auc"]:.3f})')
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('ROC Curve')
    plt.legend()
    plt.savefig(os.path.join(output_dir, f'roc_curve_{timestamp}.png'))
    plt.close()
    
    # 绘制混淆矩阵
    plt.figure(figsize=(8, 6))
    cm = np.array([
        [results['confusion_matrix']['tn'], results['confusion_matrix']['fp']],
        [results['confusion_matrix']['fn'], results['confusion_matrix']['tp']]
    ])
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
    plt.xlabel('Predicted')
    plt.ylabel('Actual')
    plt.title('Confusion Matrix')
    plt.savefig(os.path.join(output_dir, f'confusion_matrix_{timestamp}.png'))
    plt.close()
    
    # 绘制异常分数分布
    plt.figure(figsize=(10, 6))
    plt.hist(results['anomaly_scores'], bins=50)
    plt.xlabel('Anomaly Score')
    plt.ylabel('Count')
    plt.title('Distribution of Anomaly Scores')
    plt.savefig(os.path.join(output_dir, f'anomaly_scores_dist_{timestamp}.png'))
    plt.close()

def save_results(results, output_dir):
    """保存评估结果"""
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f'evaluation_results_{timestamp}.json')
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logging.info(f'评估结果已保存到: {output_file}')

def main():
    parser = argparse.ArgumentParser(description='评估异常检测模型')
    parser.add_argument('--model_path', type=str, required=True,
                      help='模型文件路径')
    parser.add_argument('--data_path', type=str, required=True,
                      help='测试数据文件路径')
    parser.add_argument('--output_dir', type=str, required=True,
                      help='评估结果保存目录')
    parser.add_argument('--threshold', type=float, default=0.5,
                      help='异常检测阈值')
    args = parser.parse_args()
    
    # 设置设备
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logging.info(f'使用设备: {device}')
    
    # 加载数据
    logging.info('加载测试数据...')
    data = load_data(args.data_path)
    features = np.array(data['features'])
    labels = np.array(data['labels'])
    
    # 加载模型
    logging.info('加载模型...')
    input_dim = features.shape[1]
    model = load_model(args.model_path, input_dim, device)
    
    # 评估模型
    logging.info('开始评估模型...')
    results = evaluate_model(model, features, labels, device, args.threshold)
    
    # 打印评估结果
    logging.info('评估结果:')
    logging.info(f'准确率: {results["accuracy"]:.4f}')
    logging.info(f'精确率: {results["precision"]:.4f}')
    logging.info(f'召回率: {results["recall"]:.4f}')
    logging.info(f'F1分数: {results["f1_score"]:.4f}')
    logging.info(f'平均精确率: {results["avg_precision"]:.4f}')
    logging.info(f'ROC AUC: {results["roc_auc"]:.4f}')
    
    # 绘制评估指标图表
    logging.info('绘制评估指标图表...')
    plot_metrics(results, args.output_dir)
    
    # 保存评估结果
    save_results(results, args.output_dir)
    
    logging.info('评估完成！')

if __name__ == '__main__':
    main() 