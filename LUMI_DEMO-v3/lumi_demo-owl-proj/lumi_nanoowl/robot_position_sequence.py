#!/usr/bin/env python3
# coding:UTF-8

import time
import sys
import os
import numpy as np
from jaka_utilfs.jaka import JAKA

def robot_position_sequence():
    """
    实现机器人位置序列运动：
    1. 关节运动到第一次位置
    2. 关节运动到第二次位置  
    3. 相对直线运动 z-60mm
    """
    
    # 机器人IP地址
    robot_ip = "192.168.10.90"
    
    # 第一次位置的关节角度（弧度）
    position1_joints = [-1.2427667453012297, 1.9872379605474098, 1.2117954113111526, 
                       -1.6717702158391754, -0.9488859665799617, 1.0826192659403806]
    
    # 第二次位置的关节角度（弧度）
    position2_joints = [-1.2531690523098895, 0.8689180517684788, 0.8639892431022482, 
                       -3.689410311880618, -1.0411525122708292, 4.501670625782143]
    
    print("=== 机器人位置序列运动 ===")
    print(f"连接机器人: {robot_ip}")
    
    try:
        # 连接机器人
        robot = JAKA(robot_ip, connect=False)
        robot.jaka_connect()
        print("机器人连接成功")
        time.sleep(2)
        
        # 获取当前位置
        current_joints = robot.getjoints()
        current_tcp = robot.get_tcp_pos()
        
        print(f"\n当前关节位置 (弧度): {current_joints}")
        print(f"当前TCP位置: {current_tcp}")
        
        # 步骤1: 关节运动到第一次位置
        print("\n=== 步骤1: 关节运动到第一次位置 ===")
        
        # 转换为度数显示
        position1_degrees = [np.degrees(j) for j in position1_joints]
        print(f"目标关节角度 (弧度): {position1_joints}")
        print(f"目标关节角度 (度数): {[f'{deg:.2f}°' for deg in position1_degrees]}")

        return
        
        # 执行关节运动
        print("开始关节运动到位置1...")
        result = robot.joint_move_origin(position1_joints, 15, 0)  # 速度15%, 绝对模式
        
        if result == 0:
            print("✅ 成功到达位置1")
            time.sleep(1)
            
            # 验证位置
            actual_joints1 = robot.getjoints()
            actual_tcp1 = robot.get_tcp_pos()
            print(f"实际到达的关节位置: {actual_joints1}")
            print(f"实际到达的TCP位置: {actual_tcp1}")
        else:
            print(f"❌ 关节运动到位置1失败，错误代码: {result}")
            return
        
        time.sleep(2)
        
        # 步骤2: 关节运动到第二次位置
        print("\n=== 步骤2: 关节运动到第二次位置 ===")
        
        # 转换为度数显示
        position2_degrees = [np.degrees(j) for j in position2_joints]
        print(f"目标关节角度 (弧度): {position2_joints}")
        print(f"目标关节角度 (度数): {[f'{deg:.2f}°' for deg in position2_degrees]}")
        
        # 执行关节运动
        print("开始关节运动到位置2...")
        result = robot.joint_move_origin(position2_joints, 15, 0)  # 速度15%, 绝对模式
        
        if result == 0:
            print("✅ 成功到达位置2")
            time.sleep(1)
            
            # 验证位置
            actual_joints2 = robot.getjoints()
            actual_tcp2 = robot.get_tcp_pos()
            print(f"实际到达的关节位置: {actual_joints2}")
            print(f"实际到达的TCP位置: {actual_tcp2}")
        else:
            print(f"❌ 关节运动到位置2失败，错误代码: {result}")
            return
        
        time.sleep(2)
        
        # 步骤3: 相对直线运动 z-60mm
        print("\n=== 步骤3: 相对直线运动 z-60mm ===")
        
        # 获取当前TCP位置
        current_tcp_final = robot.get_tcp_pos()
        print(f"当前TCP位置: {current_tcp_final}")
        print(f"当前Z坐标: {current_tcp_final[2]:.3f} mm")
        
        # 计算目标位置（Z轴减少60mm）
        target_tcp = list(current_tcp_final)
        target_tcp[2] -= 60.0  # Z轴减少60mm
        
        print(f"目标TCP位置: {target_tcp}")
        print(f"目标Z坐标: {target_tcp[2]:.3f} mm")
        print(f"Z轴移动距离: -60.0 mm")
        
        # 执行直线运动
        print("开始直线运动 z-60mm...")
        result = robot.liner_move(target_tcp, 20)  # 速度20%
        
        if result == 0:
            print("✅ 直线运动完成")
            time.sleep(1)
            
            # 验证最终位置
            final_tcp = robot.get_tcp_pos()
            print(f"最终TCP位置: {final_tcp}")
            print(f"最终Z坐标: {final_tcp[2]:.3f} mm")
            print(f"实际Z轴移动: {final_tcp[2] - current_tcp_final[2]:.3f} mm")
        else:
            print(f"❌ 直线运动失败，错误代码: {result}")
            return
        
        print("\n🎉 所有运动序列完成！")
        
        # 运动总结
        print("\n=== 运动序列总结 ===")
        print("1. ✅ 关节运动到位置1")
        print("2. ✅ 关节运动到位置2") 
        print("3. ✅ 相对直线运动 z-60mm")
        
    except Exception as e:
        print(f"❌ 运动过程中发生错误: {e}")
        
    finally:
        try:
            # 断开机器人连接
            print("\n断开机器人连接...")
            robot.robot_disconnect()
            print("机器人连接已断开")
        except:
            pass

