#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ARIES - 知识图谱模块
实现知识图谱的构建和查询功能
"""

import os
import json
import logging
import networkx as nx
from typing import Dict, List, Any, Optional
from ..database.db import Database

class KnowledgeGraph:
    """知识图谱类，用于构建和查询运维知识"""
    
    def __init__(self, db: Database):
        """初始化知识图谱
        
        Args:
            db: 数据库实例
        """
        self.db = db
        self.logger = logging.getLogger("aries_kg")
        
        # 加载知识图谱
        self._load_graph()
    
    def _load_graph(self):
        """从数据库加载知识图谱"""
        try:
            # 创建图实例
            self.graph = nx.DiGraph()
            
            # 加载节点
            nodes = self.db.execute_query("SELECT * FROM kg_nodes")
            for node in nodes:
                # 将JSON字符串转换回列表
                commands = json.loads(node['commands']) if node['commands'] else []
                self.graph.add_node(
                    node['id'],
                    type=node['type'],
                    category=node['category'],
                    description=node['description'],
                    commands=commands
                )
            
            # 加载边
            edges = self.db.execute_query("SELECT * FROM kg_edges")
            for edge in edges:
                self.graph.add_edge(
                    edge['source'],
                    edge['target'],
                    weight=edge['weight']
                )
            
            self.logger.info(f"已从数据库加载知识图谱，包含 {len(nodes)} 个节点和 {len(edges)} 条边")
            
            # 如果没有数据，创建基础知识
            if len(nodes) == 0:
                self._create_base_knowledge()
                
        except Exception as e:
            self.logger.error(f"加载知识图谱失败: {str(e)}")
            # 创建新图谱
            self.graph = nx.DiGraph()
            self._create_base_knowledge()
    
    def _create_base_knowledge(self):
        """创建基础知识"""
        # 添加一些基础的运维知识节点和关系
        # 服务类型节点
        services = [
            {"id": "nginx", "type": "service", "category": "web_server"},
            {"id": "apache", "type": "service", "category": "web_server"},
            {"id": "mysql", "type": "service", "category": "database"},
            {"id": "postgresql", "type": "service", "category": "database"},
            {"id": "redis", "type": "service", "category": "cache"},
            {"id": "mongodb", "type": "service", "category": "database"},
            {"id": "kubernetes", "type": "service", "category": "container_orchestration"},
            {"id": "docker", "type": "service", "category": "container"}
        ]
        
        # 问题类型节点
        problems = [
            {"id": "high_cpu", "type": "problem", "category": "performance"},
            {"id": "high_memory", "type": "problem", "category": "performance"},
            {"id": "disk_full", "type": "problem", "category": "storage"},
            {"id": "service_down", "type": "problem", "category": "availability"},
            {"id": "network_latency", "type": "problem", "category": "network"},
            {"id": "connection_refused", "type": "problem", "category": "network"}
        ]
        
        # 解决方案节点
        solutions = [
            {
                "id": "restart_service", 
                "type": "solution", 
                "description": "重启服务",
                "commands": ["systemctl restart {service}"]
            },
            {
                "id": "clear_cache", 
                "type": "solution", 
                "description": "清理缓存",
                "commands": ["echo 3 > /proc/sys/vm/drop_caches"]
            },
            {
                "id": "clean_logs", 
                "type": "solution", 
                "description": "清理日志文件",
                "commands": ["find /var/log -type f -name \"*.log\" -exec truncate -s 0 {} \\;"]
            },
            {
                "id": "check_process", 
                "type": "solution", 
                "description": "检查进程状态",
                "commands": ["ps aux | grep {service}"]
            }
        ]
        
        # 添加节点到数据库
        node_params = []
        for service in services:
            node_params.append((
                service['id'],
                service['type'],
                service['category'],
                None,
                None
            ))
        
        for problem in problems:
            node_params.append((
                problem['id'],
                problem['type'],
                problem['category'],
                None,
                None
            ))
        
        for solution in solutions:
            node_params.append((
                solution['id'],
                solution['type'],
                None,
                solution['description'],
                json.dumps(solution['commands'], ensure_ascii=False)
            ))
        
        if node_params:
            self.db.execute_many("""
                INSERT OR REPLACE INTO kg_nodes (id, type, category, description, commands)
                VALUES (?, ?, ?, ?, ?)
            """, node_params)
        
        # 添加边到数据库
        # 服务与问题的关系
        relations = [
            ("nginx", "high_cpu", 0.7),
            ("nginx", "service_down", 0.9),
            ("mysql", "high_memory", 0.8),
            ("mysql", "disk_full", 0.6),
            ("redis", "high_memory", 0.7),
            ("kubernetes", "service_down", 0.8),
            ("docker", "high_cpu", 0.6)
        ]
        
        # 问题与解决方案的关系
        problem_solutions = [
            ("high_cpu", "restart_service", 0.6),
            ("high_cpu", "check_process", 0.8),
            ("high_memory", "clear_cache", 0.9),
            ("disk_full", "clean_logs", 0.8),
            ("service_down", "restart_service", 0.9),
            ("service_down", "check_process", 0.7)
        ]
        
        edge_params = [(src, dst, weight) for src, dst, weight in relations + problem_solutions]
        
        if edge_params:
            self.db.execute_many("""
                INSERT OR REPLACE INTO kg_edges (source, target, weight)
                VALUES (?, ?, ?)
            """, edge_params)
        
        # 重新加载图
        self._load_graph()
    
    def add_node(self, node_id: str, **attributes):
        """添加节点
        
        Args:
            node_id: 节点ID
            **attributes: 节点属性
        """
        # 添加到图
        self.graph.add_node(node_id, **attributes)
        
        # 添加到数据库
        commands = json.dumps(attributes.get('commands', []), ensure_ascii=False) if attributes.get('commands') else None
        self.db.execute_update("""
            INSERT OR REPLACE INTO kg_nodes (id, type, category, description, commands)
            VALUES (?, ?, ?, ?, ?)
        """, (
            node_id,
            attributes.get('type', 'unknown'),
            attributes.get('category'),
            attributes.get('description'),
            commands
        ))
        
        self.logger.info(f"已添加节点: {node_id}")
    
    def add_edge(self, source: str, target: str, **attributes):
        """添加边（关系）
        
        Args:
            source: 源节点ID
            target: 目标节点ID
            **attributes: 边属性
        """
        # 添加到图
        self.graph.add_edge(source, target, **attributes)
        
        # 添加到数据库
        self.db.execute_update("""
            INSERT OR REPLACE INTO kg_edges (source, target, weight)
            VALUES (?, ?, ?)
        """, (
            source,
            target,
            attributes.get('weight', 0.5)
        ))
        
        self.logger.info(f"已添加边: {source} -> {target}")
    
    def get_node(self, node_id: str) -> Dict[str, Any]:
        """获取节点信息
        
        Args:
            node_id: 节点ID
            
        Returns:
            节点属性字典
        """
        if node_id in self.graph.nodes:
            return dict(self.graph.nodes[node_id])
        return {}
    
    def get_neighbors(self, node_id: str) -> List[Dict[str, Any]]:
        """获取节点的邻居
        
        Args:
            node_id: 节点ID
            
        Returns:
            邻居节点列表
        """
        if node_id not in self.graph.nodes:
            return []
        
        neighbors = []
        for neighbor in self.graph.neighbors(node_id):
            node_data = dict(self.graph.nodes[neighbor])
            edge_data = dict(self.graph.edges[node_id, neighbor])
            neighbors.append({
                "id": neighbor,
                **node_data,
                "edge": edge_data
            })
        
        return neighbors
    
    def find_path(self, source: str, target: str) -> List[str]:
        """查找从源节点到目标节点的路径
        
        Args:
            source: 源节点ID
            target: 目标节点ID
            
        Returns:
            路径节点ID列表
        """
        try:
            path = nx.shortest_path(self.graph, source=source, target=target)
            return path
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return []
    
    def find_solutions(self, problem: str) -> List[Dict[str, Any]]:
        """查找问题的解决方案
        
        Args:
            problem: 问题节点ID
            
        Returns:
            解决方案列表
        """
        solutions = []
        
        if problem not in self.graph.nodes:
            return solutions
        
        # 查找与问题直接相连的解决方案
        for neighbor in self.graph.neighbors(problem):
            node_data = dict(self.graph.nodes[neighbor])
            if node_data.get("type") == "solution":
                edge_data = dict(self.graph.edges[problem, neighbor])
                solutions.append({
                    "id": neighbor,
                    **node_data,
                    "relevance": edge_data.get("weight", 0.5)
                })
        
        # 按相关性排序
        solutions.sort(key=lambda x: x.get("relevance", 0), reverse=True)
        
        return solutions
    
    def update_from_experience(self, problem: str, solution: str, success: bool, context: Dict[str, Any]):
        """根据经验更新知识图谱
        
        Args:
            problem: 问题节点ID
            solution: 解决方案节点ID
            success: 解决方案是否成功
            context: 上下文信息
        """
        # 确保节点存在
        if problem not in self.graph.nodes:
            self.add_node(problem, type="problem", category=context.get("category", "unknown"))
        
        if solution not in self.graph.nodes:
            self.add_node(solution, type="solution", description=context.get("description", ""))
        
        # 更新或添加边
        if self.graph.has_edge(problem, solution):
            # 更新权重
            current_weight = self.graph.edges[problem, solution].get("weight", 0.5)
            if success:
                # 成功则增加权重
                new_weight = min(1.0, current_weight + 0.1)
            else:
                # 失败则减少权重
                new_weight = max(0.1, current_weight - 0.1)
            
            # 更新图中的边
            self.graph.edges[problem, solution]["weight"] = new_weight
            
            # 更新数据库中的边
            self.db.execute_update("""
                UPDATE kg_edges
                SET weight = ?, updated_at = CURRENT_TIMESTAMP
                WHERE source = ? AND target = ?
            """, (new_weight, problem, solution))
            
            self.logger.info(f"已更新边权重: {problem} -> {solution}, 新权重: {new_weight}")
        else:
            # 添加新边
            initial_weight = 0.6 if success else 0.3
            self.add_edge(problem, solution, weight=initial_weight)