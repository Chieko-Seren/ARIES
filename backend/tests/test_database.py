#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ARIES - 数据库测试模块
测试数据库的基本功能
"""

import pytest
from ..core.database.db import Database

def test_database_initialization(test_db: Database):
    """测试数据库初始化"""
    # 检查表是否存在
    tables = test_db.execute_query("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name IN ('kg_nodes', 'kg_edges', 'vector_documents', 'llm_prompts')
    """)
    assert len(tables) == 4, "数据库表创建失败"

def test_database_operations(test_db: Database):
    """测试数据库基本操作"""
    # 测试插入
    test_db.execute_update(
        "INSERT INTO kg_nodes (id, type, category) VALUES (?, ?, ?)",
        ("test_node", "test", "test_category")
    )
    
    # 测试查询
    result = test_db.execute_query(
        "SELECT * FROM kg_nodes WHERE id = ?",
        ("test_node",)
    )
    assert len(result) == 1, "插入数据查询失败"
    assert result[0]["type"] == "test", "插入数据类型错误"
    
    # 测试更新
    test_db.execute_update(
        "UPDATE kg_nodes SET category = ? WHERE id = ?",
        ("updated_category", "test_node")
    )
    
    result = test_db.execute_query(
        "SELECT * FROM kg_nodes WHERE id = ?",
        ("test_node",)
    )
    assert result[0]["category"] == "updated_category", "更新数据失败"
    
    # 测试批量操作
    test_data = [
        ("test_node1", "test", "category1"),
        ("test_node2", "test", "category2"),
        ("test_node3", "test", "category3")
    ]
    
    test_db.execute_many(
        "INSERT INTO kg_nodes (id, type, category) VALUES (?, ?, ?)",
        test_data
    )
    
    result = test_db.execute_query("SELECT * FROM kg_nodes WHERE type = 'test'")
    assert len(result) == 4, "批量插入数据失败"

def test_database_constraints(test_db: Database):
    """测试数据库约束"""
    # 测试主键约束
    with pytest.raises(Exception):
        test_db.execute_update(
            "INSERT INTO kg_nodes (id, type) VALUES (?, ?)",
            ("test_node", "test")  # 重复的主键
        )
    
    # 测试外键约束
    with pytest.raises(Exception):
        test_db.execute_update(
            "INSERT INTO kg_edges (source, target) VALUES (?, ?)",
            ("non_existent_node", "test_node")  # 不存在的源节点
        )

def test_database_transaction(test_db: Database):
    """测试数据库事务"""
    with test_db.get_connection() as conn:
        cursor = conn.cursor()
        try:
            # 开始事务
            cursor.execute("BEGIN TRANSACTION")
            
            # 执行多个操作
            cursor.execute(
                "INSERT INTO kg_nodes (id, type) VALUES (?, ?)",
                ("transaction_node1", "test")
            )
            cursor.execute(
                "INSERT INTO kg_nodes (id, type) VALUES (?, ?)",
                ("transaction_node2", "test")
            )
            
            # 提交事务
            conn.commit()
            
        except Exception:
            # 回滚事务
            conn.rollback()
            raise
    
    # 验证事务结果
    result = test_db.execute_query(
        "SELECT * FROM kg_nodes WHERE id IN (?, ?)",
        ("transaction_node1", "transaction_node2")
    )
    assert len(result) == 2, "事务提交失败" 