def safe_robot_sequence():
    """
    安全版本的机器人运动序列，包含更多检查和确认
    """
    
    # 机器人IP地址
    robot_ip = "192.168.10.90"
    
    # 第一次位置的关节角度（弧度）
    position1_joints = [-1.2427667453012297, 1.9872379605474098, 1.2117954113111526, 
                       -1.6717702158391754, -0.9488859665799617, 1.0826192659403806]
    
    # 第二次位置的关节角度（弧度）
    position2_joints = [-1.2531690523098895, 0.8689180517684788, 0.8639892431022482, 
                       -3.689410311880618, -1.0411525122708292, 4.501670625782143]
    
    print("=== 安全版机器人位置序列运动 ===")
    
    # 显示即将执行的运动
    print("\n即将执行的运动序列:")
    print("1. 关节运动到位置1")
    print("2. 关节运动到位置2")
    print("3. 相对直线运动 z-60mm")
    
    # 用户确认
    confirm = input("\n是否继续执行？(y/N): ").strip().lower()
    if confirm != 'y':
        print("运动序列已取消")
        return
    
    try:
        # 连接机器人
        robot = JAKA(robot_ip, connect=False)
        robot.jaka_connect()
        print("机器人连接成功")
        time.sleep(2)
        
        # 步骤1: 关节运动到第一次位置
        print("\n=== 步骤1: 关节运动到第一次位置 ===")
        print("准备移动到位置1...")
        time.sleep(2)
        
        result = robot.joint_move_origin(position1_joints, 10, 0)  # 较慢速度10%
        if result == 0:
            print("✅ 成功到达位置1")
            time.sleep(3)  # 等待稳定
        else:
            print(f"❌ 运动失败，错误代码: {result}")
            return
        
        # 步骤2: 关节运动到第二次位置
        print("\n=== 步骤2: 关节运动到第二次位置 ===")
        print("准备移动到位置2...")
        time.sleep(2)
        
        result = robot.joint_move_origin(position2_joints, 10, 0)  # 较慢速度10%
        if result == 0:
            print("✅ 成功到达位置2")
            time.sleep(3)  # 等待稳定
        else:
            print(f"❌ 运动失败，错误代码: {result}")
            return
        
        # 步骤3: 相对直线运动 z-60mm
        print("\n=== 步骤3: 相对直线运动 z-60mm ===")
        
        current_tcp = robot.get_tcp_pos()
        target_tcp = list(current_tcp)
        target_tcp[2] -= 60.0  # Z轴减少60mm
        
        print(f"当前Z: {current_tcp[2]:.3f} mm")
        print(f"目标Z: {target_tcp[2]:.3f} mm")
        print("准备执行直线运动...")
        time.sleep(2)
        
        result = robot.liner_move(target_tcp, 15)  # 较慢速度15%
        if result == 0:
            print("✅ 直线运动完成")
            
            # 验证最终位置
            final_tcp = robot.get_tcp_pos()
            actual_movement = final_tcp[2] - current_tcp[2]
            print(f"实际Z轴移动: {actual_movement:.3f} mm")
        else:
            print(f"❌ 直线运动失败，错误代码: {result}")
            return
        
        print("\n🎉 安全运动序列完成！")
        
    except Exception as e:
        print(f"❌ 运动过程中发生错误: {e}")
        
    finally:
        try:
            robot.robot_disconnect()
            print("机器人连接已断开")
        except:
            pass

def main():
    """主函数，提供选择菜单"""
    print("机器人位置序列运动程序")
    print("=" * 40)
    print("1. 标准运动序列")
    print("2. 安全运动序列（包含确认步骤）")
    print("3. 退出")
    
    choice = input("\n请选择 (1-3): ").strip()
    
    if choice == "1":
        robot_position_sequence()
    elif choice == "2":
        safe_robot_sequence()
    elif choice == "3":
        print("程序退出")
    else:
        print("无效选择")

if __name__ == "__main__":
    main()
