#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ARIES - 数据迁移模块
实现从文件系统到SQLite数据库的数据迁移
"""

import os
import json
import logging
import numpy as np
from typing import Dict, List, Any, Optional
from .db import Database

class DataMigration:
    """数据迁移类，用于将文件数据迁移到数据库"""
    
    def __init__(self, db: Database, kg_path: str, vector_db_path: str):
        """初始化数据迁移
        
        Args:
            db: 数据库实例
            kg_path: 知识图谱文件路径
            vector_db_path: 向量数据库路径
        """
        self.db = db
        self.kg_path = kg_path
        self.vector_db_path = vector_db_path
        self.logger = logging.getLogger("aries_migration")
    
    def migrate_kg(self) -> bool:
        """迁移知识图谱数据
        
        Returns:
            是否迁移成功
        """
        try:
            if not os.path.exists(self.kg_path):
                self.logger.warning(f"知识图谱文件不存在: {self.kg_path}")
                return False
            
            # 读取知识图谱数据
            with open(self.kg_path, 'r') as f:
                kg_data = json.load(f)
            
            # 迁移节点数据
            nodes = kg_data.get('nodes', [])
            node_params = []
            for node in nodes:
                node_params.append((
                    node['id'],
                    node.get('type', 'unknown'),
                    node.get('category'),
                    node.get('description'),
                    json.dumps(node.get('commands', []), ensure_ascii=False) if node.get('commands') else None
                ))
            
            if node_params:
                self.db.execute_many("""
                    INSERT OR REPLACE INTO kg_nodes (id, type, category, description, commands)
                    VALUES (?, ?, ?, ?, ?)
                """, node_params)
            
            # 迁移边数据
            edges = kg_data.get('links', [])
            edge_params = []
            for edge in edges:
                edge_params.append((
                    edge['source'],
                    edge['target'],
                    edge.get('weight', 0.5)
                ))
            
            if edge_params:
                self.db.execute_many("""
                    INSERT OR REPLACE INTO kg_edges (source, target, weight)
                    VALUES (?, ?, ?)
                """, edge_params)
            
            self.logger.info(f"知识图谱数据迁移完成，迁移了 {len(nodes)} 个节点和 {len(edges)} 条边")
            return True
            
        except Exception as e:
            self.logger.error(f"知识图谱数据迁移失败: {str(e)}")
            return False
    
    def migrate_vector_docs(self) -> bool:
        """迁移向量文档数据
        
        Returns:
            是否迁移成功
        """
        try:
            docs_path = os.path.join(self.vector_db_path, "documents.json")
            if not os.path.exists(docs_path):
                self.logger.warning(f"向量文档文件不存在: {docs_path}")
                return False
            
            # 读取文档数据
            with open(docs_path, 'r') as f:
                documents = json.load(f)
            
            # 迁移文档数据
            doc_params = []
            for doc in documents:
                # 将向量数据转换为二进制格式
                embedding = None
                if 'embedding' in doc:
                    embedding = np.array(doc['embedding'], dtype=np.float32).tobytes()
                
                doc_params.append((
                    doc['id'],
                    doc['content'],
                    doc.get('type'),
                    doc.get('category'),
                    embedding
                ))
            
            if doc_params:
                self.db.execute_many("""
                    INSERT OR REPLACE INTO vector_documents (id, content, type, category, embedding)
                    VALUES (?, ?, ?, ?, ?)
                """, doc_params)
            
            self.logger.info(f"向量文档数据迁移完成，迁移了 {len(documents)} 个文档")
            return True
            
        except Exception as e:
            self.logger.error(f"向量文档数据迁移失败: {str(e)}")
            return False
    
    def migrate_llm_prompts(self) -> bool:
        """迁移LLM提示词数据
        
        Returns:
            是否迁移成功
        """
        try:
            # 从RAG模块中提取默认提示词
            default_prompts = [
                {
                    "id": "fix_plan",
                    "name": "修复计划生成",
                    "system_message": """你是一个专业的系统运维专家，负责诊断和修复服务器问题。
请根据提供的服务器状态信息和问题描述，生成一个修复计划，包括具体的命令。
你的回答应该是JSON格式，包含以下字段：
1. diagnosis: 问题诊断
2. commands: 修复命令列表
3. explanation: 修复方案解释""",
                    "prompt_template": """## 服务器信息
服务器ID: {server_id}
服务器类型: {server_type}

## 问题描述
{problem_desc}

## 详细状态
{details}

## 历史失败次数
{history}

## 相关知识
{knowledge}

请生成一个修复计划，包括具体的命令。""",
                    "description": "生成服务器问题修复计划的提示词模板"
                },
                {
                    "id": "shell_command",
                    "name": "Shell命令生成",
                    "system_message": """你是一个{system_type}系统专家，精通Shell命令。
请根据用户的描述，生成一个准确的Shell命令。
你的回答应该是JSON格式，包含以下字段：
1. command: 完整的Shell命令
2. explanation: 命令的解释""",
                    "prompt_template": """## 系统类型
{system_type}

## 命令描述
{description}

## 相关知识
{knowledge}

请生成一个准确的Shell命令。""",
                    "description": "生成Shell命令的提示词模板"
                },
                {
                    "id": "task_plan",
                    "name": "任务计划生成",
                    "system_message": """你是一个专业的系统运维专家，负责规划和执行运维任务。
请根据提供的任务描述和可用服务器信息，生成一个任务执行计划，包括目标服务器和具体命令。
你的回答应该是JSON格式，包含以下字段：
1. target_servers: 目标服务器ID列表
2. commands: 执行命令列表
3. explanation: 任务计划解释""",
                    "prompt_template": """## 任务描述
{task_description}

## 可用服务器
{available_servers}

## 相关知识
{knowledge}

请生成一个任务执行计划，包括目标服务器和具体命令。""",
                    "description": "生成任务执行计划的提示词模板"
                }
            ]
            
            # 迁移提示词数据
            prompt_params = []
            for prompt in default_prompts:
                prompt_params.append((
                    prompt['id'],
                    prompt['name'],
                    prompt['system_message'],
                    prompt['prompt_template'],
                    prompt['description']
                ))
            
            if prompt_params:
                self.db.execute_many("""
                    INSERT OR REPLACE INTO llm_prompts (id, name, system_message, prompt_template, description)
                    VALUES (?, ?, ?, ?, ?)
                """, prompt_params)
            
            self.logger.info(f"LLM提示词数据迁移完成，迁移了 {len(default_prompts)} 个提示词模板")
            return True
            
        except Exception as e:
            self.logger.error(f"LLM提示词数据迁移失败: {str(e)}")
            return False
    
    def migrate_all(self) -> bool:
        """迁移所有数据
        
        Returns:
            是否全部迁移成功
        """
        kg_success = self.migrate_kg()
        vector_success = self.migrate_vector_docs()
        prompt_success = self.migrate_llm_prompts()
        
        return kg_success and vector_success and prompt_success 