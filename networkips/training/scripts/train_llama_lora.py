#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from transformers import (
    LlamaTokenizer, 
    LlamaForCausalLM,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from peft import (
    prepare_model_for_kbit_training,
    LoraConfig,
    get_peft_model,
    TaskType
)
import logging
from datetime import datetime
import numpy as np
from tqdm import tqdm
import bitsandbytes as bnb
from accelerate import Accelerator

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('llama_training.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class SecurityReportDataset(Dataset):
    def __init__(self, texts, tokenizer, max_length=2048):
        self.texts = texts
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        text = str(self.texts[idx])
        
        # 构建提示模板
        prompt = f"""分析以下网络安全事件并提供详细报告：

事件描述：
{text}

请提供以下方面的分析：
1. 威胁等级评估
2. 攻击类型识别
3. 潜在影响分析
4. 建议的应对措施
5. 预防建议

分析报告："""

        # 编码文本
        encoding = self.tokenizer(
            prompt,
            add_special_tokens=True,
            max_length=self.max_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )

        return {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'labels': encoding['input_ids'].flatten()
        }

def prepare_model_and_tokenizer(model_name, use_4bit=True):
    """准备模型和分词器"""
    # 加载分词器
    tokenizer = LlamaTokenizer.from_pretrained(model_name)
    tokenizer.pad_token = tokenizer.eos_token
    
    # 配置量化参数
    if use_4bit:
        compute_dtype = torch.float16
        bnb_4bit_compute_dtype = "float16"
        bnb_4bit_use_double_quant = True
        bnb_4bit_quant_type = "nf4"
        
        # 加载模型
        model = LlamaForCausalLM.from_pretrained(
            model_name,
            load_in_4bit=True,
            torch_dtype=compute_dtype,
            device_map="auto",
            quantization_config={
                "load_in_4bit": True,
                "bnb_4bit_compute_dtype": bnb_4bit_compute_dtype,
                "bnb_4bit_use_double_quant": bnb_4bit_use_double_quant,
                "bnb_4bit_quant_type": bnb_4bit_quant_type
            }
        )
    else:
        model = LlamaForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16,
            device_map="auto"
        )
    
    # 准备模型进行训练
    model = prepare_model_for_kbit_training(model)
    
    return model, tokenizer

def create_peft_config():
    """创建PEFT配置"""
    return LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        inference_mode=False,
        r=8,  # LoRA秩
        lora_alpha=32,  # LoRA alpha参数
        lora_dropout=0.1,
        target_modules=["q_proj", "v_proj"]  # 目标模块
    )

def load_data(data_dir):
    """加载安全事件数据"""
    texts = []
    
    # 遍历数据目录
    for root, _, files in os.walk(data_dir):
        for file in files:
            if file.endswith('.json'):
                with open(os.path.join(root, file), 'r') as f:
                    data = json.load(f)
                    texts.extend(data['events'])
    
    return texts

class CustomTrainer(Trainer):
    def compute_loss(self, model, inputs, return_outputs=False):
        """自定义损失计算"""
        input_ids = inputs["input_ids"]
        attention_mask = inputs["attention_mask"]
        labels = inputs["labels"]
        
        outputs = model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            labels=labels
        )
        
        loss = outputs.loss
        
        if return_outputs:
            return loss, outputs
        return loss

def main():
    # 配置参数
    data_dir = '../data/security_events'
    model_save_dir = '../models/llama_lora'
    model_name = "meta-llama/Llama-2-70b-hf"  # 需要替换为实际的模型路径
    max_length = 2048
    batch_size = 4
    num_epochs = 3
    gradient_accumulation_steps = 4
    learning_rate = 2e-4
    
    # 创建模型保存目录
    os.makedirs(model_save_dir, exist_ok=True)
    
    # 设置设备
    accelerator = Accelerator()
    device = accelerator.device
    logging.info(f'使用设备: {device}')
    
    # 准备模型和分词器
    logging.info('加载模型和分词器...')
    model, tokenizer = prepare_model_and_tokenizer(model_name)
    
    # 创建PEFT配置
    peft_config = create_peft_config()
    model = get_peft_model(model, peft_config)
    
    # 加载数据
    logging.info('加载数据...')
    texts = load_data(data_dir)
    
    # 创建数据集
    dataset = SecurityReportDataset(texts, tokenizer, max_length)
    
    # 创建数据整理器
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False
    )
    
    # 配置训练参数
    training_args = TrainingArguments(
        output_dir=model_save_dir,
        num_train_epochs=num_epochs,
        per_device_train_batch_size=batch_size,
        gradient_accumulation_steps=gradient_accumulation_steps,
        learning_rate=learning_rate,
        fp16=True,
        logging_steps=10,
        save_strategy="epoch",
        save_total_limit=3,
        remove_unused_columns=False,
        report_to="tensorboard"
    )
    
    # 创建训练器
    trainer = CustomTrainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        data_collator=data_collator
    )
    
    # 训练模型
    logging.info('开始训练...')
    trainer.train()
    
    # 保存模型
    logging.info('保存模型...')
    model_save_path = os.path.join(model_save_dir, 
                                 f'llama_lora_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
    trainer.save_model(model_save_path)
    
    # 保存训练历史
    history = trainer.state.log_history
    history_path = os.path.join(model_save_dir, 'training_history.json')
    with open(history_path, 'w') as f:
        json.dump(history, f)
    
    logging.info('训练完成！')
    logging.info(f'模型已保存到: {model_save_path}')
    logging.info(f'训练历史已保存到: {history_path}')

if __name__ == '__main__':
    main() 