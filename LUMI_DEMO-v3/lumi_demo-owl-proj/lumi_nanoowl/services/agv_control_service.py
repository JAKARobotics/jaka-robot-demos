#!/usr/bin/env python3
"""
AGV控制服务
基于JAKAIntegrated实现AGV控制功能
"""

import time
import threading
from typing import Optional, Dict, Any
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jaka_utilfs.jaka_integrated import JAKAIntegrated

class AGVControlService:
    """AGV控制服务"""
    
    def __init__(self, config: dict):
        """
        初始化AGV控制服务
        :param config: 配置字典，包含agv_ip, agv_port等
        """
        self.config = config
        self.is_running = False
        self.agv_ip = config.get("agv_ip", "192.168.10.10")
        self.agv_port = config.get("agv_port", 31001)
        
        # AGV控制实例
        self.agv_control = None
        
        # 标记点映射
        self.marker_mapping = {
            "table": "table_marker",
            "shelf": "shelf_marker",
            "home": "home_marker"
        }
        
        # 控制线程
        self.control_thread = None
    
    def start(self):
        """启动AGV控制服务"""
        if self.is_running:
            return
        
        try:
            # 初始化AGV控制
            self.agv_control = JAKAIntegrated(
                robot_ip="192.168.10.90",  # 机器人IP（这里不需要实际连接）
                agv_ip=self.agv_ip,
                agv_port=self.agv_port
            )
            
            self.is_running = True
            print("AGV控制服务已启动")
            
        except Exception as e:
            print(f"AGV控制服务启动失败: {e}")
            self.is_running = False
    
    def stop(self):
        """停止AGV控制服务"""
        self.is_running = False
        print("AGV控制服务已停止")
    
    def move_to_marker(self, marker_name: str) -> bool:
        """
        移动到指定标记点
        :param marker_name: 标记点名称（如"table", "shelf"）
        :return: 是否成功到达
        """
        # if not self.is_running or not self.agv_control:
        #     print("AGV控制服务未启动")
        #     return False
        
        try:
            # # 获取标记点编号
            # marker_id = self.marker_mapping.get(marker_name)
            # if not marker_id:
            #     print(f"未知的标记点: {marker_name}")
            #     return False
            
            # print(f"AGV正在移动到标记点: {marker_name} ({marker_id})")
            
            # 调用AGV移动方法
            result = self.agv_control.agv_moveto(marker_name)
            
            if result:
                print(f"AGV已到达标记点: {marker_name}")
                return True
            else:
                print(f"AGV移动到标记点 {marker_name} 失败")
                return False
                
        except Exception as e:
            print(f"AGV移动出错: {e}")
            return False
    




    def get_status(self) -> Optional[Dict[str, Any]]:
        """
        获取AGV状态
        :return: AGV状态信息
        """
        if not self.is_running or not self.agv_control:
            return None
        
        try:
            return self.agv_control.agv_get_status()
        except Exception as e:
            print(f"获取AGV状态失败: {e}")
            return None
    
    def add_marker(self, marker_name: str, marker_id: str):
        """
        添加标记点映射
        :param marker_name: 标记点名称
        :param marker_id: 标记点ID
        """
        self.marker_mapping[marker_name] = marker_id
        print(f"已添加标记点映射: {marker_name} -> {marker_id}")
    
    def list_markers(self) -> Dict[str, str]:
        """
        列出所有标记点
        :return: 标记点映射字典
        """
        return self.marker_mapping.copy()
    
    def is_connected(self) -> bool:
        """
        检查AGV连接状态
        :return: 是否已连接
        """
        return self.is_running and self.agv_control is not None 