# from OrbbecSDK.pyorbbecsdk import *
from pyorbbecsdk import *
from utils import frame_to_bgr_image

import cv2
import numpy as np
import sys
import time
import threading

ESC_KEY = 27
PRINT_INTERVAL = 1  # seconds
MIN_DEPTH = 20  # 20mm
MAX_DEPTH = 10000  # 10000mm

class TemporalFilter:
    def __init__(self, alpha):
        self.alpha = alpha
        self.previous_frame = None

    def process(self, frame):
        if self.previous_frame is None:
            result = frame
        else:
            result = cv2.addWeighted(frame, self.alpha, self.previous_frame, 1 - self.alpha, 0)
        self.previous_frame = result
        return result

class MultiCameraManager:
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self.context = Context()
        self.pipelines = {}  # serial_number -> Pipeline
        self.devices = {}    # serial_number -> Device
        self.configs = {}    # serial_number -> Config
        self.device_index_map = {}  # device_index -> serial_number

    @classmethod
    def get_instance(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = MultiCameraManager()
            return cls._instance

    def get_pipeline(self, serial_number):
        if serial_number in self.pipelines:
            return self.pipelines[serial_number]
        # 查找设备
        device_list = self.context.query_devices()
        found = False
        for i in range(device_list.get_count()):
            dev = device_list.get_device_by_index(i)
            dev_sn = dev.get_device_info().get_serial_number()
            if dev_sn == serial_number:
                found = True
                self.devices[serial_number] = dev
                self.device_index_map[i] = serial_number
                break
        if not found:
            raise RuntimeError(f"Device with serial {serial_number} not found")
        pipeline = Pipeline(self.devices[serial_number])
        self.pipelines[serial_number] = pipeline
        return pipeline

    def get_device_by_index(self, device_index):
        """根据设备索引获取设备，如果该索引的设备已被使用，则返回下一个可用设备"""
        device_list = self.context.query_devices()
        if device_index >= device_list.get_count():
            raise RuntimeError(f"Device index {device_index} out of range")
        
        # 检查该索引是否已被使用
        if device_index in self.device_index_map:
            # 该索引已被使用，查找下一个可用设备
            for i in range(device_list.get_count()):
                if i not in self.device_index_map:
                    device_index = i
                    break
            else:
                raise RuntimeError("No available devices")
        
        dev = device_list.get_device_by_index(device_index)
        dev_sn = dev.get_device_info().get_serial_number()
        self.devices[dev_sn] = dev
        self.device_index_map[device_index] = dev_sn
        pipeline = Pipeline(dev)
        self.pipelines[dev_sn] = pipeline
        return pipeline, dev_sn

    def close_pipeline(self, serial_number):
        if serial_number in self.pipelines:
            self.pipelines[serial_number].stop()
            del self.pipelines[serial_number]
            del self.devices[serial_number]
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
        return available_devices

class Camera():
    print('orbbec camera-------')
    def __init__(self, serial_number=None, device_index=None, align_mode="SW", enable_sync=True):
        self.serial_number = serial_number
        self.manager = MultiCameraManager.get_instance()
        
        # 列出所有可用设备
        available_devices = self.manager.list_available_devices()
        print(f"Available devices: {len(available_devices)}")
        for dev in available_devices:
            status = "USED" if dev["is_used"] else "AVAILABLE"
            print(f"  Device {dev['index']}: {dev['name']} (SN: {dev['serial_number']}) - {status}")
        
        if serial_number:
            # 使用指定的序列号
            self.pipeline = self.manager.get_pipeline(serial_number)
            device_info = self.pipeline.get_device().get_device_info()
            print(f"Using device with SN: {serial_number} ({device_info.get_name()})")
        elif device_index is not None:
            # 使用指定的设备索引
            self.pipeline, self.serial_number = self.manager.get_device_by_index(device_index)
            device_info = self.pipeline.get_device().get_device_info()
            print(f"Using device at index {device_index}: {device_info.get_name()} (SN: {self.serial_number})")
        else:
            # 自动选择第一个可用设备
            device_list = self.manager.context.query_devices()
            if device_list.get_count() == 0:
                    print("No devices connected!")
                return
            
            # 查找第一个未使用的设备
            for i in range(device_list.get_count()):
                if i not in self.manager.device_index_map:
                    self.pipeline, self.serial_number = self.manager.get_device_by_index(i)
                    device_info = self.pipeline.get_device().get_device_info()
                    print(f"Auto-selected device {i}: {device_info.get_name()} (SN: {self.serial_number})")
                    break
            else:
                print("No available devices!")
                return
        
        device_info = self.pipeline.get_device().get_device_info()
        device_pid = device_info.get_pid()
        config = Config()

        # align_mode = "HW" # align mode, HW=hardware mode,SW=software mode,NONE=disable align
        # enable_sync = True  # enable sync
        try:
            color_profiles = self.pipeline.get_stream_profile_list(OBSensorType.COLOR_SENSOR)
            color_profile = color_profiles.get_video_stream_profile(1280, 800, OBFormat.RGB, 30)
            # color_profile = profile_list.get_default_video_stream_profile()
            config.enable_stream(color_profile)

            depth_profiles = self.pipeline.get_stream_profile_list(OBSensorType.DEPTH_SENSOR)
            assert depth_profiles is not None
            # depth_profile = depth_profiles.get_default_video_stream_profile()
            depth_profile = depth_profiles.get_video_stream_profile(1280, 800, OBFormat.RLE, 30)
            assert depth_profile is not None
            print("color profile : {}x{}@{}_{}".format(color_profile.get_width(),
                                                       color_profile.get_height(),
                                                       color_profile.get_fps(),
                                                       color_profile.get_format()))
            print("depth profile : {}x{}@{}_{}".format(depth_profile.get_width(),
                                                       depth_profile.get_height(),
                                                       depth_profile.get_fps(),
                                                       depth_profile.get_format()))
            config.enable_stream(depth_profile)
        except Exception as e:
            print(f"Error configuring streams: {e}")
            return
        if align_mode == 'HW':
            print('--------align_mode: HW')
            if device_pid == 0x066B:
                # Femto Mega does not support hardware D2C, and it is changed to software D2C
                config.set_align_mode(OBAlignMode.SW_MODE)
            else:
                config.set_align_mode(OBAlignMode.HW_MODE)
        elif align_mode == 'SW':
            print('--------align_mode: SW')
            config.set_align_mode(OBAlignMode.SW_MODE)
        else:
            config.set_align_mode(OBAlignMode.DISABLE)
        if enable_sync:
            try:
                self.pipeline.enable_frame_sync()
            except Exception as e:
                print(f"Error enabling frame sync: {e}")
                return
        try:
            self.pipeline.start(config)
        except Exception as e:
            print(f"Error starting pipeline: {e}")
            return

        # 尝试获取初始帧，但加入更多的错误处理
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
                depth_frame = frames.get_depth_frame()
                
                if color_frame is None:
                    print(f"Initial color frame is None, attempt {attempt+1}/{max_attempts}")
                    attempt += 1
                    time.sleep(0.5)
                    continue
                    
                if depth_frame is None:
                    print(f"Initial depth frame is None, attempt {attempt+1}/{max_attempts}")
                    attempt += 1
                    time.sleep(0.5)
                    continue
                
                # 确认帧有效性
                if depth_frame.get_width() > 0 and depth_frame.get_height() > 0:
                    # 获取彩色图像数据，确认数据有效
                    color_image = frame_to_bgr_image(color_frame)
                    if color_image is not None and color_image.size > 0:
                        success = True
                        print("Successfully initialized camera with valid frames")
                    else:
                        print(f"Invalid color image data, attempt {attempt+1}/{max_attempts}")
                else:
                    print(f"Invalid depth frame dimensions, attempt {attempt+1}/{max_attempts}")
                
                attempt += 1
                if not success:
                    time.sleep(0.5)
                
            except Exception as e:
                print(f"Error getting initial frames (attempt {attempt+1}/{max_attempts}): {e}")
                attempt += 1
                time.sleep(0.5)
        
        if not success:
            print("Failed to initialize camera after multiple attempts")
            self.close()  # 确保释放资源
            return

    def getColorImage(self):
        # print('--1--')
        # 获取一帧图像
        while True:
            try:
                frames: FrameSet = self.pipeline.wait_for_frames(1000)
                if frames is None:
                    print('frame is none')
                    continue

                color_frame = frames.get_color_frame()
                if color_frame is None:
                    print('color frame is None')
                    continue

                if color_frame is not None:
                    # covert to RGB format
                    color_image = frame_to_bgr_image(color_frame)
                    return color_image
                break
            except Exception as e:
                print("e: ",e)
                return []
                
    def getColorDepthData(self):
        # 获取一帧图像
        while True:
            try:
                frames: FrameSet = self.pipeline.wait_for_frames(1000)
                if frames is None:
                    print('frame is none')
                    continue

                color_frame = frames.get_color_frame()
                depth_frame = frames.get_depth_frame()
                if color_frame is None or depth_frame is None:
                    print('color/depth frame is None')
                    continue

                if color_frame is not None:
                    # covert to RGB format
                    color_image = frame_to_bgr_image(color_frame)

                if depth_frame is not None:
                    depth_frame = frames.get_depth_frame()

                try:
                    width = depth_frame.get_width()
                    height = depth_frame.get_height()
                    scale = depth_frame.get_depth_scale()  # 1280 720 1.0
                    # print('--h,w,s------')
                    # print(width, height, scale)
                except:
                    width = 1280
                    height = 800
                    scale = 1.0

                depth_data = np.frombuffer(depth_frame.get_data(), dtype=np.uint16)
                depth_data = depth_data.reshape((height, width))
                depth_data = depth_data.astype(np.float32) * scale

                temporal_filter = TemporalFilter(alpha=0.5)
                depth_data = np.where((depth_data > MIN_DEPTH) & (depth_data < MAX_DEPTH), depth_data, 0)
                depth_data = depth_data.astype(np.uint16)
                # Apply temporal filtering
                depth_data = temporal_filter.process(depth_data)
                # center_distance = depth_data[center_y, center_x]

                depth_image = cv2.normalize(depth_data, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
                depth_image = cv2.applyColorMap(depth_image, cv2.COLORMAP_JET)

                # overlay color image on depth image
                depth_image = cv2.addWeighted(color_image, 0.5, depth_image, 0.5, 0)

                return color_image, depth_data, depth_image
            except Exception as e:
                print(f"Error getting color/depth data: {e}")
                return [],[],[]

    def close(self):
        if hasattr(self, 'serial_number') and self.serial_number:
            self.manager.close_pipeline(self.serial_number)
        elif hasattr(self, 'pipeline') and self.pipeline:
            self.pipeline.stop()
            
    def list_connected_devices(self):
        """List all connected Orbbec devices and their serial numbers"""
        device_list = self.context.query_devices()
        
        # 检测设备数量的正确方法
        devices_info = []
        device_count = 0
        
        # 尝试枚举设备，直到抛出异常
        try:
            while True:
                device = device_list.get_device_by_index(device_count)
                if device:
                    dev_info = device.get_device_info()
                    devices_info.append({
                        "index": device_count,
                        "name": dev_info.get_name(),
                        "serial_number": dev_info.get_serial_number(),
                        "pid": dev_info.get_pid(),
                        "vid": dev_info.get_vid()
                    })
                    device_count += 1
        except Exception as e:
            # 当没有更多设备时会抛出异常，这是正常的
            print(f"已找到 {device_count} 个设备")
        
        return devices_info


if __name__ == "__main__":
    import cv2
    import time

    # 可选：指定相机序列号 AY8V74300CZ
    serial_number = "AY8V74300CZ" # 或 "AY8V74300H1" 之类
    # serial_number=serial_number)
    cam = Camera()
    print("Camera initialized.")

    # 获取一帧 color/depth 数据
    color_img, depth_data, depth_image = cam.getColorDepthData()
    print("getColorDepthData returned.")

    # 和 lumi_det_demo.py 一样的有效性判断
    if color_img is None or depth_data is None:
        print("无法获取有效的相机图像，跳过此次检测")
    else:
        print("Color image shape:", color_img.shape)
        print("Depth data shape:", depth_data.shape)
        # 显示图像
        cv2.imshow("Color Image", color_img)
        cv2.imshow("Depth Image", depth_image)
        print("Press any key to exit...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        # 可选：保存图片
        # cv2.imwrite("test_color.jpg", color_img)
        # cv2.imwrite("test_depth.jpg", depth_image)

    # 关闭相机
    cam.close()
    print("Camera closed.")
