#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ARIES - RAG模块
实现检索增强生成功能，结合向量存储和LLM进行智能推理
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
import requests
from ..database.db import Database

class RAG:
    """检索增强生成类，用于智能推理"""
    
    def __init__(self, vector_store, db: Database, llm_config: Dict[str, Any]):
        """初始化RAG
        
        Args:
            vector_store: 向量存储实例
            db: 数据库实例
            llm_config: LLM配置
        """
        self.vector_store = vector_store
        self.db = db
        self.llm_config = llm_config
        self.logger = logging.getLogger("aries_rag")
    
    def _get_prompt_template(self, prompt_id: str) -> Dict[str, Any]:
        """获取提示词模板
        
        Args:
            prompt_id: 提示词ID
            
        Returns:
            提示词模板信息
        """
        try:
            result = self.db.execute_query(
                "SELECT * FROM llm_prompts WHERE id = ?",
                (prompt_id,)
            )
            if result:
                return dict(result[0])
            else:
                self.logger.error(f"未找到提示词模板: {prompt_id}")
                return None
        except Exception as e:
            self.logger.error(f"获取提示词模板失败: {str(e)}")
            return None
    
    def _call_llm(self, prompt: str, system_message: str = None) -> Dict[str, Any]:
        """调用LLM API
        
        Args:
            prompt: 提示词
            system_message: 系统消息
            
        Returns:
            LLM响应
        """
        try:
            provider = self.llm_config.get("provider", "openai").lower()
            
            if provider == "openai":
                return self._call_openai(prompt, system_message)
            else:
                raise ValueError(f"不支持的LLM提供商: {provider}")
                
        except Exception as e:
            self.logger.error(f"调用LLM失败: {str(e)}")
            raise
    
    def _call_openai(self, prompt: str, system_message: str = None) -> Dict[str, Any]:
        """调用OpenAI API
        
        Args:
            prompt: 提示词
            system_message: 系统消息
            
        Returns:
            OpenAI响应
        """
        import openai
        
        openai.api_key = self.llm_config.get("api_key")
        
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        
        messages.append({"role": "user", "content": prompt})
        
        response = openai.ChatCompletion.create(
            model=self.llm_config.get("model", "gpt-4"),
            messages=messages,
            temperature=self.llm_config.get("temperature", 0.1),
            max_tokens=self.llm_config.get("max_tokens", 2000),
            top_p=self.llm_config.get("top_p", 1),
            frequency_penalty=self.llm_config.get("frequency_penalty", 0),
            presence_penalty=self.llm_config.get("presence_penalty", 0)
        )
        
        return response
    
    def generate_fix_plan(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """生成修复计划
        
        Args:
            context: 上下文信息，包含服务器和状态信息
            
        Returns:
            修复计划
        """
        # 获取相关文档
        server_type = context["server"].get("type", "linux")
        problem_desc = context["status"].get("message", "")
        details = context["status"].get("details", {})
        
        query = f"服务器问题: {problem_desc}, 服务器类型: {server_type}"
        relevant_docs = self.vector_store.search(query, limit=5)
        
        # 获取提示词模板
        prompt_template = self._get_prompt_template("fix_plan")
        if not prompt_template:
            raise ValueError("未找到修复计划提示词模板")
        
        # 构建提示词
        prompt = prompt_template["prompt_template"].format(
            server_id=context['server'].get('id'),
            server_type=server_type,
            problem_desc=problem_desc,
            details=json.dumps(details, indent=2),
            history=context['history'],
            knowledge=' '.join([doc['content'] for doc in relevant_docs])
        )
        
        # 调用LLM
        response = self._call_llm(prompt, prompt_template["system_message"])
        
        # 解析响应
        try:
            content = response['choices'][0]['message']['content']
            # 提取JSON部分
            if '{' in content and '}' in content:
                json_str = content[content.find('{'):content.rfind('}')+1]
                plan = json.loads(json_str)
            else:
                # 如果没有找到JSON，尝试解析整个内容
                plan = json.loads(content)
                
            return plan
        except Exception as e:
            self.logger.error(f"解析LLM响应失败: {str(e)}")
            # 返回一个基本的计划
            return {
                "diagnosis": "无法解析LLM响应",
                "commands": ["echo '无法生成修复命令'"],
                "explanation": "生成修复计划时出错"
            }
    
    def generate_shell_command(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """生成Shell命令
        
        Args:
            context: 上下文信息，包含系统类型和命令描述
            
        Returns:
            Shell命令信息
        """
        system_type = context["system_type"].lower()
        description = context["description"]
        
        # 获取相关文档
        query = f"系统类型: {system_type}, 命令: {description}"
        relevant_docs = self.vector_store.search(query, limit=3)
        
        # 获取提示词模板
        prompt_template = self._get_prompt_template("shell_command")
        if not prompt_template:
            raise ValueError("未找到Shell命令提示词模板")
        
        # 构建提示词
        prompt = prompt_template["prompt_template"].format(
            system_type=system_type,
            description=description,
            knowledge=' '.join([doc['content'] for doc in relevant_docs])
        )
        
        # 调用LLM
        response = self._call_llm(
            prompt,
            prompt_template["system_message"].format(system_type=system_type)
        )
        
        # 解析响应
        try:
            content = response['choices'][0]['message']['content']
            # 提取JSON部分
            if '{' in content and '}' in content:
                json_str = content[content.find('{'):content.rfind('}')+1]
                command_info = json.loads(json_str)
            else:
                # 如果没有找到JSON，尝试解析整个内容
                command_info = json.loads(content)
                
            return command_info
        except Exception as e:
            self.logger.error(f"解析LLM响应失败: {str(e)}")
            # 返回一个基本的命令信息
            return {
                "command": "echo '无法生成命令'",
                "explanation": "生成命令时出错"
            }
    
    def generate_task_plan(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """生成任务执行计划
        
        Args:
            context: 上下文信息，包含任务描述和可用服务器
            
        Returns:
            任务执行计划
        """
        task_description = context["task_description"]
        available_servers = context["available_servers"]
        
        # 获取相关文档
        query = f"运维任务: {task_description}"
        relevant_docs = self.vector_store.search(query, limit=5)
        
        # 获取提示词模板
        prompt_template = self._get_prompt_template("task_plan")
        if not prompt_template:
            raise ValueError("未找到任务计划提示词模板")
        
        # 构建提示词
        prompt = prompt_template["prompt_template"].format(
            task_description=task_description,
            available_servers=json.dumps([{
                "id": s["id"],
                "name": s.get("name", s["id"]),
                "ip": s["ip"],
                "type": s.get("type", "linux")
            } for s in available_servers], indent=2),
            knowledge=' '.join([doc['content'] for doc in relevant_docs])
        )
        
        # 调用LLM
        response = self._call_llm(prompt, prompt_template["system_message"])
        
        # 解析响应
        try:
            content = response['choices'][0]['message']['content']
            # 提取JSON部分
            if '{' in content and '}' in content:
                json_str = content[content.find('{'):content.rfind('}')+1]
                plan = json.loads(json_str)
            else:
                # 如果没有找到JSON，尝试解析整个内容
                plan = json.loads(content)
                
            return plan
        except Exception as e:
            self.logger.error(f"解析LLM响应失败: {str(e)}")
            # 返回一个基本的计划
            return {
                "target_servers": [],
                "commands": ["echo '无法生成任务命令'"],
                "explanation": "生成任务计划时出错"
            }
    
    def analyze_data(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """分析系统数据
        
        Args:
            context: 上下文信息，包含查询和数据
            
        Returns:
            分析结果
        """
        query = context["query"]
        data = context["data"]
        
        # 获取提示词模板
        prompt_template = self._get_prompt_template("data_analysis")
        if not prompt_template:
            # 使用默认提示词
            system_message = """你是一个专业的数据分析师，精通系统运维数据分析。
请根据提供的系统数据和查询，进行专业的分析并给出见解。
你的回答应该是JSON格式，包含以下字段：
1. analysis: 数据分析结果
2. insights: 关键见解列表
3. recommendations: 建议列表"""
            
            prompt = f"""## 查询
{query}

## 系统数据
{json.dumps(data, indent=2)}

请对数据进行专业分析，并给出见解和建议。"""
        else:
            system_message = prompt_template["system_message"]
            prompt = prompt_template["prompt_template"].format(
                query=query,
                data=json.dumps(data, indent=2)
            )
        
        # 调用LLM
        response = self._call_llm(prompt, system_message)
        
        # 解析响应
        try:
            content = response['choices'][0]['message']['content']
            # 提取JSON部分
            if '{' in content and '}' in content:
                json_str = content[content.find('{'):content.rfind('}')+1]
                analysis = json.loads(json_str)
            else:
                # 如果没有找到JSON，尝试解析整个内容
                analysis = json.loads(content)
                
            return analysis
        except Exception as e:
            self.logger.error(f"解析LLM响应失败: {str(e)}")
            # 返回一个基本的分析结果
            return {
                "analysis": "无法解析LLM响应",
                "insights": ["分析数据时出错"],
                "recommendations": ["请检查LLM配置和连接"]
            }
    
    def generate_kube_plan(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """生成Kubernetes操作计划
        
        Args:
            context: 上下文信息，包含任务描述和当前集群状态
            
        Returns:
            Kubernetes操作计划
        """
        description = context["description"]
        current_state = context["current_state"]
        
        # 获取相关文档
        query = f"Kubernetes任务: {description}"
        relevant_docs = self.vector_store.search(query, limit=5)
        
        # 获取提示词模板
        prompt_template = self._get_prompt_template("kube_plan")
        if not prompt_template:
            # 使用默认提示词
            system_message = """你是一个Kubernetes专家，精通集群管理和操作。
请根据提供的任务描述和当前集群状态，生成一个Kubernetes操作计划。
你的回答应该是JSON格式，包含以下字段：
1. operations: 操作列表，每个操作包含type和params
2. explanation: 操作计划解释"""
            
            prompt = f"""## 任务描述
{description}

## 当前集群状态
{json.dumps(current_state, indent=2)}

## 相关知识
{' '.join([doc['content'] for doc in relevant_docs])}

请生成一个Kubernetes操作计划。"""
        else:
            system_message = prompt_template["system_message"]
            prompt = prompt_template["prompt_template"].format(
                description=description,
                current_state=json.dumps(current_state, indent=2),
                knowledge=' '.join([doc['content'] for doc in relevant_docs])
            )
        
        # 调用LLM
        response = self._call_llm(prompt, system_message)
        
        # 解析响应
        try:
            content = response['choices'][0]['message']['content']
            # 提取JSON部分
            if '{' in content and '}' in content:
                json_str = content[content.find('{'):content.rfind('}')+1]
                plan = json.loads(json_str)
            else:
                # 如果没有找到JSON，尝试解析整个内容
                plan = json.loads(content)
                
            return plan
        except Exception as e:
            self.logger.error(f"解析LLM响应失败: {str(e)}")
            # 返回一个基本的计划
            return {
                "operations": [],
                "explanation": "生成Kubernetes操作计划时出错"
            }
    
    def generate_network_plan(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """生成网络操作计划
        
        Args:
            context: 上下文信息，包含任务描述和网络拓扑
            
        Returns:
            网络操作计划
        """
        description = context["description"]
        topology = context["topology"]
        
        # 获取相关文档
        query = f"网络任务: {description}"
        relevant_docs = self.vector_store.search(query, limit=5)
        
        # 获取提示词模板
        prompt_template = self._get_prompt_template("network_plan")
        if not prompt_template:
            # 使用默认提示词
            system_message = """你是一个网络工程师，精通网络配置和故障排除。
请根据提供的任务描述和网络拓扑，生成一个网络操作计划。
你的回答应该是JSON格式，包含以下字段：
1. operations: 操作列表，每个操作包含type和params
2. explanation: 操作计划解释"""
            
            prompt = f"""## 任务描述
{description}

## 网络拓扑
{json.dumps(topology, indent=2)}

## 相关知识
{' '.join([doc['content'] for doc in relevant_docs])}

请生成一个网络操作计划。"""
        else:
            system_message = prompt_template["system_message"]
            prompt = prompt_template["prompt_template"].format(
                description=description,
                topology=json.dumps(topology, indent=2),
                knowledge=' '.join([doc['content'] for doc in relevant_docs])
            )
        
        # 调用LLM
        response = self._call_llm(prompt, system_message)
        
        # 解析响应
        try:
            content = response['choices'][0]['message']['content']
            # 提取JSON部分
            if '{' in content and '}' in content:
                json_str = content[content.find('{'):content.rfind('}')+1]
                plan = json.loads(json_str)
            else:
                # 如果没有找到JSON，尝试解析整个内容
                plan = json.loads(content)
                
            return plan
        except Exception as e:
            self.logger.error(f"解析LLM响应失败: {str(e)}")
            # 返回一个基本的计划
            return {
                "operations": [],
                "explanation": "生成网络操作计划时出错"
            }