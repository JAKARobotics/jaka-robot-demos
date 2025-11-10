#!/usr/bin/env python3
"""
简单的检测功能测试脚本
快速测试目标检测功能，不涉及机器人控制
"""

import time
import json
import numpy as np
import sys
import os
import subprocess
import requests

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.object_detection_service import ObjectDetectionService
from jaka_utilfs.tools import pixel_to_world

def start_detection_web():
    """启动检测Web服务"""
    web_dir = os.path.join(os.path.dirname(__file__), "examples/lumi_demo_ali")
    cmd = [
        "python3",
        "lumi_demo_ali.py",
        "--camera-sn", "AY8V74300F4",
        "--port", "7861"
    ]
    proc = subprocess.Popen(cmd, cwd=web_dir)
    print("检测Web服务已启动，等待8秒以确保服务就绪...")
    time.sleep(8)
    return proc

def load_calib_params():
    """加载相机标定参数"""
    try:
        with open('conf/CalibParams-lumi-hand.json', 'r') as f:
            calib_params = json.load(f)
        return calib_params
    except Exception as e:
        print(f"加载相机标定参数失败: {e}")
        return None

def test_web_service_direct():
    """直接测试Web服务"""
    print("=== 直接测试Web服务 ===")
    
    url = "http://localhost:7861/detect"
    data = {
        "tags": ["西瓜霜润喉片", "红霉素软膏"],
        "conf": 0.2,
        "iou": 0.8
    }
    
    try:
        print(f"发送请求到: {url}")
        print(f"请求数据: {data}")
        
        response = requests.post(url, json=data, timeout=10)
        
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("检测成功！")
            print(f"检测结果: {result}")
            return result
        else:
            print(f"Web服务响应错误: {response.status_code}")
            print(f"响应内容: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Web服务连接失败: {e}")
        return None
    except Exception as e:
        print(f"检测出错: {e}")
        return None

def test_detection_service(detector, target_tags):
    """测试检测服务"""
    print(f"=== 测试检测服务 ===")
    print(f"检测目标: {target_tags}")
    
    # 调用检测服务
    detection_result = detector.detect_objects(target_tags)
    
    if detection_result["success"]:
        labels = detection_result["labels"]
        locs = detection_result["locs"]
        confs = detection_result["confs"]
        depth_data = detection_result["depth_data"]
        
        print(f"检测成功！")
        print(f"检测到的标签: {labels}")
        print(f"检测到的位置: {locs}")
        print(f"检测到的置信度: {confs}")
        
        if depth_data:
            depth_array = np.array(depth_data)
            print(f"深度数据形状: {depth_array.shape}")
            print(f"深度数据范围: {depth_array.min()} - {depth_array.max()}")
        else:
            print("深度数据: None")
        
        return detection_result
    else:
        print(f"检测失败: {detection_result.get('error', '未知错误')}")
        return None

def test_coordinate_conversion(detection_result, calib_params):
    """测试坐标转换功能"""
    print(f"=== 测试坐标转换功能 ===")
    
    if not detection_result or not detection_result["success"]:
        print("没有有效的检测结果")
        return None
    
    labels = detection_result["labels"]
    locs = detection_result["locs"]
    depth_data = detection_result["depth_data"]
    
    if len(labels) == 0:
        print("没有检测到目标")
        return None
    
    world_coords_list = []
    
    # 处理所有检测到的目标
    for i, (label, loc) in enumerate(zip(labels, locs)):
        print(f"\n处理目标 {i+1}: {label}, 位置: {loc}")
        
        # 计算目标中心点坐标
        center_x = int((loc[0] + loc[2]) / 2)
        center_y = int((loc[1] + loc[3]) / 2)
        
        # 获取深度信息
        target_depth = depth_data[center_y][center_x]
        print(f"目标中心点: ({center_x}, {center_y}), 深度: {target_depth}")
        
        # 检查深度是否有效
        if target_depth <= 0:
            print("深度信息无效，跳过此目标")
            continue
        
        # 执行坐标转换
        try:
            world_coords = pixel_to_world(
                [center_x, center_y], 
                target_depth, 
                calib_params["CameraMatrix"], 
                calib_params["RotationMat"], 
                calib_params["TranslationMat"]
            )
            
            print(f"世界坐标: {world_coords}")
            world_coords_list.append({
                "label": label,
                "pixel_coords": [center_x, center_y],
                "depth": target_depth,
                "world_coords": world_coords
            })
            
        except Exception as e:
            print(f"坐标转换失败: {e}")
    
    return world_coords_list

def main():
    """主函数"""
    print("=== 简单检测功能测试程序 ===")
    
    # 启动检测Web服务
    print("启动检测Web服务...")
    web_proc = start_detection_web()
    
    try:
        # 加载标定参数
        print("加载相机标定参数...")
        calib_params = load_calib_params()
        
        if not calib_params:
            print("相机标定参数加载失败")
            return
        
        # 初始化检测服务
        print("初始化检测服务...")
        detector = ObjectDetectionService({
            "camera_serial": "AY8V74300F4",
            "web_url": "http://localhost:7861/detect"
        })
        detector.start()
        
        # 测试目标
        target_tags = ["西瓜霜润喉片", "红霉素软膏"]
        
        while True:
            print("\n=== 选择测试模式 ===")
            print("1. 直接测试Web服务")
            print("2. 测试检测服务")
            print("3. 测试检测+坐标转换")
            print("4. 连续检测测试")
            print("5. 退出")
            
            choice = input("请选择测试模式 (1-5): ").strip()
            
            if choice == '1':
                test_web_service_direct()
            elif choice == '2':
                test_detection_service(detector, target_tags)
            elif choice == '3':
                detection_result = test_detection_service(detector, target_tags)
                if detection_result:
                    test_coordinate_conversion(detection_result, calib_params)
            elif choice == '4':
                print("开始连续检测测试，按Ctrl+C停止...")
                try:
                    count = 0
                    while True:
                        count += 1
                        print(f"\n--- 第 {count} 次检测 ---")
                        detection_result = test_detection_service(detector, target_tags)
                        if detection_result:
                            world_coords_list = test_coordinate_conversion(detection_result, calib_params)
                            if world_coords_list:
                                print(f"成功转换 {len(world_coords_list)} 个目标的坐标")
                        time.sleep(2)  # 等待2秒再进行下一次检测
                except KeyboardInterrupt:
                    print("\n连续检测测试已停止")
            elif choice == '5':
                print("退出程序")
                break
            else:
                print("无效选择，请重新输入")
            
            if choice != '4':
                input("\n按回车键继续...")
    
    finally:
        # 清理资源
        print("清理资源...")
        detector.stop()
        web_proc.terminate()
        print("程序结束")

if __name__ == "__main__":
    main()
