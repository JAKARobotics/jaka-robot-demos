#!/usr/bin/env python3
"""
ObjectDetectionService 使用例子
演示如何使用目标检测服务进行目标检测和抓取
"""

import time
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.object_detection_service import ObjectDetectionService

def example_basic_usage():
    """基本使用例子"""
    print("=== 基本使用例子 ===")
    
    # 1. 创建服务实例
    config = {
        "camera_serial": "AY8V743013S",
        "web_url": "http://localhost:7860/detect"
    }
    
    service = ObjectDetectionService(config)
    
    # 2. 启动服务
    service.start()
    print("服务已启动")
    
    try:
        # 3. 检查服务状态
        status = service.get_service_status()
        print(f"服务状态: {status}")
        
        # 4. 测试Web服务连接
        if service.test_web_service():
            print("✓ Web服务连接正常")
        else:
            print("✗ Web服务连接失败")
            return
        
        # 5. 进行目标检测
        print("\n开始目标检测...")
        detection_result = service.detect_objects(["medicine", "bottle", "cup"])
        
        if detection_result.get("success"):
            print("✓ 检测成功")
            print(f"检测到的标签: {detection_result.get('labels', [])}")
            print(f"检测到的位置: {detection_result.get('locs', [])}")
            print(f"检测到的置信度: {detection_result.get('confs', [])}")
        else:
            print(f"✗ 检测失败: {detection_result.get('error')}")
        
    finally:
        # 6. 停止服务
        service.stop()
        print("服务已停止")

def example_detect_and_grasp():
    """检测并抓取例子"""
    print("\n=== 检测并抓取例子 ===")
    
    config = {
        "camera_serial": "AY8V74300F4",
        "web_url": "http://localhost:7860/detect"
    }
    
    service = ObjectDetectionService(config)
    service.start()
    
    try:
        # 模拟从二维码扫描获得的药品标签
        qr_scanned_tags = ["medicine", "bottle"]
        print(f"从二维码扫描获得的标签: {qr_scanned_tags}")
        
        # 执行检测和抓取
        result = service.detect_and_grasp(qr_scanned_tags)
        
        if result.get("success"):
            print("✓ 检测和抓取成功")
            print(f"目标标签: {result.get('targets')}")
            print(f"检测结果: {result.get('result')}")
        else:
            print(f"✗ 检测和抓取失败: {result.get('error')}")
            
    finally:
        service.stop()

def example_batch_detection():
    """批量检测例子"""
    print("\n=== 批量检测例子 ===")
    
    config = {
        "camera_serial": "AY8V74300F4",
        "web_url": "http://localhost:7860/detect"
    }
    
    service = ObjectDetectionService(config)
    service.start()
    
    try:
        # 定义多个检测任务
        detection_tasks = [
            ["medicine", "bottle"],
            ["cup", "bowl"],
            ["book", "clock"],
            []  # 检测所有目标
        ]
        
        for i, tags in enumerate(detection_tasks, 1):
            print(f"\n任务 {i}: 检测标签 {tags if tags else '所有目标'}")
            
            result = service.detect_objects(tags)
            
            if result.get("success"):
                detected_labels = result.get("labels", [])
                print(f"✓ 检测到 {len(detected_labels)} 个目标: {detected_labels}")
            else:
                print(f"✗ 检测失败: {result.get('error')}")
            
            # 等待一段时间再进行下一次检测
            time.sleep(2)
            
    finally:
        service.stop()

def example_error_handling():
    """错误处理例子"""
    print("\n=== 错误处理例子 ===")
    
    # 1. 测试无效的Web服务URL
    print("1. 测试无效的Web服务URL")
    config_invalid = {
        "camera_serial": "AY8V74300F4",
        "web_url": "http://localhost:9999/detect"  # 无效端口
    }
    
    service = ObjectDetectionService(config_invalid)
    service.start()
    
    try:
        result = service.detect_objects(["medicine"])
        print(f"检测结果: {result}")
    finally:
        service.stop()
    
    # 2. 测试服务未启动的情况
    print("\n2. 测试服务未启动的情况")
    config = {
        "camera_serial": "AY8V74300F4",
        "web_url": "http://localhost:7860/detect"
    }
    
    service = ObjectDetectionService(config)
    # 不启动服务，直接调用检测
    
    result = service.detect_objects(["medicine"])
    print(f"检测结果: {result}")
    
    # 3. 测试空标签列表
    print("\n3. 测试空标签列表")
    service.start()
    
    try:
        result = service.detect_objects([])  # 空标签列表
        print(f"检测结果: {result}")
    finally:
        service.stop()

def example_service_monitoring():
    """服务监控例子"""
    print("\n=== 服务监控例子 ===")
    
    config = {
        "camera_serial": "AY8V74300F4",
        "web_url": "http://localhost:7860/detect"
    }
    
    service = ObjectDetectionService(config)
    
    # 监控服务状态
    print("服务启动前状态:")
    status = service.get_service_status()
    print(f"运行状态: {status['is_running']}")
    print(f"相机序列号: {status['camera_serial']}")
    print(f"Web服务URL: {status['web_url']}")
    print(f"Web服务可用性: {status['web_service_available']}")
    
    service.start()
    
    print("\n服务启动后状态:")
    status = service.get_service_status()
    print(f"运行状态: {status['is_running']}")
    print(f"相机序列号: {status['camera_serial']}")
    print(f"Web服务URL: {status['web_url']}")
    print(f"Web服务可用性: {status['web_service_available']}")
    
    service.stop()

def main():
    """主函数"""
    print("ObjectDetectionService 使用例子")
    print("=" * 50)
    
    try:
        # 运行各种例子
        example_basic_usage()
        # example_detect_and_grasp()
        # example_batch_detection()
        # example_error_handling()
        # example_service_monitoring()
        
        print("\n" + "=" * 50)
        print("所有例子运行完成")
        
    except KeyboardInterrupt:
        print("\n用户中断，正在退出...")
    except Exception as e:
        print(f"运行例子时出错: {e}")

if __name__ == "__main__":
    main() 