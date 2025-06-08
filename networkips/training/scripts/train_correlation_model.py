#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import logging
from datetime import datetime
from torch.nn import TransformerEncoder, TransformerEncoderLayer
import math

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('correlation_training.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class PositionalEncoding(nn.Module):
    def __init__(self, d_model, max_len=5000):
        super(PositionalEncoding, self).__init__()
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)
        self.register_buffer('pe', pe)

    def forward(self, x):
        return x + self.pe[:, :x.size(1)]

class SecurityEventCorrelationModel(nn.Module):
    def __init__(self, input_dim, d_model=256, nhead=8, num_layers=6, dim_feedforward=1024, dropout=0.1):
        super(SecurityEventCorrelationModel, self).__init__()
        
        self.input_projection = nn.Linear(input_dim, d_model)
        self.pos_encoder = PositionalEncoding(d_model)
        
        encoder_layers = TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            batch_first=True
        )
        self.transformer_encoder = TransformerEncoder(encoder_layers, num_layers)
        
        self.correlation_head = nn.Sequential(
            nn.Linear(d_model, 128),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, 1),
            nn.Sigmoid()
        )
        
        self.init_weights()
    
    def init_weights(self):
        initrange = 0.1
        self.input_projection.weight.data.uniform_(-initrange, initrange)
        self.correlation_head[0].weight.data.uniform_(-initrange, initrange)
        self.correlation_head[0].bias.data.zero_()
    
    def forward(self, src, src_mask=None):
        # src: [batch_size, seq_len, input_dim]
        src = self.input_projection(src)
        src = self.pos_encoder(src)
        
        if src_mask is None:
            src_mask = self.generate_square_subsequent_mask(src.size(1)).to(src.device)
        
        output = self.transformer_encoder(src, src_mask)
        
        # 使用序列的平均值进行相关性预测
        output = output.mean(dim=1)
        correlation_score = self.correlation_head(output)
        
        return correlation_score
    
    def generate_square_subsequent_mask(self, sz):
        mask = (torch.triu(torch.ones(sz, sz)) == 1).transpose(0, 1)
        mask = mask.float().masked_fill(mask == 0, float('-inf')).masked_fill(mask == 1, float(0.0))
        return mask

class SecurityEventDataset(Dataset):
    def __init__(self, features, labels, max_seq_len=100):
        self.features = torch.FloatTensor(features)
        self.labels = torch.FloatTensor(labels)
        self.max_seq_len = max_seq_len
        
        # 如果序列长度不足，进行填充
        if self.features.size(1) < max_seq_len:
            padding = torch.zeros(self.features.size(0), max_seq_len - self.features.size(1), 
                                self.features.size(2))
            self.features = torch.cat([self.features, padding], dim=1)
        # 如果序列长度过长，进行截断
        elif self.features.size(1) > max_seq_len:
            self.features = self.features[:, :max_seq_len, :]

    def __len__(self):
        return len(self.features)

    def __getitem__(self, idx):
        return self.features[idx], self.labels[idx]

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
            correlation_scores = model(batch_features)
            
            loss = criterion(correlation_scores, batch_labels.unsqueeze(1))
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
                
                correlation_scores = model(batch_features)
                loss = criterion(correlation_scores, batch_labels.unsqueeze(1))
                
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
    data_dir = '../data/correlation'
    model_save_dir = '../models/correlation'
    input_dim = 50  # 特征维度
    d_model = 256   # Transformer模型维度
    nhead = 8       # 注意力头数
    num_layers = 6  # Transformer层数
    batch_size = 32
    num_epochs = 100
    learning_rate = 0.0001
    
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
    features_scaled = scaler.fit_transform(features.reshape(-1, features.shape[-1])).reshape(features.shape)
    
    # 保存scaler
    scaler_path = os.path.join(model_save_dir, 'scaler.pkl')
    torch.save(scaler, scaler_path)
    
    # 划分训练集和验证集
    X_train, X_val, y_train, y_val = train_test_split(
        features_scaled, labels, test_size=0.2, random_state=42
    )
    
    # 创建数据加载器
    train_dataset = SecurityEventDataset(X_train, y_train)
    val_dataset = SecurityEventDataset(X_val, y_val)
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size)
    
    # 创建模型
    model = SecurityEventCorrelationModel(
        input_dim=input_dim,
        d_model=d_model,
        nhead=nhead,
        num_layers=num_layers
    ).to(device)
    
    # 定义损失函数和优化器
    criterion = nn.BCELoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)
    
    # 训练模型
    logging.info('开始训练...')
    model_save_path = os.path.join(model_save_dir, 
                                 f'correlation_model_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pt')
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