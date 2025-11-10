#!/usr/bin/env python3
"""
快速检测测试脚本
最简单的检测功能验证，只需要相机和Web服务
"""

import time
import subprocess
import requests
import json
import os

def start_detection_web():
    """启动检测Web服务"""
    web_dir = os.path.join(os.path.dirname(__file__), "examples/lumi_demo_ali")
    
    if not os.path.exists(web_dir):
        print(f"错误: Web服务目录不存在: {web_dir}")
        return None
    
    lumi_demo_file = os.path.join(web_dir, "lumi_demo_ali.py")
    if not os.path.exists(lumi_demo_file):
        print(f"错误: Web服务文件不存在: {lumi_demo_file}")
        return None
    
    cmd = [
        "python3",
        "lumi_demo_ali.py",
        "--camera-sn", "AY8V74300F4",
        "--port", "7861"
    ]
    
    print(f"启动Web服务: {' '.join(cmd)}")
    print(f"工作目录: {web_dir}")
    
    try:
        proc = subprocess.Popen(cmd, cwd=web_dir)
        print("检测Web服务已启动，等待10秒以确保服务就绪...")
        time.sleep(10)
        return proc
    except Exception as e:
        print(f"启动Web服务失败: {e}")
        return None

def test_web_service():
    """测试Web服务"""
    print("=== 测试Web服务连接 ===")
    
    # 先测试服务是否可访问
    try:
        response = requests.get("http://localhost:7861", timeout=5)
        print(f"Web服务状态: {response.status_code}")
    except Exception as e:
        print(f"Web服务连接失败: {e}")
        return False
    
    # 测试检测接口
    print("\n=== 测试检测接口 ===")
    url = "http://localhost:7861/detect"
    data = {
        "tags": ["西瓜霜润喉片", "红霉素软膏"],
        "conf": 0.2,
        "iou": 0.8
    }
    
    try:
        print(f"发送检测请求...")
        print(f"URL: {url}")
        print(f"数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
        
        response = requests.post(url, json=data, timeout=15)
        
        print(f"\n响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 检测成功！")
            
            labels = result.get("labels", [])
            locs = result.get("locs", [])
            confs = result.get("confs", [])
            depth_data = result.get("depth_data", [])
            
            print(f"\n检测结果:")
            print(f"  检测到的目标数量: {len(labels)}")
            print(f"  标签: {labels}")
            print(f"  位置: {locs}")
            print(f"  置信度: {confs}")
            
            if depth_data:
                import numpy as np
                depth_array = np.array(depth_data)
                print(f"  深度数据形状: {depth_array.shape}")
                print(f"  深度数据范围: {depth_array.min():.3f} - {depth_array.max():.3f}")
            else:
                print("  深度数据: 无")
            
            return True
        else:
            print(f"❌ 检测失败，状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ 请求超时，可能是相机初始化需要更多时间")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 检测出错: {e}")
        return False

def main():
    """主函数"""
    print("=== 快速检测功能测试 ===")
    print("此测试只验证基础的目标检测功能")
    print("需要: 相机连接 + 网络连接")
    print()
    
    # 检查必要文件
    web_dir = os.path.join(os.path.dirname(__file__), "examples/lumi_demo_ali")
    if not os.path.exists(web_dir):
        print(f"❌ Web服务目录不存在: {web_dir}")
        print("请确保项目结构完整")
        return
    
    # 启动Web服务
    web_proc = start_detection_web()
    if web_proc is None:
        print("❌ Web服务启动失败")
        return
    
    try:
        # 等待用户确认
        input("Web服务已启动，请确保目标物体在相机视野内，然后按回车开始测试...")
        
        # 执行测试
        success = test_web_service()
        
        if success:
            print("\n🎉 检测功能测试通过！")
            print("可以继续进行更复杂的测试")
        else:
            print("\n❌ 检测功能测试失败")
            print("请检查:")
            print("1. 相机是否正确连接 (序列号: AY8V74300F4)")
            print("2. 目标物体是否在相机视野内")
            print("3. 光线条件是否适合")
            print("4. 网络连接是否正常")
        
        # 询问是否继续测试
        while True:
            choice = input("\n是否继续测试? (y/n): ").strip().lower()
            if choice == 'y':
                test_web_service()
            elif choice == 'n':
                break
            else:
                print("请输入 y 或 n")
    
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    
    finally:
        # 清理资源
        print("\n清理资源...")
        if web_proc:
            web_proc.terminate()
            try:
                web_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                web_proc.kill()
        print("程序结束")

if __name__ == "__main__":
    main()
