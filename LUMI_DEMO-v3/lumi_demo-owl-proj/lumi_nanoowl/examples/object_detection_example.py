#!/usr/bin/env python3
"""
ObjectDetectionService 使用例子
演示如何使用目标检测服务进行目标检测和抓取

使用前请确保：
1. 先启动 lumi_demo_owl.py 的Web服务
2. 确保相机连接正常
"""

import time
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.object_detection_service import ObjectDetectionService

def check_prerequisites():
    """检查前置条件"""
    print("=== 检查前置条件 ===")
    
    # 1. 检查Web服务是否运行
    print("1. 检查Owl检测Web服务...")
    service = ObjectDetectionService({
        "camera_serial": "AY8V74300F4",
        "web_url": "http://localhost:7860/detect"
    })
    
    if service.test_web_service():
        print("✓ Owl检测Web服务正在运行")
        return True
    else:
        print("✗ Owl检测Web服务未运行")
        print("请先启动Web服务：")
        print("python3 examples/lumi_demo/lumi_demo_owl.py /opt/nanoowl/data/owl_image_encoder_patch32.engine --camera-sn AY8V74300F4 --port 7860")
        return False

def simple_detection_example():
    """简单的检测例子"""
    print("\n=== 简单检测例子 ===")
    
    # 创建服务实例
    config = {
        "camera_serial": "AY8V74300F4",
        "web_url": "http://localhost:7860/detect"
    }
    
    service = ObjectDetectionService(config)
    service.start()
    
    try:
        # 检测特定目标
        print("检测目标: medicine, bottle")
        result = service.detect_objects(["medicine", "bottle"])
        
        if result.get("success"):
            print("✓ 检测成功")
            labels = result.get("labels", [])
            locs = result.get("locs", [])
            confs = result.get("confs", [])
            
            print(f"检测到 {len(labels)} 个目标:")
            for i, (label, loc, conf) in enumerate(zip(labels, locs, confs)):
                print(f"  {i+1}. {label} - 位置: {loc[:4]} - 置信度: {conf:.2f}")
        else:
            print(f"✗ 检测失败: {result.get('error')}")
            
    finally:
        service.stop()

def qr_integration_example():
    """二维码集成例子"""
    print("\n=== 二维码集成例子 ===")
    
    # 模拟从二维码扫描获得的标签
    qr_scanned_tags = ["medicine", "bottle"]
    print(f"模拟从二维码扫描获得的标签: {qr_scanned_tags}")
    
    config = {
        "camera_serial": "AY8V74300F4",
        "web_url": "http://localhost:7860/detect"
    }
    
    service = ObjectDetectionService(config)
    service.start()
    
    try:
        # 使用二维码标签进行检测
        print("使用二维码标签进行目标检测...")
        result = service.detect_objects(qr_scanned_tags)
        
        if result.get("success"):
            detected_labels = result.get("labels", [])
            if detected_labels:
                print(f"✓ 成功检测到目标: {detected_labels}")
                
                # 模拟抓取操作
                print("模拟执行抓取操作...")
                grasp_result = service.detect_and_grasp(qr_scanned_tags)
                
                if grasp_result.get("success"):
                    print("✓ 抓取成功")
                else:
                    print(f"✗ 抓取失败: {grasp_result.get('error')}")
            else:
                print("未检测到指定目标")
        else:
            print(f"✗ 检测失败: {result.get('error')}")
            
    finally:
        service.stop()

def main():
    """主函数"""
    print("ObjectDetectionService 使用例子")
    print("=" * 50)
    
    # 检查前置条件
    if not check_prerequisites():
        print("\n请先启动Web服务，然后重新运行此例子")
        return
    
    try:
        # 运行例子
        simple_detection_example()
        qr_integration_example()
        
        print("\n" + "=" * 50)
        print("例子运行完成")
        
    except KeyboardInterrupt:
        print("\n用户中断，正在退出...")
    except Exception as e:
        print(f"运行例子时出错: {e}")

if __name__ == "__main__":
    main() 