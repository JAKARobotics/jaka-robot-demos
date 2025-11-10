#!/usr/bin/env python3
"""
语音唤醒系统主控制器
实现语音唤醒、语音识别、语音合成、AGV控制、目标检测等功能的服务化调用
"""

import time
import threading
import json
import queue
from typing import Optional, Dict, Any

# 导入各个服务模块
from services.voice_recognition_service import VoiceRecognitionService
from services.voice_synthesis_service import VoiceSynthesisService
from services.agv_control_service import AGVControlService
from services.qr_scan_service import QRScanService
from services.object_detection_service import ObjectDetectionService
from services.ali_detection_service import AliDetectionService
from services.robot_control_service import RobotControlService

class VoiceWakeupSystem:
    """语音唤醒系统主控制器"""
    
    def __init__(self, config_path: str = "./conf/voice_wakeup_config.json"):
        """
        初始化语音唤醒系统
        :param config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        self.is_running = False
        self.is_wakeup = False
        self.command_queue = queue.Queue()
        
        # 检测服务类型选择
        self.detection_type = self.config.get("detection_type", "owl")  # "owl" 或 "ali"
        
        # 初始化各个服务
        self.voice_recognition = VoiceRecognitionService(self.config.get("voice_recognition", {}))
        self.voice_synthesis = VoiceSynthesisService(self.config.get("voice_synthesis", {}))
        self.agv_control = AGVControlService(self.config.get("agv_control", {}))
        self.qr_scan = QRScanService(self.config.get("qr_scan", {}))
        
        # 根据配置选择检测服务
        if self.detection_type == "ali":
            self.object_detection = AliDetectionService(self.config.get("ali_detection", {}))
            print(f"使用阿里检测服务")
        else:
        self.object_detection = ObjectDetectionService(self.config.get("object_detection", {}))
            print(f"使用Owl检测服务")
        
        self.robot_control = RobotControlService(self.config.get("robot_control", {}))
        
        # 启动服务
        self._start_services()
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"配置文件 {config_path} 不存在，使用默认配置")
            return self._get_default_config()
        except Exception as e:
            print(f"加载配置文件失败: {e}，使用默认配置")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "detection_type": "owl",  # "owl" 或 "ali"
            "voice_recognition": {
                "wakeup_word": "lumi",
                "timeout": 5.0
            },
            "voice_synthesis": {
                "appid": "1be4dc2a",
                "apikey": "e4e0a90722f7c18e8e40e9a414f7a100",
                "apisecret": "YTI3YjllMTYwZjczMDJlZTUwZjI3NjI5"
            },
            "agv_control": {
                "agv_ip": "192.168.10.10",
                "agv_port": 31001
            },
            "qr_scan": {
                "camera_serial": "AY8V74300CZ"
            },
            "object_detection": {
                "camera_serial": "AY8V74300F4",
                "web_url": "http://localhost:7860/detect"
            },
            "ali_detection": {
                "camera_serial": "AY8V74300F4",
                "web_url": "http://localhost:7861/detect"
            },
            "robot_control": {
                "robot_ip": "192.168.10.90",
                "ext_base_url": "http://192.168.10.100"
            }
        }
    
    def _start_services(self):
        """启动各个服务"""
        print("正在启动各个服务...")
        
        # 启动语音识别服务
        self.voice_recognition.start()
        print("✓ 语音识别服务已启动")
        
        # 启动语音合成服务
        self.voice_synthesis.start()
        print("✓ 语音合成服务已启动")
        
        # 启动AGV控制服务
        self.agv_control.start()
        print("✓ AGV控制服务已启动")
        
        # 启动二维码扫描服务
        self.qr_scan.start()
        print("✓ 二维码扫描服务已启动")
        
        # 启动目标检测服务
        self.object_detection.start()
        print(f"✓ {self.detection_type.upper()}检测服务已启动")
        
        # 启动机器人控制服务
        self.robot_control.start()
        print("✓ 机器人控制服务已启动")
    
    def start(self):
        """启动语音唤醒系统"""
        if self.is_running:
            print("系统已在运行中")
            return
        
        self.is_running = True
        print("=== 语音唤醒系统启动 ===")
        print(f"检测服务类型: {self.detection_type.upper()}")
        print("等待唤醒词: 'lumi'")
        
        # 启动主循环
        self._main_loop()
    
    def stop(self):
        """停止语音唤醒系统"""
        self.is_running = False
        print("正在停止语音唤醒系统...")
        
        # 停止各个服务
        self.voice_recognition.stop()
        self.voice_synthesis.stop()
        self.agv_control.stop()
        self.qr_scan.stop()
        self.object_detection.stop()
        self.robot_control.stop()
        
        print("语音唤醒系统已停止")
    
    def _main_loop(self):
        """主循环"""
        while self.is_running:
            try:
                # 等待唤醒词
                if not self.is_wakeup:
                    wakeup_result = self.voice_recognition.wait_for_wakeup()
                    if wakeup_result:
                        self._handle_wakeup()
                        continue
                
                # 已唤醒，等待命令
                command = self.voice_recognition.wait_for_command()
                if command:
                    self._handle_command(command)
                
            except KeyboardInterrupt:
                print("\n用户中断，正在退出...")
                break
            except Exception as e:
                print(f"主循环出错: {e}")
                time.sleep(1)
    
    def _handle_wakeup(self):
        """处理唤醒事件"""
        print("检测到唤醒词 'lumi'")
        self.is_wakeup = True
        
        # 语音回复
        self.voice_synthesis.speak("您好，我在")
        
        print("等待语音命令...")
    
    def _handle_command(self, command: str):
        """处理语音命令"""
        print(f"收到命令: {command}")
        
        # 解析命令
        if "请帮我根据桌上的盒子拿药" in command:
            self._execute_medicine_task()
        elif "停止" in command or "退出" in command:
            self.is_wakeup = False
            self.voice_synthesis.speak("好的，我休息了")
            print("等待唤醒词: 'lumi'")
        else:
            self.voice_synthesis.speak("抱歉，我没有理解您的命令")
    
    def _execute_medicine_task(self):
        """执行拿药任务"""
        print("开始执行拿药任务...")
        
        try:
            # 1. 语音确认任务
            self.voice_synthesis.speak("好的，我来帮您拿药")
            
            # 2. 移动到桌子
            self.voice_synthesis.speak("正在移动到桌子")
            if self.agv_control.move_to_marker("table"):
                self.voice_synthesis.speak("已到达桌子")
            else:
                self.voice_synthesis.speak("移动到桌子失败")
                return
            
            # 3. 扫描二维码
            self.voice_synthesis.speak("正在扫描二维码")
            qr_result = self.qr_scan.scan_qr_code()
            if qr_result:
                self.voice_synthesis.speak(f"扫描到药品标签: {qr_result}")
            else:
                self.voice_synthesis.speak("扫描二维码失败")
                return
            
            # 4. 移动到货架
            self.voice_synthesis.speak("正在移动到货架")
            if self.agv_control.move_to_marker("shelf"):
                self.voice_synthesis.speak("已到达货架")
            else:
                self.voice_synthesis.speak("移动到货架失败")
                return
            
            # 5. 目标检测和抓取
            self.voice_synthesis.speak("正在检测目标")
            detection_result = self.object_detection.detect_and_grasp([qr_result])
            
            if detection_result.get("success"):
                self.voice_synthesis.speak("抓取成功")
            else:
                self.voice_synthesis.speak("抓取失败")
                return
            
            # 6. 移动回桌子
            self.voice_synthesis.speak("正在返回桌子")
            if self.agv_control.move_to_marker("table"):
                self.voice_synthesis.speak("已返回桌子，任务完成")
            else:
                self.voice_synthesis.speak("返回桌子失败")
            
        except Exception as e:
            print(f"执行拿药任务时出错: {e}")
            self.voice_synthesis.speak("任务执行出错，请重试")

if __name__ == "__main__":
    # 创建并启动语音唤醒系统
    system = VoiceWakeupSystem()
    
    try:
        system.start()
    except KeyboardInterrupt:
        print("\n正在退出...")
    finally:
        system.stop() 