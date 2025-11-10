#!/usr/bin/env python3
"""
语音唤醒系统启动脚本
可以分别启动各个服务或启动完整系统
"""

import argparse
import time
import sys
import os

def start_owl_detection_service():
    """启动Owl目标检测Web服务"""
    print("启动Owl目标检测Web服务...")
    
    # 启动lumi_demo_owl.py的Web服务
    import subprocess
    try:
        # 使用subprocess启动Web服务
        cmd = [
            "python3", "examples/lumi_demo/lumi_demo_owl.py",
            "/opt/nanoowl/data/owl_image_encoder_patch32.engine",
            "--camera-sn", "AY8V74300F4",
            "--port", "7860",
            "--host", "0.0.0.0"
        ]
        
        print(f"执行命令: {' '.join(cmd)}")
        process = subprocess.Popen(cmd)
        
        # 等待服务启动
        time.sleep(5)
        
        print("Owl目标检测Web服务已启动")
        return process
        
    except Exception as e:
        print(f"启动Owl目标检测服务失败: {e}")
        return None

def start_ali_detection_service():
    """启动阿里目标检测Web服务"""
    print("启动阿里目标检测Web服务...")
    
    # 启动lumi_demo_ali.py的Web服务
    import subprocess
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
        
        print("阿里目标检测Web服务已启动")
        return process
        
    except Exception as e:
        print(f"启动阿里目标检测服务失败: {e}")
        return None

def start_voice_wakeup_system(detection_type="owl"):
    """启动完整的语音唤醒系统"""
    print(f"启动完整的语音唤醒系统 (检测类型: {detection_type.upper()})...")
    
    try:
        from voice_wakeup_system import VoiceWakeupSystem
        
        # 创建并启动系统
        system = VoiceWakeupSystem()
        
        # 设置检测类型
        system.detection_type = detection_type
        if detection_type == "ali":
            from services.ali_detection_service import AliDetectionService
            system.object_detection = AliDetectionService(system.config.get("ali_detection", {}))
        else:
            from services.object_detection_service import ObjectDetectionService
            system.object_detection = ObjectDetectionService(system.config.get("object_detection", {}))
        
        system.start()
        
    except KeyboardInterrupt:
        print("\n用户中断，正在退出...")
    except Exception as e:
        print(f"启动语音唤醒系统失败: {e}")

def test_individual_services():
    """测试各个独立服务"""
    print("测试各个独立服务...")
    
    try:
        # 测试语音识别服务
        print("\n=== 测试语音识别服务 ===")
        from services.voice_recognition_service import VoiceRecognitionService
        voice_recognition = VoiceRecognitionService({"wakeup_word": "lumi", "timeout": 5.0})
        voice_recognition.start()
        time.sleep(2)
        voice_recognition.stop()
        
        # 测试语音合成服务
        print("\n=== 测试语音合成服务 ===")
        from services.voice_synthesis_service import VoiceSynthesisService
        voice_synthesis = VoiceSynthesisService({
            "appid": "1be4dc2a",
            "apikey": "e4e0a90722f7c18e8e40e9a414f7a100",
            "apisecret": "YTI3YjllMTYwZjczMDJlZTUwZjI3NjI5"
        })
        voice_synthesis.start()
        voice_synthesis.speak("语音合成服务测试成功", block=True)
        voice_synthesis.stop()
        
        # 测试二维码扫描服务
        print("\n=== 测试二维码扫描服务 ===")
        from services.qr_scan_service import QRScanService
        qr_scan = QRScanService({"camera_serial": "AY8V74300CZ"})
        qr_scan.start()
        
        # 测试相机连接
        if qr_scan.test_camera():
            print("二维码扫描服务相机连接正常")
        else:
            print("二维码扫描服务相机连接失败")
        
        qr_scan.stop()
        
        # 测试Owl目标检测服务
        print("\n=== 测试Owl目标检测服务 ===")
        from services.object_detection_service import ObjectDetectionService
        object_detection = ObjectDetectionService({
            "camera_serial": "AY8V74300F4",
            "web_url": "http://localhost:7860/detect"
        })
        object_detection.start()
        
        # 测试Web服务连接
        if object_detection.test_web_service():
            print("Owl目标检测Web服务连接正常")
        else:
            print("Owl目标检测Web服务连接失败")
        
        object_detection.stop()
        
        # 测试阿里目标检测服务
        print("\n=== 测试阿里目标检测服务 ===")
        from services.ali_detection_service import AliDetectionService
        ali_detection = AliDetectionService({
            "camera_serial": "AY8V74300F4",
            "web_url": "http://localhost:7861/detect"
        })
        ali_detection.start()
        
        # 测试Web服务连接
        if ali_detection.test_web_service():
            print("阿里目标检测Web服务连接正常")
        else:
            print("阿里目标检测Web服务连接失败")
        
        ali_detection.stop()
        
        print("\n所有服务测试完成")
        
    except Exception as e:
        print(f"服务测试失败: {e}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="语音唤醒系统启动脚本")
    parser.add_argument("--mode", choices=["full", "owl", "ali", "test"], default="full",
                       help="启动模式: full=完整系统, owl=仅启动Owl检测, ali=仅启动阿里检测, test=测试各个服务")
    parser.add_argument("--detection-type", choices=["owl", "ali"], default="owl",
                       help="检测服务类型: owl=Owl检测, ali=阿里检测")
    parser.add_argument("--config", default="./conf/voice_wakeup_config.json",
                       help="配置文件路径")
    
    args = parser.parse_args()
    
    if args.mode == "owl":
        # 仅启动Owl目标检测Web服务
        process = start_owl_detection_service()
        if process:
            try:
                print("Owl目标检测Web服务正在运行...")
                print("按 Ctrl+C 停止服务")
                process.wait()
            except KeyboardInterrupt:
                print("\n正在停止Owl目标检测Web服务...")
                process.terminate()
                process.wait()
                print("服务已停止")
    
    elif args.mode == "ali":
        # 仅启动阿里目标检测Web服务
        process = start_ali_detection_service()
        if process:
            try:
                print("阿里目标检测Web服务正在运行...")
                print("按 Ctrl+C 停止服务")
                process.wait()
            except KeyboardInterrupt:
                print("\n正在停止阿里目标检测Web服务...")
                process.terminate()
                process.wait()
                print("服务已停止")
    
    elif args.mode == "test":
        # 测试各个服务
        test_individual_services()
    
    else:
        # 启动完整系统
        start_voice_wakeup_system(args.detection_type)

if __name__ == "__main__":
    main() 