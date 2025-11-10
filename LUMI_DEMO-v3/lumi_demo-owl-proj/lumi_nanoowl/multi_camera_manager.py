#!/usr/bin/env python3
"""
多相机管理器
让QR_SCAN.py和lumi_demo_owl.py能够独立使用不同的相机
"""

import threading
import time
import atexit
import signal
import sys
from pyorbbecsdk import *
from utils import frame_to_bgr_image
import cv2
import numpy as np

class MultiCameraManager:
    """多相机管理器，支持多个相机同时使用"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __init__(self):
        self.context = Context()
        self.pipelines = {}  # serial_number -> Pipeline
        self.devices = {}    # serial_number -> Device
        self.configs = {}    # serial_number -> Config
        self.device_index_map = {}  # device_index -> serial_number
        
        # 注册清理函数
        atexit.register(self._cleanup_all)
        
        # 注册信号处理器
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """信号处理函数，确保程序退出时释放所有资源"""
        print(f"\nReceived signal {signum}, cleaning up all camera resources...")
        self._cleanup_all()
        sys.exit(0)
    
    def _cleanup_all(self):
        """清理所有相机资源"""
        print("Cleaning up all camera resources...")
        for sn in list(self.pipelines.keys()):
            try:
                self.close_pipeline(sn)
                print(f"Released camera: {sn}")
            except Exception as e:
                print(f"Error releasing camera {sn}: {e}")
    
    def __del__(self):
        """析构函数，确保资源被释放"""
        self._cleanup_all()
    
    @classmethod
    def get_instance(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = MultiCameraManager()
            return cls._instance
    
    def get_device_by_serial(self, serial_number):
        """根据序列号获取设备"""
        if serial_number in self.devices:
            return self.devices[serial_number]
        
        device_list = self.context.query_devices()
        for i in range(device_list.get_count()):
            dev = device_list.get_device_by_index(i)
            dev_sn = dev.get_device_info().get_serial_number()
            if dev_sn == serial_number:
                self.devices[serial_number] = dev
                self.device_index_map[i] = serial_number
                return dev
        
        raise RuntimeError(f"Device with serial {serial_number} not found")
    
    def get_device_by_index(self, device_index):
        """根据索引获取设备"""
        device_list = self.context.query_devices()
        if device_index >= device_list.get_count():
            raise RuntimeError(f"Device index {device_index} out of range")
        
        # 检查该索引是否已被使用
        if device_index in self.device_index_map:
            # 该索引已被使用，查找下一个可用设备
            actual_index = device_index
            for i in range(device_list.get_count()):
                if i not in self.device_index_map:
                    actual_index = i
                    break
            else:
                raise RuntimeError("No available devices")
        else:
            actual_index = device_index
        
        try:
            dev = device_list.get_device_by_index(actual_index)
            dev_sn = dev.get_device_info().get_serial_number()
            self.devices[dev_sn] = dev
            self.device_index_map[actual_index] = dev_sn
            return dev, dev_sn
        except Exception as e:
            print(f"Error accessing device at index {actual_index}: {e}")
            # 如果当前索引失败，尝试其他可用索引
            for i in range(device_list.get_count()):
                if i not in self.device_index_map and i != actual_index:
                    try:
                        dev = device_list.get_device_by_index(i)
                        dev_sn = dev.get_device_info().get_serial_number()
                        self.devices[dev_sn] = dev
                        self.device_index_map[i] = dev_sn
                        print(f"Successfully accessed device at index {i} instead of {actual_index}")
                        return dev, dev_sn
                    except Exception as e2:
                        print(f"Error accessing device at index {i}: {e2}")
                        continue
            raise RuntimeError(f"Failed to access any available device: {e}")
    
    def create_pipeline(self, device, align_mode="SW", enable_sync=True):
        """为设备创建pipeline"""
        pipeline = Pipeline(device)
        config = Config()
        
        try:
            # 配置彩色流
            color_profiles = pipeline.get_stream_profile_list(OBSensorType.COLOR_SENSOR)
            color_profile = color_profiles.get_video_stream_profile(1280, 800, OBFormat.RGB, 30)
            config.enable_stream(color_profile)
            
            # 配置深度流
            depth_profiles = pipeline.get_stream_profile_list(OBSensorType.DEPTH_SENSOR)
            depth_profile = depth_profiles.get_video_stream_profile(1280, 800, OBFormat.RLE, 30)
            config.enable_stream(depth_profile)
            
            # 设置对齐模式
            if align_mode == 'HW':
                config.set_align_mode(OBAlignMode.HW_MODE)
            elif align_mode == 'SW':
                config.set_align_mode(OBAlignMode.SW_MODE)
            else:
                config.set_align_mode(OBAlignMode.DISABLE)
            
            # 启用帧同步
            if enable_sync:
                pipeline.enable_frame_sync()
            
            # 启动pipeline
            pipeline.start(config)
            return pipeline, config
            
        except Exception as e:
            print(f"Error creating pipeline: {e}")
            raise
    
    def get_pipeline(self, serial_number, align_mode="SW", enable_sync=True):
        """获取或创建pipeline"""
        if serial_number in self.pipelines:
            return self.pipelines[serial_number]
        
        device = self.get_device_by_serial(serial_number)
        pipeline, config = self.create_pipeline(device, align_mode, enable_sync)
        self.pipelines[serial_number] = pipeline
        self.configs[serial_number] = config
        return pipeline
    
    def close_pipeline(self, serial_number):
        """关闭pipeline"""
        if serial_number in self.pipelines:
            self.pipelines[serial_number].stop()
            del self.pipelines[serial_number]
            del self.configs[serial_number]
            # 从索引映射中移除
            for idx, sn in list(self.device_index_map.items()):
                if sn == serial_number:
                    del self.device_index_map[idx]
                    break
    
    def list_available_devices(self):
        """列出所有可用设备"""
        device_list = self.context.query_devices()
        available_devices = []
        for i in range(device_list.get_count()):
            try:
                dev = device_list.get_device_by_index(i)
                dev_info = dev.get_device_info()
                dev_sn = dev_info.get_serial_number()
                is_used = dev_sn in self.pipelines
                available_devices.append({
                    "index": i,
                    "name": dev_info.get_name(),
                    "serial_number": dev_sn,
                    "pid": dev_info.get_pid(),
                    "vid": dev_info.get_vid(),
                    "is_used": is_used
                })
            except Exception as e:
                print(f"Warning: Failed to get device info for index {i}: {e}")
                # 如果设备已被使用，仍然添加到列表中但标记为已使用
                if i in self.device_index_map:
                    dev_sn = self.device_index_map[i]
                    available_devices.append({
                        "index": i,
                        "name": "Unknown (in use)",
                        "serial_number": dev_sn,
                        "pid": 0,
                        "vid": 0,
                        "is_used": True
                    })
        return available_devices

class Camera:
    """相机类，支持多设备管理"""
    
    def __init__(self, serial_number=None, device_index=None, align_mode="SW", enable_sync=True, require_depth=True):
        self.serial_number = serial_number
        self.manager = MultiCameraManager.get_instance()
        self.pipeline = None
        self._is_closed = False
        self.require_depth = require_depth
        
        # 列出所有可用设备
        available_devices = self.manager.list_available_devices()
        print(f"Available devices: {len(available_devices)}")
        for dev in available_devices:
            status = "USED" if dev["is_used"] else "AVAILABLE"
            print(f"  Device {dev['index']}: {dev['name']} (SN: {dev['serial_number']}) - {status}")
        
        if serial_number:
            # 使用指定的序列号
            try:
                self.pipeline = self.manager.get_pipeline(serial_number, align_mode, enable_sync)
                device_info = self.pipeline.get_device().get_device_info()
                print(f"Using device with SN: {serial_number} ({device_info.get_name()})")
            except Exception as e:
                print(f"Error getting pipeline for SN {serial_number}: {e}")
                raise
        elif device_index is not None:
            # 使用指定的设备索引
            try:
                device, self.serial_number = self.manager.get_device_by_index(device_index)
                self.pipeline, _ = self.manager.create_pipeline(device, align_mode, enable_sync)
                device_info = device.get_device_info()
                print(f"Using device at index {device_index}: {device_info.get_name()} (SN: {self.serial_number})")
            except Exception as e:
                print(f"Error getting device at index {device_index}: {e}")
                raise
        else:
            # 自动选择第一个可用设备
            device_list = self.manager.context.query_devices()
            if device_list.get_count() == 0:
                print("No devices connected!")
                return
            
            # 查找第一个未使用的设备
            for i in range(device_list.get_count()):
                if i not in self.manager.device_index_map:
                    try:
                        device, self.serial_number = self.manager.get_device_by_index(i)
                        self.pipeline, _ = self.manager.create_pipeline(device, align_mode, enable_sync)
                        device_info = device.get_device_info()
                        print(f"Auto-selected device {i}: {device_info.get_name()} (SN: {self.serial_number})")
                        break
                    except Exception as e:
                        print(f"Error with device {i}: {e}, trying next device...")
                        continue
            else:
                print("No available devices!")
                return
        
        # 等待初始化完成
        self._wait_for_initialization()
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口，自动释放资源"""
        self.close()
    
    def close(self):
        """关闭相机"""
        if self._is_closed:
            return
            
        try:
            if hasattr(self, 'serial_number') and self.serial_number:
                print(f"Closing camera: {self.serial_number}")
                self.manager.close_pipeline(self.serial_number)
            elif hasattr(self, 'pipeline') and self.pipeline:
                print("Closing camera pipeline")
                self.pipeline.stop()
            self._is_closed = True
            print("Camera closed successfully")
        except Exception as e:
            print(f"Error closing camera: {e}")
    
    def __del__(self):
        """析构函数，确保资源被释放"""
        if not self._is_closed:
            self.close()
    
    def _wait_for_initialization(self):
        """等待相机初始化完成"""
        max_attempts = 5
        attempt = 0
        success = False
        
        while attempt < max_attempts and not success:
            try:
                frames = self.pipeline.wait_for_frames(1000)
                if frames is None:
                    print(f"Initial frames are None, attempt {attempt+1}/{max_attempts}")
                    attempt += 1
                    time.sleep(0.5)
                    continue
                    
                color_frame = frames.get_color_frame()
                depth_frame = None
                if self.require_depth:
                    depth_frame = frames.get_depth_frame()

                if color_frame is None or (self.require_depth and depth_frame is None):
                    print(f"Initial frames are None, attempt {attempt+1}/{max_attempts}")
                    attempt += 1
                    time.sleep(0.5)
                    continue
                
                # 检查 color image
                color_image = frame_to_bgr_image(color_frame)
                if color_image is not None and color_image.size > 0:
                    if self.require_depth:
                        # 检查 depth frame
                        if depth_frame.get_width() > 0 and depth_frame.get_height() > 0:
                            success = True
                            print("Successfully initialized camera with valid color and depth frames")
                        else:
                            print(f"Invalid depth frame dimensions, attempt {attempt+1}/{max_attempts}")
                            continue
                    else:
                        success = True
                        print("Successfully initialized camera with valid color frame (no depth required)")
                else:
                    print(f"Invalid color image data, attempt {attempt+1}/{max_attempts}")
                    continue
                
                attempt += 1
                if not success:
                    time.sleep(0.5)
                
            except Exception as e:
                print(f"Error getting initial frames (attempt {attempt+1}/{max_attempts}): {e}")
                attempt += 1
                time.sleep(0.5)
        
        if not success:
            print("Failed to initialize camera after multiple attempts")
            self.close()
            raise RuntimeError("Camera initialization failed")
    
    def getColorDepthData(self):
        """获取彩色和深度数据"""
        try:
            frames = self.pipeline.wait_for_frames(1000)
            if frames is None:
                return None, None, None

            color_frame = frames.get_color_frame()
            depth_frame = frames.get_depth_frame()
            
            if color_frame is None or depth_frame is None:
                return None, None, None

            # 获取彩色图像
            color_image = frame_to_bgr_image(color_frame)

            # 获取深度数据
            width = depth_frame.get_width()
            height = depth_frame.get_height()
            scale = depth_frame.get_depth_scale()
            
            depth_data = np.frombuffer(depth_frame.get_data(), dtype=np.uint16)
            depth_data = depth_data.reshape((height, width))
            depth_data = depth_data.astype(np.float32) * scale

            # 深度图像可视化
            depth_image = cv2.normalize(depth_data, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
            depth_image = cv2.applyColorMap(depth_image, cv2.COLORMAP_JET)
            depth_image = cv2.addWeighted(color_image, 0.5, depth_image, 0.5, 0)

            return color_image, depth_data, depth_image
            
        except Exception as e:
            print(f"Error getting color/depth data: {e}")
            return None, None, None

    def getColorImageData(self):
        """只获取彩色图像数据，不依赖深度数据"""
        try:
            frames = self.pipeline.wait_for_frames(1000)
            if frames is None:
                return None
            color_frame = frames.get_color_frame()
            if color_frame is None:
                return None
            color_image = frame_to_bgr_image(color_frame)
            return color_image
        except Exception as e:
            print(f"Error getting color image data: {e}")
            return None

def list_devices():
    """列出所有连接的设备"""
    manager = MultiCameraManager.get_instance()
    devices = manager.list_available_devices()
    print("Connected devices:")
    for dev in devices:
        status = "USED" if dev["is_used"] else "AVAILABLE"
        print(f"  {dev['index']}: {dev['name']} (SN: {dev['serial_number']}) - {status}")
    return devices

if __name__ == "__main__":
    # 测试多相机管理器
    print("Testing Multi-Camera Manager...")
    devices = list_devices()
    
    if len(devices) >= 2:
        print("\nTesting two cameras simultaneously...")
        
        # 创建第一个相机
        cam1 = Camera(device_index=0)
        print(f"Camera 1 initialized: {cam1.serial_number}")
        
        # 创建第二个相机
        cam2 = Camera(device_index=1)
        print(f"Camera 2 initialized: {cam2.serial_number}")
        
        # 测试获取数据
        for i in range(5):
            print(f"\nFrame {i+1}:")
            
            # 获取相机1的数据
            color1, depth1, depth_img1 = cam1.getColorDepthData()
            if color1 is not None:
                print(f"  Camera 1: Color shape {color1.shape}, Depth shape {depth1.shape}")
            
            # 获取相机2的数据
            color2, depth2, depth_img2 = cam2.getColorDepthData()
            if color2 is not None:
                print(f"  Camera 2: Color shape {color2.shape}, Depth shape {depth2.shape}")
            
            time.sleep(0.5)
        
        # 关闭相机
        cam1.close()
        cam2.close()
        print("\nCameras closed successfully")
    else:
        print("Need at least 2 cameras for testing") 