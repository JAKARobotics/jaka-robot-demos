#!/usr/bin/env python3
"""
二维码扫描服务
基于QR_SCAN模块实现二维码扫描功能
支持单个和多个二维码检测，统一返回列表格式
"""

import time
import threading
from typing import Optional, List
import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import QR_SCAN


def load_config_from_file(config_file: str = "qr_detection_config.json") -> dict:
    """
    从配置文件加载配置
    :param config_file: 配置文件路径
    :return: 配置字典
    """
    try:
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), config_file)
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        return config_data
    except FileNotFoundError:
        print(f"配置文件 {config_file} 不存在，使用默认配置")
        return {}
    except json.JSONDecodeError as e:
        print(f"配置文件格式错误: {e}，使用默认配置")
        return {}


def create_config_from_mode(mode: str = "default") -> dict:
    """
    根据预设模式创建配置
    :param mode: 模式名称 (default, high_precision, fast, multi_qr)
    :return: 配置字典
    """
    file_config = load_config_from_file()

    # 基础配置
    base_config = {
        "camera_serial": "AY8V74300CZ",
        "use_enhanced_detection": True,
        "save_debug_images": False,
        "max_attempts_per_detection": 2
    }

    # 从文件更新基础配置
    if "camera_settings" in file_config:
        base_config["camera_serial"] = file_config["camera_settings"].get("camera_serial", base_config["camera_serial"])

    # 根据模式选择配置
    mode_configs = {
        "default": file_config.get("detection_settings", {}),
        "high_precision": file_config.get("high_precision_mode", {}),
        "fast": file_config.get("fast_mode", {}),
        "multi_qr": file_config.get("multi_qr_mode", {})
    }

    if mode in mode_configs:
        base_config.update(mode_configs[mode])

    return base_config

class QRScanService:
    """二维码扫描服务"""

    def __init__(self, config: dict):
        """
        初始化二维码扫描服务
        :param config: 配置字典，包含camera_serial等
        """
        self.config = config
        self.is_running = False
        self.camera_serial = config.get("camera_serial", "AY8V74300CZ")

        # 增强检测配置
        self.use_enhanced_detection = config.get("use_enhanced_detection", True)
        self.save_debug_images = config.get("save_debug_images", False)
        self.max_attempts_per_detection = config.get("max_attempts_per_detection", 2)

        # 扫描线程
        self.scan_thread = None
        self.scan_result = None
        self.scan_event = threading.Event()

    @classmethod
    def create_with_mode(cls, mode: str = "default", camera_serial: str = None):
        """
        使用预设模式创建服务实例
        :param mode: 模式名称 (default, high_precision, fast, multi_qr)
        :param camera_serial: 可选的相机序列号，覆盖配置文件设置
        :return: QRScanService实例
        """
        config = create_config_from_mode(mode)
        if camera_serial:
            config["camera_serial"] = camera_serial
        return cls(config)
    
    def start(self):
        """启动二维码扫描服务"""
        if self.is_running:
            return
        
        self.is_running = True
        print("二维码扫描服务已启动")
    
    def stop(self):
        """停止二维码扫描服务"""
        self.is_running = False
        print("二维码扫描服务已停止")
    
    def scan_qr_codes(self, timeout: float = 30.0) -> List[str]:
        """
        扫描二维码（兼容单个和多个）
        :param timeout: 超时时间（秒）
        :return: 扫描到的二维码内容列表
        """
        if not self.is_running:
            print("二维码扫描服务未启动")
            return []

        try:
            print(f"开始扫描二维码，使用相机: {self.camera_serial}")
            print(f"增强检测: {'启用' if self.use_enhanced_detection else '禁用'}")

            if self.use_enhanced_detection:
                # 使用增强版检测
                qr_texts = QR_SCAN.get_qr_text_from_camera_enhanced(
                    camera_serial_number=self.camera_serial,
                    timeout=timeout,
                    max_attempts_per_detection=self.max_attempts_per_detection,
                    save_debug=self.save_debug_images
                )
            else:
                # 使用原始检测方法
                qr_texts = QR_SCAN.get_qr_text_from_camera(
                    camera_serial_number=self.camera_serial,
                    timeout=timeout
                )

            if qr_texts:
                print(f"扫描成功，检测到 {len(qr_texts)} 个二维码: {qr_texts}")
                return qr_texts
            else:
                print("扫描失败或超时，未检测到二维码")
                return []

        except Exception as e:
            print(f"二维码扫描出错: {e}")
            return []
    
    def scan_qr_codes_async(self, callback=None):
        """
        异步扫描二维码（兼容单个和多个）
        :param callback: 回调函数，参数为扫描结果列表
        """
        if not self.is_running:
            print("二维码扫描服务未启动")
            return
        
        def scan_worker():
            try:
                results = self.scan_qr_codes()
                if callback:
                    callback(results)
            except Exception as e:
                print(f"异步扫描出错: {e}")
                if callback:
                    callback([])
        
        scan_thread = threading.Thread(target=scan_worker, daemon=True)
        scan_thread.start()
    
    def scan_qr_codes_from_image(self, image_path: str, use_enhanced: bool = None) -> List[str]:
        """
        从图像文件扫描二维码（兼容单个和多个）
        :param image_path: 图像文件路径
        :param use_enhanced: 是否使用增强检测，None时使用配置默认值
        :return: 扫描到的二维码内容列表
        """
        try:
            print(f"从图像文件扫描二维码: {image_path}")

            # 确定是否使用增强检测
            enhanced = use_enhanced if use_enhanced is not None else self.use_enhanced_detection

            if enhanced:
                print("使用增强版图像检测")
                qr_texts = QR_SCAN.get_qr_text_enhanced(image_path, save_debug=self.save_debug_images)
            else:
                print("使用标准图像检测")
                qr_texts = QR_SCAN.get_qr_text(image_path)

            if qr_texts:
                print(f"扫描成功，检测到 {len(qr_texts)} 个二维码: {qr_texts}")
                return qr_texts
            else:
                print("扫描失败，未检测到二维码")
                return []

        except Exception as e:
            print(f"图像二维码扫描出错: {e}")
            return []
    
    def test_camera(self) -> bool:
        """
        测试相机连接
        :return: 相机是否可用
        """
        try:
            # 尝试创建相机实例
            from multi_camera_manager import Camera
            cam = Camera(serial_number=self.camera_serial, require_depth=False)
            cam.close()
            return True
        except Exception as e:
            print(f"相机测试失败: {e}")
            return False
    
    def get_camera_info(self) -> Optional[dict]:
        """
        获取相机信息
        :return: 相机信息字典
        """
        try:
            from multi_camera_manager import list_devices
            devices = list_devices()
            
            for device in devices:
                if device["serial_number"] == self.camera_serial:
                    return {
                        "serial_number": device["serial_number"],
                        "name": device["name"],
                        "index": device["index"],
                        "is_used": device["is_used"]
                    }
            
            return None
        except Exception as e:
            print(f"获取相机信息失败: {e}")
            return None 

