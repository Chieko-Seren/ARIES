#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ARIES - 网络分析器
实现网络拓扑分析和网络故障排查功能
"""

import os
import json
import logging
import subprocess
import networkx as nx
from typing import Dict, List, Any, Optional

class NetworkAnalyzer:
    """网络分析器类，用于网络拓扑分析和故障排查"""
    
    def __init__(self):
        """初始化网络分析器"""
        self.logger = logging.getLogger("aries_network")
        self.topology = nx.DiGraph()
    
    def get_topology(self) -> Dict[str, Any]:
        """获取网络拓扑
        
        Returns:
            网络拓扑信息
        """
        try:
            # 这里应该实现实际的网络拓扑发现逻辑
            # 简化实现，返回示例拓扑
            nodes = [
                {"id": "router1", "type": "router", "ip": "192.168.1.1"},
                {"id": "switch1", "type": "switch", "ip": "192.168.1.2"},
                {"id": "switch2", "type": "switch", "ip": "192.168.1.3"},
                {"id": "server1", "type": "server", "ip": "192.168.1.100"},
                {"id": "server2", "type": "server", "ip": "192.168.1.101"},
                {"id": "server3", "type": "server", "ip": "192.168.1.102"}
            ]
            
            links = [
                {"source": "router1", "target": "switch1"},
                {"source": "router1", "target": "switch2"},
                {"source": "switch1", "target": "server1"},
                {"source": "switch1", "target": "server2"},
                {"source": "switch2", "target": "server3"}
            ]
            
            # 构建拓扑图
            self.topology = nx.DiGraph()
            
            for node in nodes:
                self.topology.add_node(node["id"], **node)
            
            for link in links:
                self.topology.add_edge(link["source"], link["target"])
            
            # 转换为可序列化的字典
            topology_dict = {
                "nodes": nodes,
                "links": links
            }
            
            return topology_dict
            
        except Exception as e:
            self.logger.error(f"获取网络拓扑失败: {str(e)}")
            return {"nodes": [], "links": []}
    
    def analyze_path(self, source: str, destination: str) -> Dict[str, Any]:
        """分析网络路径
        
        Args:
            source: 源节点ID或IP
            destination: 目标节点ID或IP
            
        Returns:
            路径分析结果
        """
        try:
            # 确保拓扑已加载
            if len(self.topology) == 0:
                self.get_topology()
            
            # 查找节点
            source_node = self._find_node(source)
            destination_node = self._find_node(destination)
            
            if not source_node or not destination_node:
                return {
                    "success": False,
                    "error": "源节点或目标节点不存在"
                }
            
            # 查找最短路径
            try:
                path = nx.shortest_path(self.topology, source=source_node, target=destination_node)
                
                # 执行traceroute获取实际路径
                traceroute_result = self._execute_traceroute(destination_node)
                
                return {
                    "success": True,
                    "path": path,
                    "hop_count": len(path) - 1,
                    "traceroute": traceroute_result
                }
            except nx.NetworkXNoPath:
                return {
                    "success": False,
                    "error": "没有找到从源节点到目标节点的路径"
                }
                
        except Exception as e:
            self.logger.error(f"分析网络路径失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def test_connectivity(self, target: str, port: Optional[int] = None) -> Dict[str, Any]:
        """测试网络连通性
        
        Args:
            target: 目标节点ID或IP
            port: 可选的端口号
            
        Returns:
            连通性测试结果
        """
        try:
            # 查找节点
            target_node = self._find_node(target)
            target_ip = target
            
            if target_node:
                node_data = self.topology.nodes[target_node]
                target_ip = node_data.get("ip", target)
            
            # 执行ping测试
            ping_result = self._execute_ping(target_ip)
            
            # 如果指定了端口，执行端口连通性测试
            port_result = None
            if port:
                port_result = self._test_port(target_ip, port)
            
            return {
                "success": ping_result["success"],
                "target": target_ip,
                "ping": ping_result,
                "port": port_result
            }
                
        except Exception as e:
            self.logger.error(f"测试网络连通性失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _find_node(self, node_id_or_ip: str) -> Optional[str]:
        """查找节点
        
        Args:
            node_id_or_ip: 节点ID或IP
            
        Returns:
            节点ID或None
        """
        # 直接匹配节点ID
        if node_id_or_ip in self.topology.nodes:
            return node_id_or_ip
        
        # 匹配IP地址
        for node_id, node_data in self.topology.nodes(data=True):
            if node_data.get("ip") == node_id_or_ip:
                return node_id
        
        return None
    
    def _execute_ping(self, target: str) -> Dict[str, Any]:
        """执行ping测试
        
        Args:
            target: 目标IP
            
        Returns:
            ping测试结果
        """
        try:
            # 执行ping命令
            process = subprocess.Popen(
                ["ping", "-c", "4", target],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            stdout, stderr = process.communicate()
            exit_code = process.returncode
            
            if exit_code == 0:
                # 解析ping结果
                lines = stdout.strip().split('\n')
                stats_line = next((line for line in reversed(lines) if "packets transmitted" in line), "")
                rtt_line = next((line for line in reversed(lines) if "min/avg/max" in line), "")
                
                transmitted = 0
                received = 0
                loss = 100
                if stats_line:
                    parts = stats_line.split()
                    transmitted = int(parts[0])
                    received = int(parts[3])
                    loss = float(parts[5].strip('%'))
                
                min_rtt = 0
                avg_rtt = 0
                max_rtt = 0
                if rtt_line:
                    rtt_parts = rtt_line.split('=')[1].strip().split('/')
                    min_rtt = float(rtt_parts[0])
                    avg_rtt = float(rtt_parts[1])
                    max_rtt = float(rtt_parts[2].split()[0])
                
                return {
                    "success": True,
                    "transmitted": transmitted,
                    "received": received,
                    "loss": loss,
                    "min_rtt": min_rtt,
                    "avg_rtt": avg_rtt,
                    "max_rtt": max_rtt,
                    "output": stdout
                }
            else:
                return {
                    "success": False,
                    "error": stderr if stderr else f"Ping失败，退出码: {exit_code}",
                    "output": stdout
                }
                
        except Exception as e:
            self.logger.error(f"执行ping测试失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _execute_traceroute(self, target: str) -> Dict[str, Any]:
        """执行traceroute
        
        Args:
            target: 目标IP
            
        Returns:
            traceroute结果
        """
        try:
            # 执行traceroute命令
            process = subprocess.Popen(
                ["traceroute", "-n", target],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            stdout, stderr = process.communicate()
            exit_code = process.returncode
            
            if exit_code == 0:
                # 解析traceroute结果
                lines = stdout.strip().split('\n')[1:]  # 跳过标题行
                hops = []
                
                for line in lines:
                    parts = line.split()
                    hop_num = int(parts[0])
                    
                    # 提取IP地址和延迟
                    ip_addresses = []
                    rtts = []
                    
                    i = 1
                    while i < len(parts):
                        if parts[i] == '*':
                            ip_addresses.append(None)
                            rtts.append(None)
                            i += 1
                        else:
                            ip = parts[i]
                            ip_addresses.append(ip)
                            
                            # 尝试提取RTT
                            if i+1 < len(parts) and 'ms' in parts[i+1]:
                                rtts.append(float(parts[i+1].replace('ms', '')))
                                i += 2
                            else:
                                rtts.append(None)
                                i += 1
                    
                    hops.append({
                        "hop": hop_num,
                        "ip": ip_addresses[0] if ip_addresses else None,
                        "rtt": rtts[0] if rtts else None,
                        "all_ips": ip_addresses,
                        "all_rtts": rtts
                    })
                
                return {
                    "success": True,
                    "hops": hops,
                    "hop_count": len(hops),
                    "output": stdout
                }
            else:
                return {
                    "success": False,
                    "error": stderr if stderr else f"Traceroute失败，退出码: {exit_code}",
                    "output": stdout
                }
                
        except Exception as e:
            self.logger.error(f"执行traceroute失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _test_port(self, target: str, port: int) -> Dict[str, Any]:
        """测试端口连通性
        
        Args:
            target: 目标IP
            port: 端口号
            
        Returns:
            端口测试结果
        """
        try:
            # 使用nc命令测试端口
            process = subprocess.Popen(
                ["nc", "-z", "-v", "-w", "5", target, str(port)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            stdout, stderr = process.communicate()
            exit_code = process.returncode
            
            if exit_code == 0:
                return {
                    "success": True,
                    "port": port,
                    "open": True,
                    "output": stdout + stderr
                }
            else:
                return {
                    "success": True,
                    "port": port,
                    "open": False,
                    "output": stdout + stderr
                }
                
        except Exception as e:
            self.logger.error(f"测试端口连通性失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }