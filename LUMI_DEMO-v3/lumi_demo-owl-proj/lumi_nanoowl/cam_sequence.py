#!/usr/bin/env python3
"""
测试相机序列使用
先启动一个相机，然后启动另一个相机
"""

import time
from multi_camera_manager import Camera, list_devices

def test_camera_sequence():
    """测试相机序列使用"""
    print("=== 测试相机序列使用 ===")
    
    # 列出所有设备
    print("\n1. 列出所有可用设备:")
    devices = list_devices()
    
    if len(devices) < 2:
        print("需要至少2个相机进行测试")
        return
    
    # 获取第一个相机的序列号
    first_camera_sn = None
    for dev in devices:
        if not dev["is_used"]:
            first_camera_sn = dev["serial_number"]
            break
    
    if not first_camera_sn:
        print("没有可用的相机")
        return
    
    print(f"\n2. 启动第一个相机 (SN: {first_camera_sn}):")
    try:
        cam1 = Camera(serial_number=first_camera_sn)
        print(f"   第一个相机启动成功: {cam1.serial_number}")
        
        # 获取几帧数据
        for i in range(3):
            color, depth, depth_img = cam1.getColorDepthData()
            if color is not None:
                print(f"   帧 {i+1}: 彩色图像尺寸 {color.shape}")
            time.sleep(0.5)
        
        print("\n3. 列出当前设备状态:")
        devices_after_cam1 = list_devices()
        
        # 获取第二个相机的序列号
        second_camera_sn = None
        for dev in devices_after_cam1:
            if not dev["is_used"]:
                second_camera_sn = dev["serial_number"]
                break
        
        if second_camera_sn:
            print(f"\n4. 启动第二个相机 (SN: {second_camera_sn}):")
            try:
                cam2 = Camera(serial_number=second_camera_sn)
                print(f"   第二个相机启动成功: {cam2.serial_number}")
                
                # 获取几帧数据
                for i in range(3):
                    color, depth, depth_img = cam2.getColorDepthData()
                    if color is not None:
                        print(f"   帧 {i+1}: 彩色图像尺寸 {color.shape}")
                    time.sleep(0.5)
                
                print("\n5. 列出最终设备状态:")
                list_devices()
                
                # 关闭相机
                print("\n6. 关闭相机:")
                cam2.close()
                print("   第二个相机关闭成功")
                
            except Exception as e:
                print(f"   第二个相机启动失败: {e}")
        else:
            print("   没有可用的第二个相机")
        
        # 关闭第一个相机
        cam1.close()
        print("   第一个相机关闭成功")
        
    except Exception as e:
        print(f"   第一个相机启动失败: {e}")

if __name__ == "__main__":
    test_camera_sequence() 