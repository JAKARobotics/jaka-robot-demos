#!/usr/bin/env python3
"""
目标检测服务
基于lumi_det_demo模块实现目标检测和抓取功能
"""

import time
import threading
import requests
from typing import Optional, List, Dict, Any
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import lumi_det_demo

class ObjectDetectionService:
    """目标检测服务"""
    
    def __init__(self, config: dict):
        """
        初始化目标检测服务
        :param config: 配置字典，包含camera_serial, web_url等
        """
        self.config = config
        self.is_running = False
        self.camera_serial = config.get("camera_serial", "AY8V743013S")
        self.web_url = config.get("web_url", "http://localhost:7860/detect")
        
        # 检测线程
        self.detection_thread = None
        self.detection_result = None
    
    def start(self):
        """启动目标检测服务"""
        if self.is_running:
            return
        
        self.is_running = True
        print("目标检测服务已启动")
    
    def stop(self):
        """停止目标检测服务"""
        self.is_running = False
        print("目标检测服务已停止")
    
    def detect_and_grasp(self, target_tags: List[str]) -> Dict[str, Any]:
        """
        检测目标并执行抓取
        :param target_tags: 目标标签列表
        :return: 检测和抓取结果
        """
        if not self.is_running:
            print("目标检测服务未启动")
            return {"success": False, "error": "服务未启动"}
        
        try:
            print(f"开始检测目标: {target_tags}")
            
            # 调用lumi_det_demo进行检测和抓取
            # 注意：这里需要确保lumi_demo_owl.py的Web服务正在运行
            result = lumi_det_demo.run_detection(
                robot=None,  # 机器人控制由RobotControlService处理
                auto_execute=True,
                camera_serial_number=self.camera_serial,
                detect_mode="realtime",
                tags=target_tags
            )
            
            return {
                "success": True,
                "targets": target_tags,
                "result": result
            }
            
        except Exception as e:
            print(f"目标检测和抓取出错: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def detect_objects(self, target_tags: List[str] = None) -> Dict[str, Any]:
        """
        仅检测目标，不执行抓取
        :param target_tags: 目标标签列表，如果为None则检测所有目标
        :return: 检测结果
        """
        if not self.is_running:
            print("目标检测服务未启动")
            return {"success": False, "error": "服务未启动"}
        
        try:
            # 通过Web API调用检测服务
            data = {
                "tags": target_tags or [],
                "conf": 0.2,
                "iou": 0.8
            }
            
            response = requests.post(self.web_url, json=data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "labels": result.get("labels", []),
                    "locs": result.get("locs", []),
                    "confs": result.get("confs", []),
                    "depth_data": result.get("depth_data", [])
                }
            else:
                return {
                    "success": False,
                    "error": f"Web服务响应错误: {response.status_code}"
                }
                
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"Web服务连接失败: {e}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"检测出错: {e}"
            }
    
    def test_web_service(self) -> bool:
        """
        测试Web服务连接
        :return: Web服务是否可用
        """
        try:
            response = requests.get(self.web_url.replace("/detect", ""), timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def get_service_status(self) -> Dict[str, Any]:
        """
        获取服务状态
        :return: 服务状态信息
        """
        return {
            "is_running": self.is_running,
            "camera_serial": self.camera_serial,
            "web_url": self.web_url,
            "web_service_available": self.test_web_service()
        } 