#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ARIES - 知识图谱测试模块
测试知识图谱的功能
"""

import pytest
import json
from ..core.knowledge.kg import KnowledgeGraph

def test_kg_initialization(test_kg: KnowledgeGraph):
    """测试知识图谱初始化"""
    # 检查基础知识是否创建
    nodes = test_kg.db.execute_query("SELECT * FROM kg_nodes")
    edges = test_kg.db.execute_query("SELECT * FROM kg_edges")
    
    assert len(nodes) > 0, "基础知识节点未创建"
    assert len(edges) > 0, "基础知识边未创建"

def test_kg_add_node(test_kg: KnowledgeGraph):
    """测试添加节点"""
    # 添加测试节点
    test_kg.add_node(
        "test_service",
        type="service",
        category="test",
        description="测试服务节点"
    )
    
    # 验证节点
    node = test_kg.get_node("test_service")
    assert node["type"] == "service", "节点类型错误"
    assert node["category"] == "test", "节点类别错误"
    assert node["description"] == "测试服务节点", "节点描述错误"

def test_kg_add_edge(test_kg: KnowledgeGraph):
    """测试添加边"""
    # 添加测试节点
    test_kg.add_node("test_problem", type="problem", category="test")
    test_kg.add_node("test_solution", type="solution", category="test")
    
    # 添加边
    test_kg.add_edge("test_problem", "test_solution", weight=0.8)
    
    # 验证边
    neighbors = test_kg.get_neighbors("test_problem")
    assert len(neighbors) == 1, "边添加失败"
    assert neighbors[0]["id"] == "test_solution", "边目标节点错误"
    assert neighbors[0]["edge"]["weight"] == 0.8, "边权重错误"

def test_kg_find_path(test_kg: KnowledgeGraph):
    """测试路径查找"""
    # 添加测试路径
    test_kg.add_node("start", type="service", category="test")
    test_kg.add_node("middle", type="problem", category="test")
    test_kg.add_node("end", type="solution", category="test")
    
    test_kg.add_edge("start", "middle", weight=0.7)
    test_kg.add_edge("middle", "end", weight=0.8)
    
    # 查找路径
    path = test_kg.find_path("start", "end")
    assert len(path) == 3, "路径查找失败"
    assert path[0] == "start", "路径起点错误"
    assert path[1] == "middle", "路径中间点错误"
    assert path[2] == "end", "路径终点错误"

def test_kg_find_solutions(test_kg: KnowledgeGraph):
    """测试解决方案查找"""
    # 添加测试问题和解
    test_kg.add_node("test_problem", type="problem", category="test")
    test_kg.add_node("solution1", type="solution", category="test", description="解决方案1")
    test_kg.add_node("solution2", type="solution", category="test", description="解决方案2")
    
    test_kg.add_edge("test_problem", "solution1", weight=0.9)
    test_kg.add_edge("test_problem", "solution2", weight=0.7)
    
    # 查找解决方案
    solutions = test_kg.find_solutions("test_problem")
    assert len(solutions) == 2, "解决方案查找失败"
    assert solutions[0]["id"] == "solution1", "解决方案排序错误"
    assert solutions[0]["relevance"] == 0.9, "解决方案相关性错误"

def test_kg_update_from_experience(test_kg: KnowledgeGraph):
    """测试经验更新"""
    # 添加测试问题和解
    test_kg.add_node("test_problem", type="problem", category="test")
    test_kg.add_node("test_solution", type="solution", category="test")
    
    # 添加初始边
    test_kg.add_edge("test_problem", "test_solution", weight=0.5)
    
    # 更新经验（成功案例）
    test_kg.update_from_experience(
        "test_problem",
        "test_solution",
        success=True,
        context={"category": "test"}
    )
    
    # 验证权重更新
    neighbors = test_kg.get_neighbors("test_problem")
    assert neighbors[0]["edge"]["weight"] == 0.6, "成功经验更新失败"
    
    # 更新经验（失败案例）
    test_kg.update_from_experience(
        "test_problem",
        "test_solution",
        success=False,
        context={"category": "test"}
    )
    
    # 验证权重更新
    neighbors = test_kg.get_neighbors("test_problem")
    assert neighbors[0]["edge"]["weight"] == 0.5, "失败经验更新失败"

def test_kg_commands(test_kg: KnowledgeGraph):
    """测试命令管理"""
    # 添加带命令的解决方案
    commands = ["echo 'test1'", "echo 'test2'"]
    test_kg.add_node(
        "test_solution",
        type="solution",
        category="test",
        description="测试解决方案",
        commands=commands
    )
    
    # 验证命令
    node = test_kg.get_node("test_solution")
    assert "commands" in node, "命令未保存"
    assert len(node["commands"]) == 2, "命令数量错误"
    assert node["commands"][0] == "echo 'test1'", "命令内容错误" 