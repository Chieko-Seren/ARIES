#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import pandas as pd
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('training.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class NetworkDataset(Dataset):
    def __init__(self, features, labels):
        self.features = torch.FloatTensor(features)
        self.labels = torch.FloatTensor(labels)

    def __len__(self):
        return len(self.features)

    def __getitem__(self, idx):
        return self.features[idx], self.labels[idx]

class AnomalyDetector(nn.Module):
    def __init__(self, input_dim):
        super(AnomalyDetector, self).__init__()
        
        # 编码器
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, 32),
            nn.ReLU()
        )
        
        # 解码器
        self.decoder = nn.Sequential(
            nn.Linear(32, 64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, 128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, input_dim),
            nn.Sigmoid()
        )
        
        # 异常检测头
        self.anomaly_head = nn.Sequential(
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Linear(16, 1),
            nn.Sigmoid()
        )

    def forward(self, x):
        # 编码
        encoded = self.encoder(x)
        # 解码
        decoded = self.decoder(encoded)
        # 异常检测
        anomaly_score = self.anomaly_head(encoded)
        return decoded, anomaly_score

def load_data(data_dir):
    """加载训练数据"""
    features = []
    labels = []
    
    # 遍历数据目录
    for root, _, files in os.walk(data_dir):
        for file in files:
            if file.endswith('.json'):
                with open(os.path.join(root, file), 'r') as f:
                    data = json.load(f)
                    features.extend(data['features'])
                    labels.extend(data['labels'])
    
    return np.array(features), np.array(labels)

def train_model(model, train_loader, val_loader, criterion, optimizer, 
                device, num_epochs, model_save_path):
    """训练模型"""
    best_val_loss = float('inf')
    train_losses = []
    val_losses = []
    
    for epoch in range(num_epochs):
        # 训练阶段
        model.train()
        train_loss = 0
        for batch_features, batch_labels in train_loader:
            batch_features = batch_features.to(device)
            batch_labels = batch_labels.to(device)
            
            optimizer.zero_grad()
            decoded, anomaly_scores = model(batch_features)
            
            # 计算重建损失和异常检测损失
            reconstruction_loss = criterion(decoded, batch_features)
            anomaly_loss = criterion(anomaly_scores, batch_labels.unsqueeze(1))
            loss = reconstruction_loss + anomaly_loss
            
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item()
        
        avg_train_loss = train_loss / len(train_loader)
        train_losses.append(avg_train_loss)
        
        # 验证阶段
        model.eval()
        val_loss = 0
        with torch.no_grad():
            for batch_features, batch_labels in val_loader:
                batch_features = batch_features.to(device)
                batch_labels = batch_labels.to(device)
                
                decoded, anomaly_scores = model(batch_features)
                reconstruction_loss = criterion(decoded, batch_features)
                anomaly_loss = criterion(anomaly_scores, batch_labels.unsqueeze(1))
                loss = reconstruction_loss + anomaly_loss
                
                val_loss += loss.item()
        
        avg_val_loss = val_loss / len(val_loader)
        val_losses.append(avg_val_loss)
        
        # 保存最佳模型
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'train_loss': train_losses,
                'val_loss': val_losses
            }, model_save_path)
        
        logging.info(f'Epoch {epoch+1}/{num_epochs}:')
        logging.info(f'Average Training Loss: {avg_train_loss:.4f}')
        logging.info(f'Average Validation Loss: {avg_val_loss:.4f}')
    
    return train_losses, val_losses

def main():
    # 配置参数
    data_dir = '../data'
    model_save_dir = '../models'
    input_dim = 50  # 特征维度
    batch_size = 64
    num_epochs = 100
    learning_rate = 0.001
    
    # 创建模型保存目录
    os.makedirs(model_save_dir, exist_ok=True)
    
    # 设置设备
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logging.info(f'使用设备: {device}')
    
    # 加载数据
    logging.info('加载数据...')
    features, labels = load_data(data_dir)
    
    # 数据预处理
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)
    
    # 保存scaler
    scaler_path = os.path.join(model_save_dir, 'scaler.pkl')
    torch.save(scaler, scaler_path)
    
    # 划分训练集和验证集
    X_train, X_val, y_train, y_val = train_test_split(
        features_scaled, labels, test_size=0.2, random_state=42
    )
    
    # 创建数据加载器
    train_dataset = NetworkDataset(X_train, y_train)
    val_dataset = NetworkDataset(X_val, y_val)
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size)
    
    # 创建模型
    model = AnomalyDetector(input_dim).to(device)
    
    # 定义损失函数和优化器
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)
    
    # 训练模型
    logging.info('开始训练...')
    model_save_path = os.path.join(model_save_dir, 
                                 f'anomaly_detector_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pt')
    train_losses, val_losses = train_model(
        model, train_loader, val_loader, criterion, optimizer,
        device, num_epochs, model_save_path
    )
    
    # 保存训练历史
    history = {
        'train_losses': train_losses,
        'val_losses': val_losses
    }
    history_path = os.path.join(model_save_dir, 'training_history.json')
    with open(history_path, 'w') as f:
        json.dump(history, f)
    
    logging.info('训练完成！')
    logging.info(f'模型已保存到: {model_save_path}')
    logging.info(f'训练历史已保存到: {history_path}')

if __name__ == '__main__':
    main() 