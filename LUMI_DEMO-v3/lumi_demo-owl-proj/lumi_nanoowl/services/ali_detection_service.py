#!/usr/bin/env python3
"""
阿里检测服务
基于lumi_demo_ali模块实现目标检测功能
"""

import time
import threading
import requests
from typing import Optional, List, Dict, Any
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入阿里检测相关模块
from examples.lumi_demo_ali.test_ali import vl_ali
from multi_camera_manager import Camera
import cv2
import numpy as np

class AliDetectionService:
    """阿里检测服务"""
    
    def __init__(self, config: dict):
        """
        初始化阿里检测服务
        :param config: 配置字典，包含camera_serial, web_url等
        """
        self.config = config
        self.is_running = False
        self.camera_serial = config.get("camera_serial", "AY8V74300F4")
        self.web_url = config.get("web_url", "http://localhost:7861/detect")
        
        # 检测线程
        self.detection_thread = None
        self.detection_result = None
        
        # COCO80类别列表（与lumi_demo_ali.py保持一致）
        self.COCO80 = [
            "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat", "traffic light",
            "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat", "dog", "horse", "sheep", "cow",
            "elephant", "bear", "zebra", "giraffe", "backpack", "umbrella", "handbag", "tie", "suitcase", "frisbee",
            "skis", "snowboard", "sports ball", "kite", "baseball bat", "baseball glove", "skateboard", "surfboard",
            "tennis racket", "bottle", "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana", "apple",
            "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair", "couch",
            "potted plant", "bed", "dining table", "toilet", "tv", "laptop", "mouse", "remote", "keyboard", "cell phone",
            "microwave", "oven", "toaster", "sink", "refrigerator", "book", "clock", "vase", "scissors", "teddy bear",
            "hair drier", "toothbrush", "screwdriver", "wrench", "pliers", "hammer", "tape measure", "electric drill", 
            "Glue gun", "Wire", "Metal ring", "Metal clamp", "double-sided tape", "medicine"
        ]
    
    def start(self):
        """启动阿里检测服务"""
        if self.is_running:
            return
        
        self.is_running = True
        print("阿里检测服务已启动")
    
    def stop(self):
        """停止阿里检测服务"""
        self.is_running = False
        print("阿里检测服务已停止")
    
    def detect_and_grasp(self, target_tags: List[str]) -> Dict[str, Any]:
        """
        检测目标并执行抓取（模拟）
        :param target_tags: 目标标签列表
        :return: 检测和抓取结果
        """
        if not self.is_running:
            print("阿里检测服务未启动")
            return {"success": False, "error": "服务未启动"}
        
        try:
            print(f"开始阿里检测目标: {target_tags}")
            
            # 先进行目标检测
            detection_result = self.detect_objects(target_tags)
            
            if not detection_result.get("success"):
                return detection_result
            
            # 模拟抓取操作
            detected_objects = detection_result.get("labels", [])
            if detected_objects:
                print(f"检测到目标: {detected_objects}")
                # 这里可以添加实际的机器人抓取逻辑
                return {
                    "success": True,
                    "targets": target_tags,
                    "detected_objects": detected_objects,
                    "grasp_success": True,
                    "message": "抓取成功"
                }
            else:
                return {
                    "success": False,
                    "error": "未检测到目标物体"
                }
            
        except Exception as e:
            print(f"阿里检测和抓取出错: {e}")
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
            print("阿里检测服务未启动")
            return {"success": False, "error": "服务未启动"}
        
        try:
            # 方法1：通过Web API调用检测服务
            if self.test_web_service():
                return self._detect_via_web_api(target_tags)
            
            # 方法2：直接调用本地检测
            return self._detect_locally(target_tags)
                
        except Exception as e:
            return {
                "success": False,
                "error": f"检测出错: {e}"
            }
    
    def _detect_via_web_api(self, target_tags: List[str] = None) -> Dict[str, Any]:
        """
        通过Web API进行检测
        """
        try:
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
    
    def _detect_locally(self, target_tags: List[str] = None) -> Dict[str, Any]:
        """
        本地直接调用检测
        """
        try:
            # 初始化相机
            camera = Camera(serial_number=self.camera_serial, require_depth=True)
            
            # 获取图像
            color_img, depth_data, _ = camera.getColorDepthData()
            
            if color_img is None or depth_data is None:
                return {
                    "success": False,
                    "error": "无法获取相机图像"
                }
            
            # 保存临时图像
            img_path = "/tmp/ali_detection_temp.jpg"
            cv2.imwrite(img_path, color_img)
            
            # 使用阿里检测
            if target_tags:
                # 检测指定目标
                obj_labels, obj_locs = vl_ali(target_tags, img_path)
            else:
                # 检测所有COCO80类别
                obj_labels, obj_locs = vl_ali(self.COCO80, img_path)
            
            # 构造结果
            obj_confs = [0.99] * len(obj_labels) if obj_labels else []
            
            # 清理临时文件
            if os.path.exists(img_path):
                os.remove(img_path)
            
            # 关闭相机
            camera.close()
            
            return {
                "success": True,
                "labels": obj_labels,
                "locs": obj_locs,
                "confs": obj_confs,
                "depth_data": depth_data.tolist() if depth_data is not None else []
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"本地检测失败: {e}"
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
    
    def test_camera(self) -> bool:
        """
        测试相机连接
        :return: 相机是否可用
        """
        try:
            camera = Camera(serial_number=self.camera_serial, require_depth=False)
            camera.close()
            return True
        except Exception as e:
            print(f"相机测试失败: {e}")
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
            "web_service_available": self.test_web_service(),
            "camera_available": self.test_camera(),
            "detection_method": "阿里视觉检测"
        }

def example_usage():
    """使用示例"""
    config = {
        "camera_serial": "AY8V74300F4",
        "web_url": "http://localhost:7861/detect"
    }
    
    service = AliDetectionService(config)
    service.start()
    
    try:
        # 测试检测
        result = service.detect_objects(["红霉素软膏"])
        print(f"检测结果: {result}")
        
        # 测试状态
        status = service.get_service_status()
        print(f"服务状态: {status}")
        
    finally:
        service.stop()

if __name__ == "__main__":
    example_usage() 