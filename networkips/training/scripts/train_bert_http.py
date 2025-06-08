#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from transformers import BertTokenizer, BertModel, BertConfig
from sklearn.model_selection import train_test_split
import logging
from datetime import datetime
import numpy as np
from tqdm import tqdm

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bert_training.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class HTTPDataset(Dataset):
    def __init__(self, texts, labels, tokenizer, max_length=512):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        text = str(self.texts[idx])
        label = self.labels[idx]

        encoding = self.tokenizer(
            text,
            add_special_tokens=True,
            max_length=self.max_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )

        return {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'labels': torch.tensor(label, dtype=torch.long)
        }

class HTTPBertClassifier(nn.Module):
    def __init__(self, bert_model_name='bert-base-uncased', num_labels=2, dropout=0.1):
        super(HTTPBertClassifier, self).__init__()
        
        self.bert = BertModel.from_pretrained(bert_model_name)
        self.dropout = nn.Dropout(dropout)
        self.classifier = nn.Sequential(
            nn.Linear(self.bert.config.hidden_size, 256),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(256, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, num_labels)
        )
        
        # 冻结BERT参数
        for param in self.bert.parameters():
            param.requires_grad = False
        
        # 只训练最后几层
        for param in self.bert.encoder.layer[-4:].parameters():
            param.requires_grad = True

    def forward(self, input_ids, attention_mask):
        outputs = self.bert(
            input_ids=input_ids,
            attention_mask=attention_mask
        )
        
        pooled_output = outputs.pooler_output
        pooled_output = self.dropout(pooled_output)
        logits = self.classifier(pooled_output)
        
        return logits

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
        train_correct = 0
        train_total = 0
        
        progress_bar = tqdm(train_loader, desc=f'Epoch {epoch+1}/{num_epochs} [Train]')
        for batch in progress_bar:
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            labels = batch['labels'].to(device)
            
            optimizer.zero_grad()
            outputs = model(input_ids, attention_mask)
            loss = criterion(outputs, labels)
            
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item()
            
            _, predicted = torch.max(outputs.data, 1)
            train_total += labels.size(0)
            train_correct += (predicted == labels).sum().item()
            
            progress_bar.set_postfix({
                'loss': f'{loss.item():.4f}',
                'acc': f'{100.*train_correct/train_total:.2f}%'
            })
        
        avg_train_loss = train_loss / len(train_loader)
        train_accuracy = 100. * train_correct / train_total
        train_losses.append(avg_train_loss)
        
        # 验证阶段
        model.eval()
        val_loss = 0
        val_correct = 0
        val_total = 0
        
        with torch.no_grad():
            progress_bar = tqdm(val_loader, desc=f'Epoch {epoch+1}/{num_epochs} [Val]')
            for batch in progress_bar:
                input_ids = batch['input_ids'].to(device)
                attention_mask = batch['attention_mask'].to(device)
                labels = batch['labels'].to(device)
                
                outputs = model(input_ids, attention_mask)
                loss = criterion(outputs, labels)
                
                val_loss += loss.item()
                
                _, predicted = torch.max(outputs.data, 1)
                val_total += labels.size(0)
                val_correct += (predicted == labels).sum().item()
                
                progress_bar.set_postfix({
                    'loss': f'{loss.item():.4f}',
                    'acc': f'{100.*val_correct/val_total:.2f}%'
                })
        
        avg_val_loss = val_loss / len(val_loader)
        val_accuracy = 100. * val_correct / val_total
        val_losses.append(avg_val_loss)
        
        # 保存最佳模型
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'train_loss': train_losses,
                'val_loss': val_losses,
                'train_accuracy': train_accuracy,
                'val_accuracy': val_accuracy
            }, model_save_path)
        
        logging.info(f'Epoch {epoch+1}/{num_epochs}:')
        logging.info(f'Average Training Loss: {avg_train_loss:.4f}, Accuracy: {train_accuracy:.2f}%')
        logging.info(f'Average Validation Loss: {avg_val_loss:.4f}, Accuracy: {val_accuracy:.2f}%')
    
    return train_losses, val_losses

def load_data(data_dir):
    """加载HTTP请求数据"""
    texts = []
    labels = []
    
    # 遍历数据目录
    for root, _, files in os.walk(data_dir):
        for file in files:
            if file.endswith('.json'):
                with open(os.path.join(root, file), 'r') as f:
                    data = json.load(f)
                    texts.extend(data['requests'])
                    labels.extend(data['labels'])
    
    return texts, np.array(labels)

def main():
    # 配置参数
    data_dir = '../data/http'
    model_save_dir = '../models/bert_http'
    bert_model_name = 'bert-base-uncased'
    max_length = 512
    batch_size = 16
    num_epochs = 10
    learning_rate = 2e-5
    
    # 创建模型保存目录
    os.makedirs(model_save_dir, exist_ok=True)
    
    # 设置设备
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logging.info(f'使用设备: {device}')
    
    # 加载tokenizer
    tokenizer = BertTokenizer.from_pretrained(bert_model_name)
    
    # 加载数据
    logging.info('加载数据...')
    texts, labels = load_data(data_dir)
    
    # 划分训练集和验证集
    X_train, X_val, y_train, y_val = train_test_split(
        texts, labels, test_size=0.2, random_state=42, stratify=labels
    )
    
    # 创建数据集和数据加载器
    train_dataset = HTTPDataset(X_train, y_train, tokenizer, max_length)
    val_dataset = HTTPDataset(X_val, y_val, tokenizer, max_length)
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size)
    
    # 创建模型
    model = HTTPBertClassifier(bert_model_name).to(device)
    
    # 定义损失函数和优化器
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=learning_rate)
    
    # 训练模型
    logging.info('开始训练...')
    model_save_path = os.path.join(model_save_dir, 
                                 f'bert_http_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pt')
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