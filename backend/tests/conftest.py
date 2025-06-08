#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ARIES - 测试配置模块
提供测试环境和通用fixture
"""

import os
import pytest
import tempfile
import shutil
from typing import Generator, Dict, Any
from ..core.database.db import Database
from ..core.knowledge.kg import KnowledgeGraph
from ..core.knowledge.vectorstore import VectorStore
from ..core.knowledge.rag import RAG
from ..config.settings import Settings

@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """创建测试配置"""
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    
    # 修改配置
    settings = Settings(
        db_path=os.path.join(temp_dir, "test.db"),
        vector_db_path=os.path.join(temp_dir, "vector_store"),
        kg_path=os.path.join(temp_dir, "knowledge_graph"),
        log_dir=os.path.join(temp_dir, "logs"),
        servers_config_path=os.path.join(temp_dir, "servers.json"),
        debug=True
    )
    
    yield settings
    
    # 清理临时目录
    shutil.rmtree(temp_dir)

@pytest.fixture(scope="session")
def test_db(test_settings: Settings) -> Generator[Database, None, None]:
    """创建测试数据库"""
    db = Database(test_settings.db_path)
    yield db

@pytest.fixture(scope="session")
def test_kg(test_db: Database) -> Generator[KnowledgeGraph, None, None]:
    """创建测试知识图谱"""
    kg = KnowledgeGraph(test_db)
    yield kg

@pytest.fixture(scope="session")
def test_vector_store(test_db: Database) -> Generator[VectorStore, None, None]:
    """创建测试向量存储"""
    vector_store = VectorStore(test_db)
    yield vector_store

@pytest.fixture(scope="session")
def test_rag(test_vector_store: VectorStore, test_db: Database, test_settings: Settings) -> Generator[RAG, None, None]:
    """创建测试RAG实例"""
    # 使用测试LLM配置
    llm_config = {
        "provider": "openai",
        "api_key": os.getenv("TEST_OPENAI_API_KEY", "test_key"),
        "model": "gpt-3.5-turbo",  # 使用更便宜的模型进行测试
        "temperature": 0.1,
        "max_tokens": 1000
    }
    
    rag = RAG(test_vector_store, test_db, llm_config)
    yield rag

@pytest.fixture(scope="function")
def mock_llm_response() -> Dict[str, Any]:
    """模拟LLM响应"""
    return {
        "choices": [{
            "message": {
                "content": """{
                    "diagnosis": "测试诊断",
                    "commands": ["echo 'test'"],
                    "explanation": "测试解释"
                }"""
            }
        }]
    } 