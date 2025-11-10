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

def force_release_all_devices():
    """强制释放所有相机设备"""
    print("\n=== 强制释放所有设备 ===")
    
    # 1. 杀死所有可能占用设备的进程
    print("1. 杀死占用设备的进程...")
    commands = [
        "sudo fuser -k /dev/video* 2>/dev/null || true",
        "sudo fuser -k /dev/bus/usb/* 2>/dev/null || true",
        "sudo pkill -f 'python.*lumi_demo' 2>/dev/null || true",
        "sudo pkill -f 'python.*camera' 2>/dev/null || true",
        "sudo pkill -f 'orbbec' 2>/dev/null || true"
    ]
    
    for cmd in commands:
        stdout, stderr, code = run_command(cmd)
        if code == 0:
            print(f"  执行: {cmd}")
    
    # 2. 卸载并重新加载相关内核模块
    print("\n2. 重新加载内核模块...")
    modules = ["uvcvideo", "usb_storage", "usbhid"]
    for module in modules:
        try:
            run_command(f"sudo modprobe -r {module} 2>/dev/null || true")
            run_command(f"sudo modprobe {module} 2>/dev/null || true")
            print(f"  重新加载: {module}")
        except:
            pass
    
    # 3. 重启 udev 服务
    print("\n3. 重启 udev 服务...")
    run_command("sudo service udev restart 2>/dev/null || true")
    run_command("sudo udevadm control --reload-rules 2>/dev/null || true")
    run_command("sudo udevadm trigger 2>/dev/null || true")
    
    # 4. 等待设备重新初始化
    print("\n4. 等待设备重新初始化...")
    import time
    time.sleep(3)
    
    # 5. 检查设备状态
    print("\n5. 检查设备状态...")
    stdout, stderr, code = run_command("ls -la /dev/video* 2>/dev/null")
    if code == 0:
        print("Video设备:")
        print(stdout)
    
    stdout, stderr, code = run_command("ls -la /dev/bus/usb/* 2>/dev/null")
    if code == 0:
        print("USB设备:")
        print(stdout)
    
    print("\n设备释放完成！")

def check_and_release_devices():
    """检查并释放被占用的设备"""
    print("\n=== 设备占用检查和释放 ===")
    
    # 检查视频设备占用
    print("1. 检查视频设备占用:")
    stdout, stderr, code = run_command("lsof /dev/video* 2>/dev/null")
    if code == 0 and stdout.strip():
        print("发现占用进程:")
        print(stdout)
        
        # 询问是否强制释放
        print("\n是否强制释放被占用的设备? (y/n): ", end="")
        try:
            import sys
            response = input().strip().lower()
            if response == 'y':
                print("正在释放设备...")
                run_command("sudo fuser -k /dev/video* 2>/dev/null")
                run_command("sudo fuser -k /dev/bus/usb/* 2>/dev/null")
                print("设备已释放")
            else:
                print("跳过释放")
        except:
            print("无法获取用户输入，跳过释放")
    else:
        print("没有发现占用进程")
    
    # 检查USB设备占用
    print("\n2. 检查USB设备占用:")
    stdout, stderr, code = run_command("lsof /dev/bus/usb/* 2>/dev/null | head -10")
    if code == 0 and stdout.strip():
        print("发现USB设备占用:")
        print(stdout)
    else:
        print("没有发现USB设备占用")
    
    # 重启udev服务（可选）
    print("\n3. 重启udev服务:")
    stdout, stderr, code = run_command("sudo service udev restart 2>/dev/null")
    if code == 0:
        print("udev服务已重启")
    else:
        print("无法重启udev服务")
    
    # 4. 如果还是有问题，提供强制释放选项
    print("\n4. 如果设备仍然被锁定，是否执行强制释放? (y/n): ", end="")
    try:
        response = input().strip().lower()
        if response == 'y':
            force_release_all_devices()
        else:
            print("跳过强制释放")
    except:
        print("无法获取用户输入，跳过强制释放")

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
                print("    1. 设备被其他进程占用")
                print("    2. 程序异常退出导致设备未释放")
                print("    3. 需要重启容器或主机")
                print("    4. 驱动问题")
                
                # 如果第一次失败，尝试释放设备
                if attempt == 0:
                    print("  尝试释放设备...")
                    run_command("sudo fuser -k /dev/video* 2>/dev/null")
                    run_command("sudo fuser -k /dev/bus/usb/* 2>/dev/null")
                    time.sleep(2)
            
            for i in range(count):
                try:
                    dev = device_list.get_device_by_index(i)
                    dev_info = dev.get_device_info()
                    print(f"  设备 {i}: {dev_info.get_name()} (SN: {dev_info.get_serial_number()})")
                except Exception as e:
                    print(f"  设备 {i}: 访问失败 - {e}")
            
            if attempt < 1:
                time.sleep(2)  # 等待2秒再试
                
    except Exception as e:
        print(f"Orbbec SDK 测试失败: {e}")
        print("可能原因:")
        print("  1. pyorbbecsdk 未正确安装")
        print("  2. 设备被占用")
        print("  3. 需要重启容器")

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
    print("=== 相机设备诊断和修复工具 ===")
    print("1. 运行完整诊断")
    print("2. 直接强制释放所有设备")
    print("3. 退出")
    
    try:
        choice = input("\n请选择 (1-3): ").strip()
        
        if choice == "1":
            diagnose_devices()
            test_usb_access()
            check_and_release_devices()
            test_orbbec_enumeration()
            test_video_devices()
        elif choice == "2":
            force_release_all_devices()
            print("\n=== 释放后重新检测 ===")
            test_orbbec_enumeration()
        elif choice == "3":
            print("退出")
        else:
            print("无效选择，运行完整诊断...")
            diagnose_devices()
            test_usb_access()
            check_and_release_devices()
            test_orbbec_enumeration()
            test_video_devices()
    except KeyboardInterrupt:
        print("\n用户中断")
    except Exception as e:
        print(f"错误: {e}")
        print("运行完整诊断...")
        diagnose_devices()
        test_usb_access()
        check_and_release_devices()
        test_orbbec_enumeration()
        test_video_devices()