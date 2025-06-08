#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ARIES - 向量存储测试模块
测试向量存储的功能
"""

import pytest
import numpy as np
from ..core.knowledge.vectorstore import VectorStore

def test_vectorstore_initialization(test_vector_store: VectorStore):
    """测试向量存储初始化"""
    # 检查基础文档是否创建
    docs = test_vector_store.get_all_documents()
    assert len(docs) > 0, "基础文档未创建"
    
    # 检查向量索引
    assert test_vector_store.index is not None, "向量索引未创建"
    assert test_vector_store.document_embeddings is not None, "文档向量未创建"

def test_vectorstore_add_document(test_vector_store: VectorStore):
    """测试添加文档"""
    # 添加测试文档
    doc_id = "test_doc"
    content = "这是一个测试文档，用于测试向量存储功能。"
    test_vector_store.add_document(
        doc_id=doc_id,
        content=content,
        doc_type="test",
        category="test"
    )
    
    # 验证文档
    doc = test_vector_store.get_document(doc_id)
    assert doc is not None, "文档添加失败"
    assert doc["content"] == content, "文档内容错误"
    assert doc["type"] == "test", "文档类型错误"
    assert doc["category"] == "test", "文档类别错误"

def test_vectorstore_search(test_vector_store: VectorStore):
    """测试文档搜索"""
    # 添加测试文档
    test_docs = [
        {
            "id": "doc1",
            "content": "MySQL数据库性能优化指南",
            "type": "guide",
            "category": "database"
        },
        {
            "id": "doc2",
            "content": "Linux系统性能监控方法",
            "type": "guide",
            "category": "system"
        },
        {
            "id": "doc3",
            "content": "网络故障排查步骤",
            "type": "guide",
            "category": "network"
        }
    ]
    
    for doc in test_docs:
        test_vector_store.add_document(**doc)
    
    # 测试搜索
    results = test_vector_store.search("数据库性能问题", limit=2)
    assert len(results) > 0, "搜索返回空结果"
    assert results[0]["id"] == "doc1", "搜索结果排序错误"
    assert "score" in results[0], "搜索结果缺少相似度分数"

def test_vectorstore_update_document(test_vector_store: VectorStore):
    """测试更新文档"""
    # 添加测试文档
    doc_id = "update_test_doc"
    original_content = "原始文档内容"
    test_vector_store.add_document(
        doc_id=doc_id,
        content=original_content,
        doc_type="test",
        category="test"
    )
    
    # 更新文档
    new_content = "更新后的文档内容"
    test_vector_store.update_document(doc_id, new_content)
    
    # 验证更新
    doc = test_vector_store.get_document(doc_id)
    assert doc["content"] == new_content, "文档更新失败"
    
    # 验证搜索
    results = test_vector_store.search(new_content)
    assert len(results) > 0, "更新后搜索失败"
    assert results[0]["id"] == doc_id, "更新后搜索结果错误"

def test_vectorstore_delete_document(test_vector_store: VectorStore):
    """测试删除文档"""
    # 添加测试文档
    doc_id = "delete_test_doc"
    test_vector_store.add_document(
        doc_id=doc_id,
        content="要删除的文档",
        doc_type="test",
        category="test"
    )
    
    # 删除文档
    success = test_vector_store.delete_document(doc_id)
    assert success, "文档删除失败"
    
    # 验证删除
    doc = test_vector_store.get_document(doc_id)
    assert doc is None, "文档未完全删除"
    
    # 验证搜索
    results = test_vector_store.search("要删除的文档")
    assert len(results) == 0, "删除后仍能搜索到文档"

def test_vectorstore_clear(test_vector_store: VectorStore):
    """测试清空存储"""
    # 添加一些测试文档
    for i in range(3):
        test_vector_store.add_document(
            doc_id=f"clear_test_doc_{i}",
            content=f"测试文档 {i}",
            doc_type="test",
            category="test"
        )
    
    # 清空存储
    success = test_vector_store.clear()
    assert success, "清空存储失败"
    
    # 验证清空
    docs = test_vector_store.get_all_documents()
    assert len(docs) == 0, "存储未完全清空"
    
    # 验证索引
    assert test_vector_store.index.ntotal == 0, "向量索引未清空"

def test_vectorstore_embedding_consistency(test_vector_store: VectorStore):
    """测试向量一致性"""
    # 添加测试文档
    doc_id = "embedding_test_doc"
    content = "测试向量一致性的文档"
    test_vector_store.add_document(
        doc_id=doc_id,
        content=content,
        doc_type="test",
        category="test"
    )
    
    # 获取文档
    doc = test_vector_store.get_document(doc_id)
    
    # 重新加载存储
    test_vector_store._load_or_create_index()
    
    # 验证向量一致性
    new_doc = test_vector_store.get_document(doc_id)
    assert new_doc is not None, "重新加载后文档丢失"
    
    # 搜索验证
    results = test_vector_store.search(content)
    assert len(results) > 0, "重新加载后搜索失败"
    assert results[0]["id"] == doc_id, "重新加载后搜索结果错误" 