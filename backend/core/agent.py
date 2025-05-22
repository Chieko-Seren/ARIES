#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ARIES - Agent核心模块
实现基于KG和RAG的智能代理，具备监控、自动修复和远程操作功能
"""

import os
import time
import json
import logging
import requests
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

# 导入连接模块
from core.connectors.ssh import SSHConnector
from core.connectors.telnet import TelnetConnector
from core.connectors.shell import ShellConnector
from core.connectors.rj45 import RJ45Connector
from core.connectors.cisco_connector import CiscoConnector

# 导入知识库和推理模块
from core.knowledge.kg import KnowledgeGraph
from core.knowledge.rag import RAG
from core.knowledge.vectorstore import VectorStore

# 导入工具模块
from core.tools.web_search import WebSearch
from core.tools.network_analyzer import NetworkAnalyzer
from core.tools.kube_manager import KubeManager

class Agent:
    """ARIES智能代理核心类"""
    
    def __init__(self, settings):
        """初始化Agent
        
        Args:
            settings: 系统配置对象
        """
        self.settings = settings
        self.logger = self._setup_logger()
        
        # 初始化知识库组件
        self.vector_store = VectorStore(settings.vector_db_path)
        self.kg = KnowledgeGraph(settings.kg_path)
        self.rag = RAG(self.vector_store, settings.llm_config)
        
        # 初始化工具
        self.web_search = WebSearch(settings.search_api_key)
        self.network_analyzer = NetworkAnalyzer()
        self.kube_manager = KubeManager(settings.kube_config_path)
        
        # 加载服务器配置
        self.servers = self._load_servers()
        
        # 故障计数器
        self.failure_counters = {}
        
        self.logger.info("Agent初始化完成")
    
    def _setup_logger(self):
        """设置日志记录器"""
        logger = logging.getLogger("aries_agent")
        logger.setLevel(logging.INFO)
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 创建文件处理器
        file_handler = logging.FileHandler(os.path.join(self.settings.log_dir, "agent.log"))
        file_handler.setLevel(logging.INFO)
        
        # 创建格式化器
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        
        # 添加处理器到记录器
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        
        return logger
    
    def _load_servers(self) -> List[Dict[str, Any]]:
        """从配置文件加载服务器信息"""
        try:
            with open(self.settings.servers_config_path, 'r') as f:
                servers = json.load(f)
            self.logger.info(f"已加载{len(servers)}台服务器配置")
            return servers
        except Exception as e:
            self.logger.error(f"加载服务器配置失败: {str(e)}")
            return []
    
    def _get_connector(self, server):
        """根据服务器配置获取适当的连接器
        
        Args:
            server: 服务器配置信息
            
        Returns:
            连接器实例
        """
        conn_type = server.get("connection_type", "ssh").lower()
        
        if conn_type == "ssh":
            return SSHConnector(
                host=server["ip"],
                port=server.get("port", 22),
                username=server["username"],
                password=server.get("password"),
                key_file=server.get("key_file")
            )
        elif conn_type == "telnet":
            return TelnetConnector(
                host=server["ip"],
                port=server.get("port", 23),
                username=server.get("username"),
                password=server.get("password")
            )
        elif conn_type == "shell":
            return ShellConnector()
        elif conn_type == "rj45":
            return RJ45Connector(
                device_path=server.get("device_path"),
                baud_rate=server.get("baud_rate", 9600)
            )
        elif conn_type == "cisco_serial":
            return CiscoConnector(
                host=server.get("ip"), # May not be used directly for serial but good for consistency
                port=server["port"], # Serial port like /dev/ttyUSB0 or COM1
                username=server["username"],
                password=server["password"],
                device_type=server.get("device_type", "cisco_ios_serial")
            )
        else:
            raise ValueError(f"不支持的连接类型: {conn_type}")
    
    def monitor(self):
        """监控所有服务器状态"""
        self.logger.info("开始监控服务器状态")
        
        for server in self.servers:
            server_id = server["id"]
            try:
                # 检查服务器状态
                status = self._check_server_status(server)
                
                if not status["healthy"]:
                    self.logger.warning(f"服务器 {server_id} 状态异常: {status['message']}")
                    
                    # 增加失败计数
                    if server_id not in self.failure_counters:
                        self.failure_counters[server_id] = 0
                    self.failure_counters[server_id] += 1
                    
                    # 尝试自动修复
                    fixed = self._try_fix_server(server, status)
                    
                    # 如果修复失败且失败次数达到阈值，通知用户
                    if not fixed and self.failure_counters[server_id] >= 5:
                        self._notify_user(server, status)
                        self.logger.error(f"服务器 {server_id} 问题无法自动修复，已通知用户")
                else:
                    # 重置失败计数
                    self.failure_counters[server_id] = 0
                    self.logger.info(f"服务器 {server_id} 状态正常")
                    
            except Exception as e:
                self.logger.error(f"监控服务器 {server_id} 时出错: {str(e)}")
    
    def _check_server_status(self, server) -> Dict[str, Any]:
        """检查单个服务器的状态
        
        Args:
            server: 服务器配置信息
            
        Returns:
            状态信息字典
        """
        try:
            connector = self._get_connector(server)
            connector.connect()
            
            results = {}
            healthy = False
            message = ""

            if server.get("connection_type") == "cisco_serial":
                self.logger.info(f"Checking status for Cisco device: {server['id']}")
                # 对于Cisco设备，可以检查接口状态或配置的可达性
                if not hasattr(connector, 'connect') or not callable(getattr(connector, 'connect')):
                    healthy = False
                    message = "Connector does not have a callable connect method."
                    results["error"] = message
                    return {"healthy": healthy, "message": message, "details": results}

                # 确保 CiscoConnector 有 get_interfaces_status 方法
                if hasattr(connector, 'get_interfaces_status') and callable(getattr(connector, 'get_interfaces_status')):
                    interfaces_status = connector.get_interfaces_status()
                    if interfaces_status and "Error" not in str(interfaces_status) and "failed" not in str(interfaces_status).lower():
                        healthy = True
                        message = f"Successfully retrieved interface status."
                        results["interfaces_status"] = str(interfaces_status)[:200] + "..." if len(str(interfaces_status)) > 200 else str(interfaces_status)
                    else:
                        healthy = False
                        message = f"Failed to retrieve interface status or error in output: {str(interfaces_status)}"
                        results["interfaces_status"] = str(interfaces_status) if interfaces_status else "No output or connection failed"
                else:
                    healthy = False
                    message = "CiscoConnector does not have a get_interfaces_status method or it is not callable."
                    results["error"] = message
                
                # 也可以尝试获取部分配置作为健康检查的一部分，例如 uptime
                if hasattr(connector, 'send_command') and callable(getattr(connector, 'send_command')):
                    version_output = connector.send_command("show version | include uptime")
                    if version_output and "Error" not in str(version_output) and "failed" not in str(version_output).lower():
                        results["version_uptime"] = str(version_output)[:200] + "..." if len(str(version_output)) > 200 else str(version_output)
                        # 如果接口状态不好，但版本信息能获取，也可能认为设备是部分可达的
                        if not healthy and results["version_uptime"]:
                            message += " | Able to get version/uptime."
                    else:
                        results["version_uptime"] = f"Failed to get version/uptime: {str(version_output)}"
                        if not healthy:
                             message += " | Also failed to get version/uptime."
                else:
                    results["version_uptime"] = "CiscoConnector does not have a send_command method or it is not callable."

            else:
                # 原有的服务器状态检查逻辑
                expected_services = server.get("expected_services", [])
                
                # 检查CPU、内存、磁盘使用情况
                cpu_result = connector.execute("top -bn1 | grep 'Cpu(s)' | awk '{print $2 + $4}'")
                mem_result = connector.execute("free -m | awk 'NR==2{printf \"%s/%s (%.2f%%)\", $3,$2,$3*100/$2 }'")
                disk_result = connector.execute("df -h | awk '$NF==\"/\"{printf \"%s/%s (%s)\",$3,$2,$5}'")
                
                results["cpu"] = cpu_result.strip() if cpu_result else "Error fetching CPU"
                results["memory"] = mem_result.strip() if mem_result else "Error fetching Memory"
                results["disk"] = disk_result.strip() if disk_result else "Error fetching Disk"
                
                # 检查预期的服务是否运行
                services_status = {}
                if expected_services:
                    for service_name in expected_services:
                        service_result = connector.execute(f"systemctl is-active {service_name}")
                        services_status[service_name] = service_result.strip() == "active" if service_result else False
                    healthy = all(services_status.values())
                    message = "所有预期服务运行正常" if healthy else "部分预期服务未运行"
                else:
                    # 如果没有定义预期服务，且基本指标能获取，则认为健康
                    if results["cpu"] != "Error fetching CPU" and results["memory"] != "Error fetching Memory" and results["disk"] != "Error fetching Disk":
                        healthy = True
                        message = "基本指标获取正常，无特定服务检查。"
                    else:
                        healthy = False
                        message = "无法获取基本服务器指标。"
                
                results["services"] = services_status
            
            if hasattr(connector, 'disconnect') and callable(getattr(connector, 'disconnect')):
                connector.disconnect()
            
            return {"healthy": healthy, "message": message, "details": results}
            
        except Exception as e:
            return {
                "healthy": False,
                "message": f"连接或检查失败: {str(e)}",
                "details": {}
            }
    
    def _try_fix_server(self, server, status) -> bool:
        """尝试自动修复服务器问题
        
        Args:
            server: 服务器配置信息
            status: 服务器状态信息
            
        Returns:
            是否修复成功
        """
        try:
            self.logger.info(f"尝试修复服务器 {server['id']} 的问题")
            
            # 使用RAG获取修复方案
            context = {
                "server": server,
                "status": status,
                "history": self.failure_counters.get(server["id"], 0)
            }
            
            fix_plan = self.rag.generate_fix_plan(context)
            self.logger.info(f"生成修复方案: {fix_plan}")
            
            # 执行修复命令
            connector = self._get_connector(server)
            connector.connect()
            
            for cmd in fix_plan["commands"]:
                self.logger.info(f"执行修复命令: {cmd}")
                result = connector.execute(cmd)
                self.logger.info(f"命令执行结果: {result}")
            
            connector.disconnect()
            
            # 再次检查状态
            new_status = self._check_server_status(server)
            fixed = new_status["healthy"]
            
            if fixed:
                self.logger.info(f"服务器 {server['id']} 问题已修复")
            else:
                self.logger.warning(f"服务器 {server['id']} 问题修复失败")
            
            return fixed
            
        except Exception as e:
            self.logger.error(f"修复服务器 {server['id']} 时出错: {str(e)}")
            return False
    
    def _notify_user(self, server, status):
        """通过webhook通知用户服务器问题
        
        Args:
            server: 服务器配置信息
            status: 服务器状态信息
        """
        try:
            if not self.settings.webhook_url:
                self.logger.warning("未配置webhook URL，无法通知用户")
                return
                
            payload = {
                "event": "server_failure",
                "server_id": server["id"],
                "server_name": server.get("name", server["id"]),
                "ip": server["ip"],
                "status": status,
                "timestamp": datetime.now().isoformat(),
                "failure_count": self.failure_counters.get(server["id"], 0)
            }
            
            response = requests.post(
                self.settings.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                self.logger.info(f"已成功通知用户服务器 {server['id']} 的问题")
            else:
                self.logger.error(f"通知用户失败，HTTP状态码: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"发送通知时出错: {str(e)}")
    
    def execute_shell(self, system_type: str, description: str) -> Dict[str, Any]:
        """根据自然语言描述生成并执行shell命令
        
        Args:
            system_type: 系统类型（如linux, windows等）
            description: 命令的自然语言描述
            
        Returns:
            执行结果
        """
        try:
            # 使用RAG生成shell命令
            context = {
                "system_type": system_type,
                "description": description
            }
            
            command_info = self.rag.generate_shell_command(context)
            command = command_info["command"]
            
            # 本地执行命令
            connector = ShellConnector()
            result = connector.execute(command)
            
            return {
                "success": True,
                "command": command,
                "result": result,
                "explanation": command_info.get("explanation", "")
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def execute_task(self, task_description: str, server_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """执行自然语言描述的运维任务
        
        Args:
            task_description: 任务的自然语言描述
            server_ids: 可选的服务器ID列表，如果为None则根据任务自动选择
            
        Returns:
            执行结果
        """
        try:
            # 使用RAG理解任务并生成执行计划
            context = {
                "task_description": task_description,
                "available_servers": self.servers
            }
            
            task_plan = self.rag.generate_task_plan(context)
            
            # 确定目标服务器
            target_servers = []
            if server_ids:
                target_servers = [s for s in self.servers if s["id"] in server_ids]
            else:
                target_server_ids = task_plan.get("target_servers", [])
                target_servers = [s for s in self.servers if s["id"] in target_server_ids]
            
            if not target_servers:
                return {
                    "success": False,
                    "error": "未指定目标服务器且无法自动确定适用的服务器"
                }
            
            # 执行任务
            results = {}
            for server in target_servers:
                server_id = server["id"]
                try:
                    connector = self._get_connector(server)
                    connector.connect()
                    
                    server_results = []
                    for cmd in task_plan["commands"]:
                        result = connector.execute(cmd)
                        server_results.append({
                            "command": cmd,
                            "output": result
                        })
                    
                    connector.disconnect()
                    results[server_id] = {
                        "success": True,
                        "results": server_results
                    }
                    
                except Exception as e:
                    results[server_id] = {
                        "success": False,
                        "error": str(e)
                    }
            
            return {
                "success": True,
                "plan": task_plan,
                "results": results
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def analyze_statistics(self, query: str) -> Dict[str, Any]:
        """使用LLM分析系统数据
        
        Args:
            query: 分析查询
            
        Returns:
            分析结果
        """
        try:
            # 收集系统数据
            data = self._collect_system_data()
            
            # 使用RAG分析数据
            context = {
                "query": query,
                "data": data
            }
            
            analysis = self.rag.analyze_data(context)
            
            return {
                "success": True,
                "analysis": analysis,
                "data_summary": data.get("summary", {})
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _collect_system_data(self) -> Dict[str, Any]:
        """收集系统数据用于分析"""
        data = {
            "servers": {},
            "summary": {
                "total_servers": len(self.servers),
                "healthy_servers": 0,
                "unhealthy_servers": 0,
                "total_services": 0,
                "failed_services": 0
            }
        }
        
        for server in self.servers:
            server_id = server["id"]
            status = self._check_server_status(server)
            
            data["servers"][server_id] = {
                "config": server,
                "status": status,
                "failure_history": self.failure_counters.get(server_id, 0)
            }
            
            # 更新汇总信息
            if status["healthy"]:
                data["summary"]["healthy_servers"] += 1
            else:
                data["summary"]["unhealthy_servers"] += 1
            
            services = status.get("details", {}).get("services", {})
            data["summary"]["total_services"] += len(services)
            data["summary"]["failed_services"] += sum(1 for s in services.values() if not s)
        
        return data
    
    def get_recent_data(self, days: int = 7) -> Dict[str, Any]:
        """获取最近的系统数据
        
        Args:
            days: 获取最近几天的数据
            
        Returns:
            系统数据
        """
        # 这里应该从数据库或日志中获取历史数据
        # 简化实现，仅返回当前数据
        return self._collect_system_data()
    
    def manage_kubernetes(self, description: str) -> Dict[str, Any]:
        """根据自然语言描述执行Kubernetes管理任务
        
        Args:
            description: 任务的自然语言描述
            
        Returns:
            执行结果
        """
        try:
            # 使用RAG生成Kubernetes操作计划
            context = {
                "description": description,
                "current_state": self.kube_manager.get_cluster_state()
            }
            
            kube_plan = self.rag.generate_kube_plan(context)
            
            # 执行Kubernetes操作
            results = []
            for operation in kube_plan["operations"]:
                op_type = operation["type"]
                params = operation["params"]
                
                if op_type == "create":
                    result = self.kube_manager.create_resource(params["kind"], params["spec"])
                elif op_type == "update":
                    result = self.kube_manager.update_resource(params["kind"], params["name"], params["spec"])
                elif op_type == "delete":
                    result = self.kube_manager.delete_resource(params["kind"], params["name"])
                elif op_type == "get":
                    result = self.kube_manager.get_resource(params["kind"], params["name"])
                elif op_type == "exec":
                    result = self.kube_manager.exec_command(params["pod"], params["command"])
                else:
                    result = {"error": f"不支持的操作类型: {op_type}"}
                
                results.append({
                    "operation": operation,
                    "result": result
                })
            
            return {
                "success": True,
                "plan": kube_plan,
                "results": results
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def manage_network(self, description: str) -> Dict[str, Any]:
        """根据自然语言描述执行网络管理任务
        
        Args:
            description: 任务的自然语言描述
            
        Returns:
            执行结果
        """
        try:
            # 获取网络拓扑
            topology = self.network_analyzer.get_topology()
            
            # 使用RAG生成网络操作计划
            context = {
                "description": description,
                "topology": topology
            }
            
            network_plan = self.rag.generate_network_plan(context)
            
            # 执行网络操作
            results = []
            for operation in network_plan["operations"]:
                op_type = operation["type"]
                params = operation["params"]
                
                if op_type == "analyze":
                    result = self.network_analyzer.analyze_path(params["source"], params["destination"])
                elif op_type == "test":
                    result = self.network_analyzer.test_connectivity(params["target"], params.get("port"))
                elif op_type == "configure":
                    result = self._configure_network_device(params["device"], params["commands"])
                else:
                    result = {"error": f"不支持的操作类型: {op_type}"}
                
                results.append({
                    "operation": operation,
                    "result": result
                })
            
            return {
                "success": True,
                "plan": network_plan,
                "results": results
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _configure_network_device(self, device_id, commands):
        """配置网络设备
        
        Args:
            device_id: 设备ID
            commands: 配置命令列表
            
        Returns:
            配置结果
        """
        # 查找设备配置
        device = next((s for s in self.servers if s["id"] == device_id), None)
        if not device:
            return {"error": f"未找到设备: {device_id}"}
        
        try:
            connector = self._get_connector(device)
            connector.connect()
            
            results = []
            for cmd in commands:
                result = connector.execute(cmd)
                results.append({
                    "command": cmd,
                    "output": result
                })
            
            connector.disconnect()
            return {"success": True, "results": results}
            
        except Exception as e:
            return {"error": str(e)}