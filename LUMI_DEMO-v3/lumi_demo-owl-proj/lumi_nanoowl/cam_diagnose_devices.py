#!/usr/bin/env python3
"""
详细的设备诊断脚本
"""

import subprocess
import os
import time

def run_command(cmd):
    """运行命令并返回输出"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "", "Command timeout", -1

def diagnose_devices():
    """诊断设备状态"""
    print("=== 设备诊断报告 ===")
    
    # 1. 检查 lsusb
    print("\n1. USB设备列表 (lsusb):")
    stdout, stderr, code = run_command("lsusb")
    if code == 0:
        print(stdout)
    else:
        print(f"Error: {stderr}")
        print("建议安装: apt update && apt install usbutils")
    
    # 2. 检查 /dev/video 设备
    print("\n2. Video设备列表:")
    stdout, stderr, code = run_command("ls -la /dev/video*")
    if code == 0:
        print(stdout)
    else:
        print(f"Error: {stderr}")
    
    # 3. 检查 /dev/media 设备
    print("\n3. Media设备列表:")
    stdout, stderr, code = run_command("ls -la /dev/media*")
    if code == 0:
        print(stdout)
    else:
        print(f"Error: {stderr}")
    
    # 4. 检查 USB 设备详细信息
    print("\n4. USB设备详细信息:")
    stdout, stderr, code = run_command("lsusb -v 2>/dev/null | grep -A 5 -B 5 '2bc5:0673'")
    if code == 0:
        print(stdout)
    else:
        print(f"Error: {stderr}")
    
    # 5. 检查设备权限
    print("\n5. 设备权限检查:")
    stdout, stderr, code = run_command("ls -la /dev/video* /dev/media* 2>/dev/null")
    if code == 0:
        print(stdout)
    else:
        print(f"Error: {stderr}")
    
    # 6. 检查当前用户组
    print("\n6. 当前用户和组:")
    stdout, stderr, code = run_command("id")
    if code == 0:
        print(stdout)
    else:
        print(f"Error: {stderr}")
    
    # 7. 检查进程占用
    print("\n7. 可能占用相机的进程:")
    stdout, stderr, code = run_command("lsof /dev/video* 2>/dev/null || echo 'No processes using video devices'")
    if code == 0:
        print(stdout)
    else:
        print(f"Error: {stderr}")
    
    # 8. 检查 Docker 容器状态
    print("\n8. Docker容器状态:")
    stdout, stderr, code = run_command("docker ps")
    if code == 0:
        print(stdout)
    else:
        print(f"Error: {stderr}")
    
    # 9. 检查 Docker 设备挂载
    print("\n9. Docker设备挂载检查:")
    stdout, stderr, code = run_command("docker inspect lumi_nanoowl | grep -A 10 -B 5 'Devices'")
    if code == 0:
        print(stdout)
    else:
        print(f"Error: {stderr}")
    
    # 10. 检查USB设备挂载
    print("\n10. USB设备挂载检查:")
    stdout, stderr, code = run_command("ls -la /dev/bus/usb/ 2>/dev/null")
    if code == 0:
        print("USB总线设备:")
        print(stdout)
    else:
        print("USB总线设备不存在 - 这是问题所在!")
        print("容器启动时需要挂载: --device=/dev/bus/usb")
    
    # 11. 检查udev规则
    print("\n11. udev规则检查:")
    stdout, stderr, code = run_command("ls -la /etc/udev/rules.d/ | grep -i orbbec")
    if code == 0:
        print(stdout)
    else:
        print("未找到Orbbec相关的udev规则")
def test_usb_access():
    """测试USB设备访问权限"""
    print("\n=== USB设备访问测试 ===")
    
    # 检查USB总线目录
    print("1. 检查USB总线目录:")
    stdout, stderr, code = run_command("ls -la /dev/bus/usb/")
    if code == 0:
        print(stdout)
    else:
        print(f"Error: {stderr}")
    
    # 检查USB设备文件
    print("\n2. 检查USB设备文件:")
    stdout, stderr, code = run_command("find /dev/bus/usb -type c 2>/dev/null | head -10")
    if code == 0:
        print(stdout)
    else:
        print(f"Error: {stderr}")
    
    # 测试USB设备读取权限
    print("\n3. 测试USB设备读取权限:")
    import os
    try:
        # 尝试读取USB设备文件
        usb_devices = []
        for bus in range(1, 10):  # 检查前10个USB总线
            bus_dir = f"/dev/bus/usb/{bus:03d}"
            if os.path.exists(bus_dir):
                for dev in os.listdir(bus_dir):
                    dev_path = f"{bus_dir}/{dev}"
                    try:
                        with open(dev_path, 'rb') as f:
                            # 尝试读取设备描述符
                            data = f.read(18)  # USB设备描述符长度
                            if len(data) >= 18:
                                usb_devices.append(dev_path)
                                print(f"  {dev_path}: 可访问")
                    except Exception as e:
                        print(f"  {dev_path}: 访问失败 - {e}")
        
        if not usb_devices:
            print("  警告: 没有可访问的USB设备!")
            print("  可能原因:")
            print("    1. 容器权限不足")
            print("    2. USB设备未正确挂载")
            print("    3. 需要--privileged参数")
    except Exception as e:
        print(f"USB设备测试失败: {e}")

def test_orbbec_enumeration():
    """测试 Orbbec SDK 枚举"""
    print("\n=== Orbbec SDK 枚举测试 ===")
    
    try:
        from pyorbbecsdk import Context
        import time
        
        # 多次尝试枚举
        for attempt in range(3):
            print(f"\n尝试 {attempt + 1}/3:")
            ctx = Context()
            device_list = ctx.query_devices()
            count = device_list.get_count()
            print(f"  检测到设备数量: {count}")
            
            if count == 0:
                print("  ⚠️  警告: 未检测到设备!")
                print("  可能原因:")
                print("    1. 容器未挂载USB设备 (--device=/dev/bus/usb)")
                print("    2. 设备被其他进程占用")
                print("    3. 驱动问题")
                print("    4. 权限问题")
                print("    5. 需要--privileged参数")
            
            for i in range(count):
                try:
                    dev = device_list.get_device_by_index(i)
                    dev_info = dev.get_device_info()
                    print(f"  设备 {i}: {dev_info.get_name()} (SN: {dev_info.get_serial_number()})")
                except Exception as e:
                    print(f"  设备 {i}: 访问失败 - {e}")
            
            if attempt < 2:
                time.sleep(2)  # 等待2秒再试
                
    except Exception as e:
        print(f"Orbbec SDK 测试失败: {e}")
        print("可能原因:")
        print("  1. pyorbbecsdk 未正确安装")
        print("  2. 缺少USB设备访问权限")
        print("  3. 容器环境限制")
        print("  4. 需要--privileged参数")

def test_video_devices():
    """测试视频设备访问"""
    print("\n=== 视频设备访问测试 ===")
    
    import cv2
    
    # 测试前几个video设备
    for i in range(5):
        try:
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    print(f"  /dev/video{i}: 可访问, 分辨率: {frame.shape}")
                else:
                    print(f"  /dev/video{i}: 可打开但无法读取帧")
                cap.release()
            else:
                print(f"  /dev/video{i}: 无法打开")
        except Exception as e:
            print(f"  /dev/video{i}: 访问失败 - {e}")

if __name__ == "__main__":
    diagnose_devices()
    test_usb_access()
    test_orbbec_enumeration()
    test_video_devices()