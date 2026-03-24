"""
内置系统监控工具
"""
import os
import time
import psutil
from typing import Dict, Any

from ..base import BaseTool, ToolDefinition


class SystemMonitorTool(BaseTool):
    """系统资源监控工具"""

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="system_monitor",
            description="查询系统资源使用情况（CPU、内存、磁盘、网络）",
            category="system",
            parameters=[
                {
                    "name": "metric",
                    "type": "string",
                    "required": True,
                    "enum": ["cpu", "memory", "disk", "network"],
                    "description": "要查询的资源类型"
                },
                {
                    "name": "duration",
                    "type": "integer",
                    "required": False,
                    "default": 5,
                    "description": "监控持续时间（秒）"
                }
            ],
            timeout=30
        )

    def execute(self, **kwargs) -> Dict[str, Any]:
        metric = kwargs.get("metric", "cpu")
        duration = kwargs.get("duration", 5)

        if metric == "cpu":
            return self._get_cpu_info(duration)
        elif metric == "memory":
            return self._get_memory_info()
        elif metric == "disk":
            return self._get_disk_info()
        elif metric == "network":
            return self._get_network_info(duration)
        else:
            return {
                "success": False,
                "error": f"Unknown metric: {metric}"
            }

    def _get_cpu_info(self, duration: int) -> Dict[str, Any]:
        """获取 CPU 信息"""
        try:
            # 获取 CPU 核心数
            cpu_count = psutil.cpu_count()

            # 获取 CPU 使用率
            cpu_percent = psutil.cpu_percent(interval=duration, percpu=False)

            # 获取每个核心的使用率
            cpu_per_core = psutil.cpu_percent(interval=None, percpu=True)

            return {
                "success": True,
                "metric": "cpu",
                "cpu_percent": cpu_percent,
                "cpu_count": cpu_count,
                "cpu_per_core": cpu_per_core,
                "duration": duration
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get CPU info: {str(e)}"
            }

    def _get_memory_info(self) -> Dict[str, Any]:
        """获取内存信息"""
        try:
            mem = psutil.virtual_memory()

            return {
                "success": True,
                "metric": "memory",
                "total_gb": round(mem.total / (1024 ** 3), 2),
                "available_gb": round(mem.available / (1024 ** 3), 2),
                "used_gb": round(mem.used / (1024 ** 3), 2),
                "percent": mem.percent
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get memory info: {str(e)}"
            }

    def _get_disk_info(self) -> Dict[str, Any]:
        """获取磁盘信息"""
        try:
            partitions = psutil.disk_partitions()
            results = []

            for partition in partitions:
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    results.append({
                        "device": partition.device,
                        "mountpoint": partition.mountpoint,
                        "fstype": partition.fstype,
                        "total_gb": round(usage.total / (1024 ** 3), 2),
                        "used_gb": round(usage.used / (1024 ** 3), 2),
                        "free_gb": round(usage.free / (1024 ** 3), 2),
                        "percent": usage.percent
                    })
                except PermissionError:
                    continue

            return {
                "success": True,
                "metric": "disk",
                "partitions": results
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get disk info: {str(e)}"
            }

    def _get_network_info(self, duration: int) -> Dict[str, Any]:
        """获取网络信息"""
        try:
            # 获取初始网络统计
            net1 = psutil.net_io_counters()

            # 等待一段时间
            time.sleep(duration)

            # 获取结束网络统计
            net2 = psutil.net_io_counters()

            # 计算差值
            bytes_sent = net2.bytes_sent - net1.bytes_sent
            bytes_recv = net2.bytes_recv - net1.bytes_recv
            packets_sent = net2.packets_sent - net1.packets_sent
            packets_recv = net2.packets_recv - net1.packets_recv

            return {
                "success": True,
                "metric": "network",
                "duration": duration,
                "bytes_sent": bytes_sent,
                "bytes_recv": bytes_recv,
                "mb_sent": round(bytes_sent / (1024 ** 2), 2),
                "mb_recv": round(bytes_recv / (1024 ** 2), 2),
                "packets_sent": packets_sent,
                "packets_recv": packets_recv
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get network info: {str(e)}"
            }
