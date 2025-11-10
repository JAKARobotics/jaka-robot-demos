#!/usr/bin/env python3
# coding:UTF-8

import time
import numpy as np
from jaka_utilfs.jaka import JAKA

def execute_robot_sequence():
    """
    执行机器人运动序列：
    1. 关节运动到第一次位置
    2. 关节运动到第二次位置
    3. 相对直线运动 z-60mm
    """
    
    # 机器人IP
    robot_ip = "192.168.10.90"
    
    # 第一次位置的关节角度（从你的测试结果复制）
    position1_joints = [-1.2427667453012297, 1.9872379605474098, 1.2117954113111526, 
                       -1.6717702158391754, -0.9488859665799617, 1.0826192659403806]
    
    # 第二次位置的关节角度（从你的测试结果复制）
    position2_joints = [-1.2531690523098895, 0.8689180517684788, 0.8639892431022482, 
                       -3.689410311880618, -1.0411525122708292, 4.501670625782143]
    
    print("开始机器人运动序列...")
    
    # 连接机器人
    robot = JAKA(robot_ip, connect=False)
    robot.jaka_connect()
    print("机器人已连接")
    
    try:
        # 步骤1: 移动到第一次位置
        print("\n步骤1: 关节运动到位置1")
        print(f"目标关节角度: {[f'{np.degrees(j):.1f}°' for j in position1_joints]}")
        
        result = robot.joint_move_origin(position1_joints, 15, 0)
        if result == 0:
            print("✅ 到达位置1")
        else:
            print(f"❌ 移动失败: {result}")
            return
        
        time.sleep(2)
        
        # 步骤2: 移动到第二次位置
        print("\n步骤2: 关节运动到位置2")
        print(f"目标关节角度: {[f'{np.degrees(j):.1f}°' for j in position2_joints]}")
        
        result = robot.joint_move_origin(position2_joints, 15, 0)
        if result == 0:
            print("✅ 到达位置2")
        else:
            print(f"❌ 移动失败: {result}")
            return
        
        time.sleep(2)
        
        # 步骤3: 直线运动 z-60mm
        print("\n步骤3: 直线运动 z-60mm")
        
        # 获取当前TCP位置
        current_tcp = robot.get_tcp_pos()
        print(f"当前TCP位置: [{current_tcp[0]:.1f}, {current_tcp[1]:.1f}, {current_tcp[2]:.1f}]")
        
        # 计算目标位置
        target_tcp = list(current_tcp)
        target_tcp[2] -= 60.0  # Z轴减少60mm
        print(f"目标TCP位置: [{target_tcp[0]:.1f}, {target_tcp[1]:.1f}, {target_tcp[2]:.1f}]")
        
        # 执行直线运动
        result = robot.liner_move(target_tcp, 20)
        if result == 0:
            print("✅ 直线运动完成")
            
            # 验证最终位置
            final_tcp = robot.get_tcp_pos()
            actual_z_move = final_tcp[2] - current_tcp[2]
            print(f"实际Z轴移动: {actual_z_move:.1f} mm")
        else:
            print(f"❌ 直线运动失败: {result}")
            return
        
        print("\n🎉 所有运动完成！")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        
    finally:
        # 断开连接
        robot.robot_disconnect()
        print("机器人已断开连接")

if __name__ == "__main__":
    execute_robot_sequence()
