#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ARIES - Kubernetes管理器
实现Kubernetes集群管理和操作功能
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from kubernetes import client, config

class KubeManager:
    """Kubernetes管理器类，用于集群管理和操作"""
    
    SUPPORTED_RESOURCES = {
        "pod": "core_api",
        "service": "core_api",
        "deployment": "apps_api",
        "namespace": "core_api",
        "configmap": "core_api",
        "secret": "core_api",
        "ingress": "networking_api",
        "daemonset": "apps_api",
        "statefulset": "apps_api",
        "job": "batch_api",
        "cronjob": "batch_api"
    }
    
    def __init__(self, config_path: str):
        """初始化Kubernetes管理器
        
        Args:
            config_path: kubeconfig文件路径
        """
        self.logger = logging.getLogger(__name__)
        self.config_path = config_path
        self._init_clients()
    
    def _init_clients(self):
        """初始化Kubernetes客户端"""
        try:
            # 加载Kubernetes配置
            if os.path.exists(self.config_path):
                config.load_kube_config(config_file=self.config_path)
                self.logger.info(f"已加载Kubernetes配置: {self.config_path}")
            else:
                # 尝试使用默认配置
                config.load_kube_config()
                self.logger.info("已加载默认Kubernetes配置")
                
            # 初始化客户端
            self.core_api = client.CoreV1Api()
            self.apps_api = client.AppsV1Api()
            self.batch_api = client.BatchV1Api()
            self.networking_api = client.NetworkingV1Api()
            
        except Exception as e:
            self.logger.error(f"加载Kubernetes配置失败: {str(e)}")
            raise
    
    def _validate_resource_type(self, kind: str) -> Tuple[bool, str]:
        """验证资源类型是否支持
        
        Args:
            kind: 资源类型
            
        Returns:
            (是否支持, 错误信息)
        """
        kind_lower = kind.lower()
        if kind_lower not in self.SUPPORTED_RESOURCES:
            return False, f"不支持的资源类型: {kind}，支持的资源类型: {', '.join(self.SUPPORTED_RESOURCES.keys())}"
        return True, ""
    
    def get_cluster_state(self) -> Dict[str, Any]:
        """获取集群状态
        
        Returns:
            集群状态信息
        """
        try:
            # 获取节点信息
            nodes = self.core_api.list_node()
            node_info = []
            for node in nodes.items:
                node_status = {
                    "name": node.metadata.name,
                    "status": self._get_node_status(node),
                    "roles": self._get_node_roles(node),
                    "version": node.status.node_info.kubelet_version,
                    "internal_ip": self._get_node_internal_ip(node),
                    "external_ip": self._get_node_external_ip(node),
                    "pods": self._get_pods_on_node(node.metadata.name)
                }
                node_info.append(node_status)
            
            # 获取命名空间信息
            namespaces = self.core_api.list_namespace()
            namespace_info = []
            for ns in namespaces.items:
                namespace_status = {
                    "name": ns.metadata.name,
                    "status": ns.status.phase,
                    "age": self._get_resource_age(ns.metadata.creation_timestamp)
                }
                namespace_info.append(namespace_status)
            
            # 获取Pod信息
            pods = self.core_api.list_pod_for_all_namespaces()
            pod_info = []
            for pod in pods.items:
                pod_status = {
                    "name": pod.metadata.name,
                    "namespace": pod.metadata.namespace,
                    "status": pod.status.phase,
                    "node": pod.spec.node_name,
                    "ip": pod.status.pod_ip,
                    "age": self._get_resource_age(pod.metadata.creation_timestamp)
                }
                pod_info.append(pod_status)
            
            # 获取服务信息
            services = self.core_api.list_service_for_all_namespaces()
            service_info = []
            for svc in services.items:
                service_status = {
                    "name": svc.metadata.name,
                    "namespace": svc.metadata.namespace,
                    "type": svc.spec.type,
                    "cluster_ip": svc.spec.cluster_ip,
                    "external_ip": svc.spec.external_i_ps if hasattr(svc.spec, "external_i_ps") else None,
                    "ports": self._get_service_ports(svc),
                    "age": self._get_resource_age(svc.metadata.creation_timestamp)
                }
                service_info.append(service_status)
            
            # 获取部署信息
            deployments = self.apps_api.list_deployment_for_all_namespaces()
            deployment_info = []
            for deploy in deployments.items:
                deployment_status = {
                    "name": deploy.metadata.name,
                    "namespace": deploy.metadata.namespace,
                    "replicas": deploy.spec.replicas,
                    "available": deploy.status.available_replicas,
                    "age": self._get_resource_age(deploy.metadata.creation_timestamp)
                }
                deployment_info.append(deployment_status)
            
            return {
                "nodes": node_info,
                "namespaces": namespace_info,
                "pods": pod_info,
                "services": service_info,
                "deployments": deployment_info
            }
            
        except Exception as e:
            self.logger.error(f"获取集群状态失败: {str(e)}")
            return {
                "error": str(e)
            }
    
    def _get_node_status(self, node):
        """获取节点状态"""
        for condition in node.status.conditions:
            if condition.type == "Ready":
                return "Ready" if condition.status == "True" else "NotReady"
        return "Unknown"
    
    def _get_node_roles(self, node):
        """获取节点角色"""
        roles = []
        labels = node.metadata.labels
        for label in labels:
            if label.startswith("node-role.kubernetes.io/"):
                role = label.split("/")[1]
                roles.append(role)
        return roles if roles else ["worker"]
    
    def _get_node_internal_ip(self, node):
        """获取节点内部IP"""
        for address in node.status.addresses:
            if address.type == "InternalIP":
                return address.address
        return None
    
    def _get_node_external_ip(self, node):
        """获取节点外部IP"""
        for address in node.status.addresses:
            if address.type == "ExternalIP":
                return address.address
        return None
    
    def _get_pods_on_node(self, node_name):
        """获取节点上的Pod数量"""
        pods = self.core_api.list_pod_for_all_namespaces(field_selector=f"spec.nodeName={node_name}")
        return len(pods.items)
    
    def _get_resource_age(self, creation_timestamp):
        """计算资源年龄"""
        if not creation_timestamp:
            return "Unknown"
        
        import datetime
        now = datetime.datetime.now(datetime.timezone.utc)
        age = now - creation_timestamp
        
        days = age.days
        hours, remainder = divmod(age.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        
        if days > 0:
            return f"{days}d{hours}h"
        elif hours > 0:
            return f"{hours}h{minutes}m"
        else:
            return f"{minutes}m"
    
    def _get_service_ports(self, service):
        """获取服务端口信息"""
        ports = []
        for port in service.spec.ports:
            port_info = {
                "name": port.name,
                "port": port.port,
                "target_port": port.target_port,
                "protocol": port.protocol
            }
            if hasattr(port, "node_port") and port.node_port:
                port_info["node_port"] = port.node_port
            ports.append(port_info)
        return ports
    
    def create_resource(self, kind: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        """创建Kubernetes资源
        
        Args:
            kind: 资源类型
            spec: 资源规格
            
        Returns:
            创建结果
        """
        try:
            # 验证资源类型
            is_valid, error_msg = self._validate_resource_type(kind)
            if not is_valid:
                return {
                    "success": False,
                    "error": error_msg
                }
            
            namespace = spec.get("namespace", "default")
            api_client = getattr(self, self.SUPPORTED_RESOURCES[kind.lower()])
            
            # 根据资源类型选择合适的API方法
            if kind.lower() == "pod":
                response = api_client.create_namespaced_pod(
                    namespace=namespace,
                    body=spec
                )
            elif kind.lower() == "service":
                response = api_client.create_namespaced_service(
                    namespace=namespace,
                    body=spec
                )
            elif kind.lower() == "deployment":
                response = api_client.create_namespaced_deployment(
                    namespace=namespace,
                    body=spec
                )
            elif kind.lower() == "namespace":
                response = api_client.create_namespace(
                    body=spec
                )
            else:
                return {
                    "success": False,
                    "error": f"暂不支持创建 {kind} 类型的资源"
                }
            
            return self._format_response(response)
            
        except Exception as e:
            self.logger.error(f"创建资源失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def update_resource(self, kind: str, name: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        """更新Kubernetes资源
        
        Args:
            kind: 资源类型
            name: 资源名称
            spec: 资源规格
            
        Returns:
            更新结果
        """
        try:
            # 验证资源类型
            is_valid, error_msg = self._validate_resource_type(kind)
            if not is_valid:
                return {
                    "success": False,
                    "error": error_msg
                }
            
            namespace = spec.get("namespace", "default")
            api_client = getattr(self, self.SUPPORTED_RESOURCES[kind.lower()])
            
            # 根据资源类型选择合适的API方法
            if kind.lower() == "pod":
                response = api_client.patch_namespaced_pod(
                    name=name,
                    namespace=namespace,
                    body=spec
                )
            elif kind.lower() == "service":
                response = api_client.patch_namespaced_service(
                    name=name,
                    namespace=namespace,
                    body=spec
                )
            elif kind.lower() == "deployment":
                response = api_client.patch_namespaced_deployment(
                    name=name,
                    namespace=namespace,
                    body=spec
                )
            elif kind.lower() == "namespace":
                response = api_client.patch_namespace(
                    name=name,
                    body=spec
                )
            else:
                return {
                    "success": False,
                    "error": f"暂不支持更新 {kind} 类型的资源"
                }
            
            return self._format_response(response)
            
        except Exception as e:
            self.logger.error(f"更新资源失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def delete_resource(self, kind: str, name: str, namespace: str = "default") -> Dict[str, Any]:
        """删除Kubernetes资源
        
        Args:
            kind: 资源类型
            name: 资源名称
            namespace: 命名空间
            
        Returns:
            删除结果
        """
        try:
            # 根据资源类型选择合适的API
            if kind.lower() == "pod":
                response = self.core_api.delete_namespaced_pod(
                    name=name,
                    namespace=namespace
                )
                return self._format_response(response)
                
            elif kind.lower() == "service":
                response = self.core_api.delete_namespaced_service(
                    name=name,
                    namespace=namespace
                )
                return self._format_response(response)
                
            elif kind.lower() == "deployment":
                response = self.apps_api.delete_namespaced_deployment(
                    name=name,
                    namespace=namespace
                )
                return self._format_response(response)
                
            elif kind.lower() == "namespace":
                response = self.core_api.delete_namespace(
                    name=name
                )
                return self._format_response(response)
                
            elif kind.lower() == "job":
                response = self.batch_api.delete_namespaced_job(
                    name=name,
                    namespace=namespace
                )
                return self._format_response(response)
                
            elif kind.lower() == "ingress":
                response = self.networking_api.delete_namespaced_ingress(
                    name=name,
                    namespace=namespace
                )
                return self._format_response(response)
                
            else:
                return {
                    "success": False,
                    "error": f"不支持的资源类型: {kind}"
                }
                
        except Exception as e:
            self.logger.error(f"删除资源失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_resource(self, kind: str, name: str, namespace: str = "default") -> Dict[str, Any]:
        """获取Kubernetes资源
        
        Args:
            kind: 资源类型
            name: 资源名称
            namespace: 命名空间
            
        Returns:
            资源信息
        """
        try:
            # 根据资源类型选择合适的API
            if kind.lower() == "pod":
                response = self.core_api.read_namespaced_pod(
                    name=name,
                    namespace=namespace
                )
                return self._format_response(response)
                
            elif kind.lower() == "service":
                response = self.core_api.read_namespaced_service(
                    name=name,
                    namespace=namespace
                )
                return self._format_response(response)
                
            elif kind.lower() == "deployment":
                response = self.apps_api.read_namespaced_deployment(
                    name=name,
                    namespace=namespace
                )
                return self._format_response(response)
                
            elif kind.lower() == "namespace":
                response = self.core_api.read_namespace(
                    name=name
                )
                return self._format_response(response)
                
            elif kind.lower() == "job":
                response = self.batch_api.read_namespaced_job(
                    name=name,
                    namespace=namespace
                )
                return self._format_response(response)
                
            elif kind.lower() == "ingress":
                response = self.networking_api.read_namespaced_ingress(
                    name=name,
                    namespace=namespace
                )
                return self._format_response(response)
                
            else:
                return {
                    "success": False,
                    "error": f"不支持的资源类型: {kind}"
                }
                
        except Exception as e:
            self.logger.error(f"获取资源失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def exec_command(self, pod: str, command: List[str], namespace: str = "default") -> Dict[str, Any]:
        """在Pod中执行命令
        
        Args:
            pod: Pod名称
            command: 要执行的命令
            namespace: 命名空间
            
        Returns:
            命令执行结果
        """
        try:
            # 执行命令
            response = client.CoreV1Api().connect_get_namespaced_pod_exec(
                name=pod,
                namespace=namespace,
                command=command,
                stderr=True,
                stdin=False,
                stdout=True,
                tty=False
            )
            
            return {
                "success": True,
                "output": response
            }
                
        except Exception as e:
            self.logger.error(f"执行命令失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _format_response(self, response):
        """格式化API响应"""
        # 将Kubernetes对象转换为字典
        if hasattr(response, "to_dict"):
            response_dict = response.to_dict()
            return {
                "success": True,
                "data": response_dict
            }
        else:
            return {
                "success": True,
                "data": response
            }