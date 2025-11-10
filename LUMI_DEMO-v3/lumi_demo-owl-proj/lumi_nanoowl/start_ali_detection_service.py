#!/usr/bin/env python3
"""
阿里检测Web服务启动脚本
启动lumi_demo_ali.py的Web服务
"""

import argparse
import time
import sys
import os
import subprocess

def start_ali_detection_service():
    """启动阿里检测Web服务"""
    print("启动阿里检测Web服务...")
    
    # 启动lumi_demo_ali.py的Web服务
    try:
        # 使用subprocess启动Web服务
        cmd = [
            "python3", "examples/lumi_demo_ali/lumi_demo_ali.py",
            "--camera-sn", "AY8V74300F4",
            "--port", "7861",
            "--host", "0.0.0.0"
        ]
        
        print(f"执行命令: {' '.join(cmd)}")
        process = subprocess.Popen(cmd)
        
        # 等待服务启动
        time.sleep(5)
        
        print("阿里检测Web服务已启动")
        print("服务地址: http://localhost:7861")
        print("检测接口: http://localhost:7861/detect")
        return process
        
    except Exception as e:
        print(f"启动阿里检测服务失败: {e}")
        return None

def test_ali_detection_service():
    """测试阿里检测服务"""
    print("测试阿里检测服务...")
    
    try:
        from services.ali_detection_service import AliDetectionService
        
        # 创建服务实例
        config = {
            "camera_serial": "AY8V74300F4",
            "web_url": "http://localhost:7861/detect"
        }
        
        service = AliDetectionService(config)
        service.start()
        
        # 测试服务状态
        status = service.get_service_status()
        print(f"服务状态: {status}")
        
        # 测试检测功能
        result = service.detect_objects(["medicine", "bottle"])
        print(f"检测结果: {result}")
        
        service.stop()
        print("阿里检测服务测试完成")
        
    except Exception as e:
        print(f"测试阿里检测服务失败: {e}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="阿里检测Web服务启动脚本")
    parser.add_argument("--mode", choices=["start", "test"], default="start",
                       help="运行模式: start=启动服务, test=测试服务")
    parser.add_argument("--camera-sn", default="AY8V74300F4",
                       help="相机序列号")
    parser.add_argument("--port", type=int, default=7861,
                       help="服务端口")
    
    args = parser.parse_args()
    
    if args.mode == "test":
        # 测试服务
        test_ali_detection_service()
    
    else:
        # 启动服务
        process = start_ali_detection_service()
        if process:
            try:
                print("阿里检测Web服务正在运行...")
                print("按 Ctrl+C 停止服务")
                process.wait()
            except KeyboardInterrupt:
                print("\n正在停止阿里检测Web服务...")
                process.terminate()
                process.wait()
                print("服务已停止")

if __name__ == "__main__":
    main() 