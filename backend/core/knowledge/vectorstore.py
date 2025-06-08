#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ARIES - 向量存储模块
实现文档的向量化和检索功能
"""

import os
import json
import logging
import numpy as np
from typing import Dict, List, Any, Optional
from sentence_transformers import SentenceTransformer
import faiss
from ..database.db import Database

class VectorStore:
    """向量存储类，用于文档的向量化和检索"""
    
    def __init__(self, db: Database, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
        """初始化向量存储
        
        Args:
            db: 数据库实例
            model_name: 向量化模型名称
        """
        self.db = db
        self.model_name = model_name
        self.logger = logging.getLogger("aries_vectorstore")
        
        # 加载或创建向量索引
        self.documents = []
        self.document_embeddings = None
        self.index = None
        self._load_or_create_index()
        
        # 加载向量化模型
        try:
            self.model = SentenceTransformer(model_name)
            self.logger.info(f"已加载向量化模型: {model_name}")
        except Exception as e:
            self.logger.error(f"加载向量化模型失败: {str(e)}")
            raise
    
    def _load_or_create_index(self):
        """加载或创建向量索引"""
        try:
            # 从数据库加载文档
            docs = self.db.execute_query("SELECT * FROM vector_documents")
            
            if docs:
                # 创建空的文档嵌入数组
                dimension = 384  # MiniLM模型维度
                self.document_embeddings = np.zeros((len(docs), dimension), dtype=np.float32)
                
                # 加载文档和向量
                self.documents = []
                for i, doc in enumerate(docs):
                    self.documents.append({
                        'id': doc['id'],
                        'content': doc['content'],
                        'type': doc['type'],
                        'category': doc['category']
                    })
                    
                    # 如果有向量数据，加载它
                    if doc['embedding']:
                        self.document_embeddings[i] = np.frombuffer(doc['embedding'], dtype=np.float32)
                    else:
                        # 如果没有向量数据，生成它
                        embedding = self.model.encode([doc['content']])[0]
                        self.document_embeddings[i] = embedding
                        # 保存到数据库
                        self.db.execute_update("""
                            UPDATE vector_documents
                            SET embedding = ?, updated_at = CURRENT_TIMESTAMP
                            WHERE id = ?
                        """, (embedding.tobytes(), doc['id']))
                
                # 创建索引
                self.index = faiss.IndexFlatL2(dimension)
                self.index.add(self.document_embeddings)
                
                self.logger.info(f"已加载向量索引，包含 {len(self.documents)} 个文档")
            else:
                # 创建新的空索引
                self._create_empty_index()
                # 添加一些基础运维知识文档
                self._add_base_documents()
                
        except Exception as e:
            self.logger.error(f"加载向量索引失败: {str(e)}")
            self._create_empty_index()
            self._add_base_documents()
    
    def _create_empty_index(self, dimension: int = 384):
        """创建空的向量索引
        
        Args:
            dimension: 向量维度，默认384（MiniLM模型）
        """
        self.documents = []
        self.document_embeddings = np.zeros((0, dimension), dtype=np.float32)
        self.index = faiss.IndexFlatL2(dimension)
        self.logger.info("已创建新的空向量索引")
    
    def _add_base_documents(self):
        """添加基础运维知识文档"""
        base_docs = [
            {
                "id": "mysql_troubleshooting",
                "content": "MySQL常见问题排查：1. 检查MySQL是否运行：systemctl status mysql；2. 检查日志文件：/var/log/mysql/error.log；3. 检查连接问题：mysql -u root -p；4. 检查数据库性能：SHOW PROCESSLIST；5. 检查表状态：CHECK TABLE table_name；6. 修复表：REPAIR TABLE table_name；7. 检查磁盘空间：df -h；8. 优化表：OPTIMIZE TABLE table_name；9. 重启MySQL：systemctl restart mysql；10. 常见错误：连接拒绝、权限问题、表损坏、磁盘空间不足、内存不足、查询超时",
                "type": "knowledge",
                "category": "database"
            },
            {
                "id": "kubernetes_commands",
                "content": "Kubernetes常用命令：kubectl get pods（列出Pod）、kubectl get nodes（列出节点）、kubectl get deployments（列出部署）、kubectl get services（列出服务）、kubectl describe pod pod_name（查看Pod详情）、kubectl logs pod_name（查看Pod日志）、kubectl exec -it pod_name -- /bin/bash（进入Pod）、kubectl apply -f file.yaml（应用配置文件）、kubectl delete pod pod_name（删除Pod）、kubectl scale deployment deployment_name --replicas=3（扩展部署）、kubectl rollout status deployment/deployment_name（查看部署状态）、kubectl rollout undo deployment/deployment_name（回滚部署）",
                "type": "knowledge",
                "category": "kubernetes"
            },
            {
                "id": "network_troubleshooting",
                "content": "网络故障排查：1. 检查网络连接：ping、traceroute；2. 检查DNS解析：nslookup、dig；3. 检查端口连通性：telnet、nc；4. 检查网络接口：ifconfig、ip addr；5. 检查路由表：route、ip route；6. 检查防火墙规则：iptables -L；7. 检查网络流量：tcpdump、wireshark；8. 检查网络服务：netstat -tulpn；9. 检查网络配置文件：/etc/network/interfaces、/etc/sysconfig/network-scripts/；10. 常见问题：DNS解析失败、路由问题、防火墙阻止、网卡配置错误、IP冲突、网络拥塞",
                "type": "knowledge",
                "category": "network"
            },
            {
                "id": "disk_troubleshooting",
                "content": "磁盘故障排查：1. 检查磁盘使用情况：df -h；2. 检查磁盘IO：iostat；3. 检查文件系统：fsck；4. 检查磁盘健康状态：smartctl -a /dev/sda；5. 检查大文件：du -sh /*；6. 检查inode使用情况：df -i；7. 清理日志文件：find /var/log -type f -name \"*.log\" -exec truncate -s 0 {} \\;；8. 清理临时文件：rm -rf /tmp/*；9. 清理软件包缓存：apt clean或yum clean all；10. 常见问题：磁盘空间不足、inode耗尽、磁盘IO高、磁盘硬件故障、文件系统损坏",
                "type": "knowledge",
                "category": "storage"
            }
        ]
        
        # 添加文档到数据库
        doc_params = []
        for doc in base_docs:
            # 生成向量
            embedding = self.model.encode([doc['content']])[0]
            
            doc_params.append((
                doc['id'],
                doc['content'],
                doc['type'],
                doc['category'],
                embedding.tobytes()
            ))
        
        if doc_params:
            self.db.execute_many("""
                INSERT OR REPLACE INTO vector_documents (id, content, type, category, embedding)
                VALUES (?, ?, ?, ?, ?)
            """, doc_params)
        
        # 重新加载索引
        self._load_or_create_index()
    
    def add_document(self, doc_id: str, content: str, doc_type: str = None, category: str = None):
        """添加文档
        
        Args:
            doc_id: 文档ID
            content: 文档内容
            doc_type: 文档类型
            category: 文档类别
        """
        try:
            # 生成向量
            embedding = self.model.encode([content])[0]
            
            # 添加到数据库
            self.db.execute_update("""
                INSERT OR REPLACE INTO vector_documents (id, content, type, category, embedding)
                VALUES (?, ?, ?, ?, ?)
            """, (
                doc_id,
                content,
                doc_type,
                category,
                embedding.tobytes()
            ))
            
            # 更新内存中的索引
            if self.document_embeddings is None:
                self._create_empty_index()
            
            # 添加到文档列表
            self.documents.append({
                'id': doc_id,
                'content': content,
                'type': doc_type,
                'category': category
            })
            
            # 添加到向量数组
            self.document_embeddings = np.vstack([self.document_embeddings, embedding])
            
            # 更新索引
            self.index.add(np.array([embedding], dtype=np.float32))
            
            self.logger.info(f"已添加文档: {doc_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"添加文档失败: {str(e)}")
            return False
    
    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """搜索相关文档
        
        Args:
            query: 查询文本
            limit: 返回结果数量限制
            
        Returns:
            相关文档列表
        """
        if not self.documents or len(self.documents) == 0:
            return []
        
        try:
            # 生成查询向量
            query_embedding = self.model.encode([query])[0]
            query_embedding_np = np.array([query_embedding], dtype=np.float32)
            
            # 搜索最相似的文档
            limit = min(limit, len(self.documents))
            distances, indices = self.index.search(query_embedding_np, limit)
            
            # 构建结果
            results = []
            for i, idx in enumerate(indices[0]):
                if idx < len(self.documents):
                    doc = self.documents[idx].copy()
                    doc['score'] = float(1.0 - distances[0][i] / 100.0)  # 转换距离为相似度分数
                    results.append(doc)
            
            return results
        except Exception as e:
            self.logger.error(f"搜索文档失败: {str(e)}")
            return []
    
    def delete_document(self, doc_id: str) -> bool:
        """删除文档
        
        Args:
            doc_id: 文档ID
            
        Returns:
            是否删除成功
        """
        # FAISS不支持直接删除，需要重建索引
        try:
            # 查找文档索引
            idx_to_delete = None
            for i, doc in enumerate(self.documents):
                if doc.get('id') == doc_id:
                    idx_to_delete = i
                    break
            
            if idx_to_delete is None:
                self.logger.warning(f"未找到文档: {doc_id}")
                return False
            
            # 删除文档
            self.documents.pop(idx_to_delete)
            
            # 重建索引
            dimension = self.index.d
            new_index = faiss.IndexFlatL2(dimension)
            
            if len(self.documents) > 0:
                # 删除对应的嵌入向量
                mask = np.ones(len(self.document_embeddings), dtype=bool)
                mask[idx_to_delete] = False
                self.document_embeddings = self.document_embeddings[mask]
                
                # 添加剩余向量到新索引
                new_index.add(self.document_embeddings)
            
            self.index = new_index
            self.logger.info(f"已删除文档: {doc_id}")
            
            # 保存更新后的索引
            self._load_or_create_index()
            return True
        except Exception as e:
            self.logger.error(f"删除文档失败: {str(e)}")
            return False
    
    def update_document(self, doc_id: str, new_content: str) -> bool:
        """更新文档内容
        
        Args:
            doc_id: 文档ID
            new_content: 新文档内容
            
        Returns:
            是否更新成功
        """
        # 先删除再添加
        try:
            # 查找文档
            doc_to_update = None
            for doc in self.documents:
                if doc.get('id') == doc_id:
                    doc_to_update = doc.copy()
                    break
            
            if doc_to_update is None:
                self.logger.warning(f"未找到文档: {doc_id}")
                return False
            
            # 删除旧文档
            self.delete_document(doc_id)
            
            # 更新内容并添加新文档
            doc_to_update['content'] = new_content
            self.add_document(doc_id, new_content)
            
            self.logger.info(f"已更新文档: {doc_id}")
            return True
        except Exception as e:
            self.logger.error(f"更新文档失败: {str(e)}")
            return False
    
    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """获取文档
        
        Args:
            doc_id: 文档ID
            
        Returns:
            文档字典或None
        """
        for doc in self.documents:
            if doc.get('id') == doc_id:
                return doc.copy()
        return None
    
    def get_all_documents(self) -> List[Dict[str, Any]]:
        """获取所有文档
        
        Returns:
            文档列表
        """
        return [doc.copy() for doc in self.documents]
    
    def clear(self) -> bool:
        """清空向量存储
        
        Returns:
            是否清空成功
        """
        try:
            dimension = self.index.d
            self.documents = []
            self.document_embeddings = np.zeros((0, dimension), dtype=np.float32)
            self.index = faiss.IndexFlatL2(dimension)
            
            self._load_or_create_index()
            self.logger.info("已清空向量存储")
            return True
        except Exception as e:
            self.logger.error(f"清空向量存储失败: {str(e)}")
            return False