def example_usage():
    # 基础配置
    config = {
        "camera_serial": "AY8V74300CZ",  # 替换为你的相机序列号 AY8V743013S  AY8V74300F4
        "use_enhanced_detection": True,  # 启用增强检测
        "save_debug_images": False,      # 是否保存调试图像
        "max_attempts_per_detection": 2  # 每次检测的最大尝试次数
    }

    service = QRScanService(config)
    service.start()
    try:
        print("=== 测试增强版二维码检测 ===")

        # 扫描二维码（兼容单个和多个）
        results = service.scan_qr_codes(timeout=30)
        if results:
            print(f"检测到 {len(results)} 个二维码:")
            for i, qr_text in enumerate(results):
                print(f"  二维码 {i+1}: {qr_text}")
        else:
            print("未扫描到二维码")

        # 异步扫描二维码
        def on_scan_complete(results):
            if results:
                print(f"异步检测完成，检测到 {len(results)} 个二维码:")
                for i, qr_text in enumerate(results):
                    print(f"  异步二维码 {i+1}: {qr_text}")
            else:
                print("异步检测完成，未检测到二维码")

        service.scan_qr_codes_async(callback=on_scan_complete)
        time.sleep(5)  # 等待异步扫描完成

    finally:
        service.stop()


def example_enhanced_usage():
    """演示增强检测功能的示例"""
    print("=== 增强版二维码检测示例 ===")

    # 高精度配置（适用于多二维码或低分辨率场景）
    high_precision_config = {
        "camera_serial": "AY8V74300CZ",
        "use_enhanced_detection": True,
        "save_debug_images": True,       # 保存调试图像用于分析
        "max_attempts_per_detection": 3  # 增加尝试次数
    }

    service = QRScanService(high_precision_config)
    service.start()

    try:
        print("高精度模式检测...")
        results = service.scan_qr_codes(timeout=45)  # 增加超时时间

        if results:
            print(f"高精度检测到 {len(results)} 个二维码:")
            for i, qr_text in enumerate(results):
                print(f"  二维码 {i+1}: {qr_text}")
        else:
            print("高精度检测未发现二维码")

    finally:
        service.stop()

def example_config_usage():
    """演示配置文件和模式的使用"""
    print("=== 配置文件和模式使用示例 ===")

    # 方法1: 使用预设模式
    print("\n1. 使用高精度模式:")
    service_hp = QRScanService.create_with_mode("high_precision")
    service_hp.start()
    try:
        results = service_hp.scan_qr_codes(timeout=20)
        print(f"高精度模式结果: {len(results)} 个二维码")
    finally:
        service_hp.stop()

    # 方法2: 使用快速模式
    print("\n2. 使用快速模式:")
    service_fast = QRScanService.create_with_mode("fast")
    service_fast.start()
    try:
        results = service_fast.scan_qr_codes(timeout=10)
        print(f"快速模式结果: {len(results)} 个二维码")
    finally:
        service_fast.stop()

    # 方法3: 使用多二维码模式
    print("\n3. 使用多二维码模式:")
    service_multi = QRScanService.create_with_mode("multi_qr")
    service_multi.start()
    try:
        results = service_multi.scan_qr_codes(timeout=30)
        print(f"多二维码模式结果: {len(results)} 个二维码")
    finally:
        service_multi.stop()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="二维码扫描服务测试")
    parser.add_argument("--mode", choices=["default", "high_precision", "fast", "multi_qr"],
                       default="default", help="检测模式")
    parser.add_argument("--config", action="store_true", help="演示配置使用")

    args = parser.parse_args()

    if args.config:
        example_config_usage()
    else:
        if args.mode == "default":
            example_usage()
        else:
            print(f"使用 {args.mode} 模式进行测试")
            service = QRScanService.create_with_mode(args.mode)
            service.start()
            try:
                results = service.scan_qr_codes()
                if results:
                    print(f"检测到 {len(results)} 个二维码:")
                    for i, qr_text in enumerate(results):
                        print(f"  二维码 {i+1}: {qr_text}")
                else:
                    print("未检测到二维码")
            finally:
                service.stop()