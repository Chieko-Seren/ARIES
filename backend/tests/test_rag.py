#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ARIES - RAG测试模块
测试RAG的功能
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from ..core.knowledge.rag import RAG

def test_rag_initialization(test_rag: RAG):
    """测试RAG初始化"""
    assert test_rag.vector_store is not None, "向量存储未初始化"
    assert test_rag.db is not None, "数据库未初始化"
    assert test_rag.llm_config is not None, "LLM配置未初始化"

def test_get_prompt_template(test_rag: RAG):
    """测试获取提示词模板"""
    # 获取修复计划模板
    template = test_rag._get_prompt_template("fix_plan")
    assert template is not None, "未找到修复计划模板"
    assert "prompt_template" in template, "模板缺少提示词"
    assert "system_message" in template, "模板缺少系统消息"
    
    # 获取不存在的模板
    template = test_rag._get_prompt_template("non_existent_template")
    assert template is None, "不存在的模板返回了结果"

@patch('openai.ChatCompletion.create')
def test_generate_fix_plan(mock_openai, test_rag: RAG, mock_llm_response):
    """测试生成修复计划"""
    # 设置模拟响应
    mock_openai.return_value = mock_llm_response
    
    # 测试上下文
    context = {
        "server": {
            "id": "test_server",
            "type": "linux"
        },
        "status": {
            "message": "CPU使用率过高",
            "details": {
                "cpu_usage": 95,
                "memory_usage": 60
            }
        },
        "history": "最近发生过类似问题"
    }
    
    # 生成修复计划
    plan = test_rag.generate_fix_plan(context)
    
    # 验证结果
    assert "diagnosis" in plan, "修复计划缺少诊断"
    assert "commands" in plan, "修复计划缺少命令"
    assert "explanation" in plan, "修复计划缺少解释"
    assert len(plan["commands"]) > 0, "修复计划命令为空"

@patch('openai.ChatCompletion.create')
def test_generate_shell_command(mock_openai, test_rag: RAG, mock_llm_response):
    """测试生成Shell命令"""
    # 设置模拟响应
    mock_openai.return_value = mock_llm_response
    
    # 测试上下文
    context = {
        "system_type": "linux",
        "description": "查看系统负载"
    }
    
    # 生成命令
    command_info = test_rag.generate_shell_command(context)
    
    # 验证结果
    assert "command" in command_info, "命令信息缺少命令"
    assert "explanation" in command_info, "命令信息缺少解释"

@patch('openai.ChatCompletion.create')
def test_generate_task_plan(mock_openai, test_rag: RAG, mock_llm_response):
    """测试生成任务计划"""
    # 设置模拟响应
    mock_openai.return_value = mock_llm_response
    
    # 测试上下文
    context = {
        "task_description": "在所有服务器上更新系统",
        "available_servers": [
            {
                "id": "server1",
                "name": "Web服务器",
                "ip": "192.168.1.100",
                "type": "linux"
            },
            {
                "id": "server2",
                "name": "数据库服务器",
                "ip": "192.168.1.101",
                "type": "linux"
            }
        ]
    }
    
    # 生成任务计划
    plan = test_rag.generate_task_plan(context)
    
    # 验证结果
    assert "target_servers" in plan, "任务计划缺少目标服务器"
    assert "commands" in plan, "任务计划缺少命令"
    assert "explanation" in plan, "任务计划缺少解释"

@patch('openai.ChatCompletion.create')
def test_analyze_data(mock_openai, test_rag: RAG, mock_llm_response):
    """测试数据分析"""
    # 设置模拟响应
    mock_openai.return_value = mock_llm_response
    
    # 测试上下文
    context = {
        "query": "分析系统性能问题",
        "data": {
            "cpu_usage": [60, 70, 80, 90, 95],
            "memory_usage": [50, 55, 60, 65, 70],
            "disk_usage": [75, 76, 77, 78, 79]
        }
    }
    
    # 分析数据
    analysis = test_rag.analyze_data(context)
    
    # 验证结果
    assert "analysis" in analysis, "分析结果缺少分析"
    assert "insights" in analysis, "分析结果缺少见解"
    assert "recommendations" in analysis, "分析结果缺少建议"

@patch('openai.ChatCompletion.create')
def test_generate_kube_plan(mock_openai, test_rag: RAG, mock_llm_response):
    """测试生成Kubernetes操作计划"""
    # 设置模拟响应
    mock_openai.return_value = mock_llm_response
    
    # 测试上下文
    context = {
        "description": "扩展Web服务部署",
        "current_state": {
            "deployments": [
                {
                    "name": "web-app",
                    "replicas": 2,
                    "available": 2
                }
            ]
        }
    }
    
    # 生成Kubernetes计划
    plan = test_rag.generate_kube_plan(context)
    
    # 验证结果
    assert "operations" in plan, "Kubernetes计划缺少操作"
    assert "explanation" in plan, "Kubernetes计划缺少解释"

@patch('openai.ChatCompletion.create')
def test_generate_network_plan(mock_openai, test_rag: RAG, mock_llm_response):
    """测试生成网络操作计划"""
    # 设置模拟响应
    mock_openai.return_value = mock_llm_response
    
    # 测试上下文
    context = {
        "description": "配置负载均衡",
        "topology": {
            "servers": [
                {
                    "id": "web1",
                    "ip": "192.168.1.100",
                    "role": "web"
                },
                {
                    "id": "web2",
                    "ip": "192.168.1.101",
                    "role": "web"
                }
            ],
            "load_balancer": {
                "id": "lb1",
                "ip": "192.168.1.1"
            }
        }
    }
    
    # 生成网络计划
    plan = test_rag.generate_network_plan(context)
    
    # 验证结果
    assert "operations" in plan, "网络计划缺少操作"
    assert "explanation" in plan, "网络计划缺少解释"

def test_error_handling(test_rag: RAG):
    """测试错误处理"""
    # 测试无效的提示词模板
    with pytest.raises(ValueError):
        test_rag.generate_fix_plan({
            "server": {"id": "test"},
            "status": {"message": "test"},
            "history": "test"
        })
    
    # 测试无效的上下文
    with pytest.raises(KeyError):
        test_rag.generate_shell_command({})
    
    # 测试无效的LLM配置
    test_rag.llm_config["api_key"] = "invalid_key"
    with pytest.raises(Exception):
        test_rag._call_llm("test prompt", "test system message") 