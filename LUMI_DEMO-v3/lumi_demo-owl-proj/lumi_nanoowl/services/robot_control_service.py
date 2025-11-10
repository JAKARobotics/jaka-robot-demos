#!/usr/bin/env python3
"""
机器人控制服务
基于JAKAIntegrated实现机器人控制功能
"""

import time
import threading
from typing import Optional, List, Dict, Any
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jaka_utilfs.jaka_integrated import JAKAIntegrated

class RobotControlService:
    """机器人控制服务"""
    
    def __init__(self, config: dict):
        """
        初始化机器人控制服务
        :param config: 配置字典，包含robot_ip, ext_base_url等
        """
        self.config = config
        self.is_running = False
        self.robot_ip = config.get("robot_ip", "192.168.10.90")
        self.ext_base_url = config.get("ext_base_url", "http://192.168.10.100")
        
        # 机器人控制实例
        self.robot_control = None
        
        # 控制线程
        self.control_thread = None
    
    def start(self):
        """启动机器人控制服务"""
        if self.is_running:
            return
        
        try:
            # 初始化机器人控制
            self.robot_control = JAKAIntegrated(
                robot_ip=self.robot_ip,
                ext_base_url=self.ext_base_url
            )
            
            # 设置系统
            if self.robot_control.setup_system():
                self.is_running = True
                print("机器人控制服务已启动")
            else:
                print("机器人控制服务启动失败")
                self.is_running = False
                
        except Exception as e:
            print(f"机器人控制服务启动失败: {e}")
            self.is_running = False
    
    def stop(self):
        """停止机器人控制服务"""
        if self.robot_control:
            self.robot_control.shutdown_system()
        
        self.is_running = False
        print("机器人控制服务已停止")
    
    def move_robot_to_position(self, position: List[float], velocity: float = 90) -> bool:
        """
        移动机器人到指定位置
        :param position: 目标位置 [J1, J2, J3, J4, J5, J6]（度数）
        :param velocity: 移动速度（度/秒）
        :return: 是否成功
        """
        if not self.is_running or not self.robot_control:
            print("机器人控制服务未启动")
            return False
        
        try:
            print(f"机器人正在移动到位置: {position}")
            result = self.robot_control.rob_moveto(position, velocity)
            
            if result == 0:
                print("机器人移动成功")
                return True
            else:
                print(f"机器人移动失败，错误码: {result}")
                return False
                
        except Exception as e:
            print(f"机器人移动出错: {e}")
            return False
    
    def move_external_axis(self, position: List[float], velocity: float = 100) -> bool:
        """
        移动外部轴到指定位置
        :param position: 目标位置 [joint1, joint2, joint3, joint4]
        :param velocity: 移动速度
        :return: 是否成功
        """
        if not self.is_running or not self.robot_control:
            print("机器人控制服务未启动")
            return False
        
        try:
            print(f"外部轴正在移动到位置: {position}")
            result = self.robot_control.ext_moveto(position, velocity)
            
            if result:
                print("外部轴移动成功")
                return True
            else:
                print("外部轴移动失败")
                return False
                
        except Exception as e:
            print(f"外部轴移动出错: {e}")
            return False
    
    def grab_action(self, action: int) -> bool:
        """
        执行夹爪动作
        :param action: 0=张开，1=闭合
        :return: 是否成功
        """
        if not self.is_running or not self.robot_control:
            print("机器人控制服务未启动")
            return False
        
        try:
            action_name = "张开" if action == 0 else "闭合"
            print(f"执行夹爪动作: {action_name}")
            
            self.robot_control.grab_action(action)
            time.sleep(1)  # 等待动作完成
            
            print("夹爪动作执行成功")
            return True
            
        except Exception as e:
            print(f"夹爪动作执行出错: {e}")
            return False
    
    def get_robot_status(self) -> Optional[Dict[str, Any]]:
        """
        获取机器人状态
        :return: 机器人状态信息
        """
        if not self.is_running or not self.robot_control:
            return None
        
        try:
            # 获取关节角度
            joints = self.robot_control.getjoints()
            # 获取TCP位置
            tcp_pos = self.robot_control.get_tcp_pos()
            # 获取外部轴状态
            ext_state = self.robot_control.ext_get_state()
            
            return {
                "joints": joints,
                "tcp_position": tcp_pos,
                "external_axis_state": ext_state,
                "is_connected": True
            }
            
        except Exception as e:
            print(f"获取机器人状态失败: {e}")
            return None
    
    def reset_robot(self) -> bool:
        """
        重置机器人到初始位置
        :return: 是否成功
        """
        if not self.is_running or not self.robot_control:
            print("机器人控制服务未启动")
            return False
        
        try:
            print("重置机器人到初始位置")
            
            # 移动到基准位置
            base_position = [0, 0, 0, 0, 0, 0]  # 根据实际情况调整
            result = self.move_robot_to_position(base_position)
            
            if result:
                print("机器人重置成功")
                return True
            else:
                print("机器人重置失败")
                return False
                
        except Exception as e:
            print(f"机器人重置出错: {e}")
            return False
    
    def is_connected(self) -> bool:
        """
        检查机器人连接状态
        :return: 是否已连接
        """
        return self.is_running and self.robot_control is not None 