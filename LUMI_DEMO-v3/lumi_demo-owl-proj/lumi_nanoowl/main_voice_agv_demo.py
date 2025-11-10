# main_voice_agv_demo.py
from services.voice_recognition_service import VoiceRecognitionService
from services.voice_synthesis_service import VoiceSynthesisService
from services.agv_control_service import AGVControlService
from services.robot_control_service import RobotControlService
from services.qr_scan_service import QRScanService
from services.object_detection_service import ObjectDetectionService

import subprocess
import time
import os
import threading
import json
import numpy as np
import sys
import tty
import termios

# 添加键盘输入功能
def get_key_press():
    """获取键盘按键输入"""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

def wait_for_key_press(prompt="按任意键继续...", timeout=None):
    """等待键盘按键，带超时功能"""
    print(prompt)
    if timeout:
        print(f"等待 {timeout} 秒...")
        start_time = time.time()
        while time.time() - start_time < timeout:
            if sys.stdin in select.select([sys.stdin], [], [], 0.1)[0]:
                key = get_key_press()
                return key
        return None
    else:
        return get_key_press()

# 添加select模块用于非阻塞输入
import select

# 启动检测Web服务
def start_detection_web():
    # 切换到Web服务目录
    web_dir = os.path.join(os.path.dirname(__file__), "examples/lumi_demo_ali")
    cmd = [
        "python3",
        "lumi_demo_ali.py",
        "--camera-sn", "AY8V74300F4",
        "--port", "7861"
    ]
    proc = subprocess.Popen(cmd, cwd=web_dir)  # 关键点：cwd参数
    print("检测Web服务已启动，等待8秒以确保服务就绪...")
    time.sleep(8)
    return proc

def degrees_to_radians(degrees_list):
    """
    将角度列表转换为弧度列表
    :param degrees_list: 角度列表 [度]
    :return: 弧度列表 [弧度]
    """
    import math
    return [math.radians(angle) for angle in degrees_list]

def move_to_prep_pose(robot, robot_config, pose_type):
    """
    移动到预备姿态
    :param robot: 机器人控制服务
    :param robot_config: 机器人配置
    :param pose_type: 姿态类型 ("grasp" 或 "place")
    :return: 是否成功
    """
    # try:
    #     if pose_type == "grasp":
    #         pose_key = "prepGraspPose"
    #         pose_name = "预备抓取姿态"
    #     elif pose_type == "place":
    #         pose_key = "prepPlacePose"
    #         pose_name = "预备放置姿态"
    #     else:
    #         print(f"未知的姿态类型: {pose_type}")
    #         return False
    try:
        # if pose_type == "grasp":
        pose_key = pose_type
        pose_name = pose_type
        
        # 从配置中获取预备姿态（角度）
        if pose_key not in robot_config["robotParams"]:
            print(f"配置文件中缺少 {pose_key}")
            return False
        
        prep_pose_degrees = robot_config["robotParams"][pose_key]
        print(f"{pose_name}姿态（角度）: {prep_pose_degrees}")
        
        # # 转换为弧度
        # prep_pose_radians = degrees_to_radians(prep_pose_degrees)
        # print(f"{pose_name}姿态（弧度）: {prep_pose_radians}")
        
        # 控制机器人移动到预备姿态
        print(f"正在移动到{pose_name}姿态...")
        success = robot.robot_control.rob_moveto(prep_pose_degrees, 10)  # 速度50%
        
        if success==0:
            # print(f"已到达{pose_name}姿态")
            time.sleep(1)  # 等待机器人稳定
            return True
        else:
            print(f"移动到{pose_name}姿态失败")
            return False
            
    except Exception as e:
        print(f"移动到{pose_name}姿态时出错: {e}")
        return False

def load_robot_config():
    """加载机器人配置"""
    try:
        with open('./conf/userCmdControl-medicine.json', 'r') as f:
            config = json.load(f)
        return config
    except Exception as e:
        print(f"加载机器人配置失败: {e}")
        return None

def calculate_grasp_pose(world_coords, robot_config):
    """
    计算抓取姿态
    :param world_coords: 目标世界坐标 [x, y, z]
    :param robot_config: 机器人配置
    :return: 抓取姿态 [x, y, z, rx, ry, rz]
    """
    # 从配置中获取相对偏移
    relative_offset_x = robot_config["robotParams"]["RelativeOffset-X"]
    relative_offset_y = robot_config["robotParams"]["RelativeOffset-Y"]
    relative_offset_z = robot_config["robotParams"]["RelativeOffset-Z"]
    
    # 计算抓取位置
    grasp_x = world_coords[0] + relative_offset_x
    grasp_y = world_coords[1] + relative_offset_y
    grasp_z = world_coords[2] + relative_offset_z
    
    # 默认抓取姿态（可根据需要调整）
    grasp_rx = 0.0  # 弧度
    grasp_ry = 0.0  # 弧度
    grasp_rz = 0.0  # 弧度
    
    return [grasp_x, grasp_y, grasp_z, grasp_rx, grasp_ry, grasp_rz]

def calculate_place_pose(robot_config):
    """
    计算放置姿态
    :param robot_config: 机器人配置
    :return: 放置姿态 [x, y, z, rx, ry, rz]
    """
    # 从配置中获取放置位置
    put_pose = robot_config["robotParams"]["putPose"]
    put_pose2 = robot_config["robotParams"]["putPose2"]
    
    # 这里可以根据需要选择放置位置
    # 暂时使用第一个放置位置
    return put_pose

def robot_grab_object(robot, world_coords, robot_config, tts, pos_type):
    """
    机器人抓取物体 - 参考multi_station_demo.py的抓取策略
    :param robot: 机器人控制服务
    :param world_coords: 目标世界坐标（从ali检测获得）
    :param robot_config: 机器人配置
    :param tts: 语音合成服务
    :return: 是否成功
    """
    try:
        # tts.speak("开始抓取", block=True)
        print("开始抓取...")
        
        # === 移动到预备抓取姿态 ===
        print("=== 移动到预备抓取姿态 ===")
        # tts.speak("移动到预备抓取姿态", block=True)
        
        prep_success = move_to_prep_pose(robot, robot_config, "prepGraspPose")
        if not prep_success:
            # tts.speak("移动到预备抓取姿态失败", block=True)
            print("移动到预备抓取姿态失败")
            return False
        
        # tts.speak("已到达预备抓取姿态", block=True)
        print("已到达预备抓取姿态")
        robot.robot_control.gripper_open()



        if pos_type == 1:
            ret = move_to_prep_pose(robot, robot_config, "med1G1")
            ret = move_to_prep_pose(robot, robot_config, "med1G2")
        if pos_type == 2:
            ret = move_to_prep_pose(robot, robot_config, "med2G1")
            ret = move_to_prep_pose(robot, robot_config, "med2G2")
        robot.robot_control.gripper_close()
        
        # # 参考multi_station_demo.py的抓取策略
        # # 使用lumi_det_demo中的抓取逻辑，但传入已获得的世界坐标
        
        # # 导入必要的函数
        # from lumi_det_demo import kine_caculate, jointMove
        
        # # 获取当前机器人状态
        # robot_status = robot.get_robot_status()
        # if not robot_status:
        #     # tts.speak("无法获取机器人状态", block=True)
        #     return False
        
        # ref_pos = robot_status["joints"]
        # base_loc_now = robot_status["tcp_position"]
        
        # # 使用kine_caculate计算抓取路径（参考multi_station_demo.py的做法）
        # mv_type, grip_loc, grip_up_loc, base2obj_pos, base2objup_pos, objup2obj_pos, grasp_flag = kine_caculate(
        #     robot.robot_control, ref_pos, base_loc_now, world_coords, robot_config, step_type=-1
        # )
        
        # if grasp_flag != 0:
        #     # tts.speak("目标位置不可达", block=True)
        #     print("目标位置不可达")
        #     return False
        
        # # 执行抓取动作（参考multi_station_demo.py的做法）
        # # tts.speak("执行抓取动作", block=True)
        # print("执行抓取动作...")
        # jointMove(robot.robot_control, mv_type, base2obj_pos, base2objup_pos, objup2obj_pos, grab_status=1)
        
        # # tts.speak("抓取完成", block=True)
        print("抓取完成")
        
        #  回到预备抓取姿态
        back_success = move_to_prep_pose(robot, robot_config, "prepGraspPose")
        if not back_success:
            # tts.speak("移动到预备抓取姿态失败", block=True)
            print("返回失败")
            return False

        return True
        
    except Exception as e:
        print(f"抓取过程中出错: {e}")
        # tts.speak("抓取过程出现异常", block=True)
        return False

def robot_place_object(robot, robot_config, tts,pos_type):
    """
    机器人放置物体 - 参考multi_station_demo.py的put_cola模式
    :param robot: 机器人控制服务
    :param robot_config: 机器人配置
    :param tts: 语音合成服务
    :return: 是否成功
    """
    try:
        tts.speak("开始放置", block=True)
        print("开始放置...")
        
        # === 移动到预备放置姿态 ===
        print("=== 移动到预备放置姿态 ===")
        tts.speak("移动到预备放置姿态", block=True)
        if pos_type == 1:
            prep_success = move_to_prep_pose(robot, robot_config, "putPose2")
        if pos_type ==2:
            prep_success = move_to_prep_pose(robot, robot_config, "putPose1")
        if not prep_success:
            # tts.speak("移动到预备放置姿态失败", block=True)
            print("移动到预备放置姿态失败")
            return False
        
        # tts.speak("已到达预备放置姿态", block=True)
        print("已到达预备放置姿态")
        
        # # 参考multi_station_demo.py中put_cola模式的放置方法
        # # 移动到放置位置1
        # robot.robot_control.rob_moveto([279,60,79,-40,-2,-102], 0)

        
        # 张开夹爪放置 - 使用新的封装方法
        robot.robot_control.gripper_open()
        time.sleep(1)

        # === 原来的夹爪代码（已注释） ===
        # robot.robot_control.grab_action(0)
        # time.sleep(1)
        
        tts.speak("放置完成", block=True)
        print("放置完成")

        prep_success = move_to_prep_pose(robot, robot_config, "back")



        return True
        
    except Exception as e:
        print(f"放置过程中出错: {e}")
        tts.speak("放置过程出现异常", block=True)
        return False

def process_single_target(tts, agv, robot, detector, target_tag, target_index, total_targets,pos_type,idx):
    """
    处理单个目标：检测、抓取、放置
    :param tts: 语音合成服务 (可以为None)
    :param agv: AGV控制服务 (可以为None)
    :param robot: 机器人控制服务
    :param detector: 目标检测服务
    :param target_tag: 目标标签
    :param target_index: 目标索引（从1开始）
    :param total_targets: 总目标数量
    """
    print(f"=== 开始处理第 {target_index}/{total_targets} 个目标: {target_tag} ===")
    if tts:
        tts.speak(f"开始处理第{target_index}个目标", block=True)

    # 加载机器人配置
    robot_config = load_robot_config()
    if not robot_config:
        if tts:
            tts.speak("加载机器人配置失败", block=True)
        print("加载机器人配置失败")
        return False
    
    # === AGV移动到检测位置 ===
    tts.speak("AGV正在前往检测位置", block=True)
    print("AGV正在前往检测位置...")
    agv_ok = agv.move_to_marker("med1")  # 假设有检测区域标记
    if agv_ok:
        tts.speak("AGV已到达检测位置", block=True)
        print("AGV已到达检测位置")
    else:
        tts.speak("AGV移动失败，请检查", block=True)
        print("AGV移动失败")
        return False
    
    # === 目标检测 ===
    if tts:
        tts.speak("正在检测目标", block=True)
    print(f"开始检测目标: {target_tag}")

    # 调用检测服务
    detection_result = detector.detect_objects([target_tag])
    if detection_result["success"]:
        labels = detection_result["labels"]
        locs = detection_result["locs"]
        confs = detection_result["confs"]
        depth_data = detection_result["depth_data"]

        if len(labels) > 0:
            if tts:
                tts.speak(f"检测到{len(labels)}个目标", block=True)
            print(f"检测成功，找到{len(labels)}个目标")
            
            # 获取第一个检测结果（假设只抓取第一个）
            first_label = labels[0]
            first_loc = locs[0]  # [x1, y1, x2, y2]
            first_conf = confs[0]
            
            print(f"目标信息: 标签={first_label}, 位置={first_loc}, 置信度={first_conf}")
            
            # 计算目标中心点坐标
            center_x = int((first_loc[0] + first_loc[2]) / 2)
            center_y = int((first_loc[1] + first_loc[3]) / 2)
            
            # 获取深度信息
            target_depth = depth_data[center_y][center_x]
            print(f"目标中心点: ({center_x}, {center_y}), 深度: {target_depth}")
            
            # === 像素坐标转世界坐标 ===
            if tts:
                tts.speak("正在计算目标位置", block=True)
            print("开始转换像素坐标到世界坐标...")

            # 导入坐标转换函数
            from jaka_utilfs.tools import pixel_to_world
            import json

            # 加载相机标定参数
            try:
                with open('conf/CalibParams-lumi-hand.json', 'r') as f:
                    calib_params = json.load(f)

                # 执行坐标转换
                world_coords = pixel_to_world(
                    [center_x, center_y],
                    target_depth,
                    calib_params["CameraMatrix"],
                    calib_params["RotationMat"],
                    calib_params["TranslationMat"]
                )

                print(f"世界坐标: {world_coords}")
                if tts:
                    tts.speak(f"目标位置计算完成", block=True)

                # 检查深度是否有效
                if target_depth <= 0:
                    if tts:
                        tts.speak("深度信息无效，请检查相机", block=True)
                    print("深度信息无效")
                    return False

            except Exception as e:
                if tts:
                    tts.speak("坐标转换失败", block=True)
                print(f"坐标转换失败: {e}")
                return False
            
            # === 机器人抓取 ===
            if tts:
                tts.speak("机器人开始抓取", block=True)
            print("机器人开始抓取...")


            pos_type1 = pos_type
            print('pos_type1:',pos_type1)
            # 执行机器人抓取
            if tts:
                grab_success = robot_grab_object(robot, world_coords, robot_config, tts,pos_type1)
            else:
                grab_success = robot_grab_object(robot, world_coords, robot_config, None)

        
            if not grab_success:
                if tts:
                    tts.speak("抓取失败，跳过此目标", block=True)
                print("抓取失败")
                return False

            # === AGV移动到放置位置 ===
            if tts:
                tts.speak("AGV正在前往放置位置", block=True)
            print("AGV正在前往放置位置...")
            agv_place_ok = agv.move_to_marker("table")  # 假设有放置区域标记
            if agv_place_ok:
                # if tts:
                    # tts.speak("AGV已到达放置位置", block=True)
                print("AGV已到达放置位置")
            else:
                if tts:
                    tts.speak("AGV移动失败，请检查", block=True)
                print("AGV移动失败")
                return False

            # === 机器人放置 ===
            if tts:
                tts.speak("机器人开始放置", block=True)
            print("机器人开始放置...")

            # 执行机器人放置
            place_success = robot_place_object(robot, robot_config, tts,pos_type1)




            if place_success != 0:
            #     if tts:
            #         tts.speak("放置失败", block=True)
            #     print("放置失败")
                return False

            if tts:
                tts.speak(f"第{target_index}个目标处理完成", block=True)
            print(f"第{target_index}个目标处理完成")
            return True

            # 测试模式下，抓取成功就返回True
            if tts:
                tts.speak(f"第{target_index}个目标抓取完成", block=True)
            print(f"第{target_index}个目标抓取完成")
            return True
            
        else:
            if tts:
                tts.speak("未检测到目标", block=True)
            print("未检测到目标")
            return False
    else:
        if tts:
            tts.speak("检测失败", block=True)
        print(f"检测失败: {detection_result.get('error', '未知错误')}")
        return False

def main():
    # 启动检测Web服务
    web_proc = start_detection_web()
    # 1. 初始化服务（参数后续细化）
    voice_rec = VoiceRecognitionService({
        "wakeup_word": "你好",
        "record_seconds": 3,
        "interval": 2,
        "input_device_name": "AIUI-USB-MC",
        "model_path": "/opt/nanoowl/whisper_main/whisper_models/base.pt",
        "language": "zh",  # 指定语言：zh(中文), en(英文), auto(自动检测)
        "allowed_languages": ["zh", "en"],  # 只允许中文和英文
        "save_audio_files": False,  # 保存语音文件用于调试
        "audio_save_dir": "./debug_audio"  # 语音文件保存目录
    })
    tts = VoiceSynthesisService({
        "appid": "1be4dc2a",
        "apikey": "e4e0a90722f7c18e8e40e9a414f7a100",
        "apisecret": "YTI3YjllMTYwZjczMDJlZTUwZjI3NjI5",
        "output_device_name": "USB Audio Device",
        "volume": 0.5,  # 设置音量，0.0-1.0，1.0表示100%音量（最大音量）
        "speed": 120,  # 设置语速，0-100，默认50，数值越大语速越快
    }); tts.start()
    agv = AGVControlService({
        "agv_ip": "192.168.10.10",
        "agv_port": 31001
    }); agv.start()
    robot = RobotControlService({
        "robot_ip": "192.168.10.90",
        "ext_base_url": "http://192.168.10.90:5000/api/extaxis"
    }); robot.start()
    qr = QRScanService({"camera_serial": "AY8V74300CZ"}); qr.start()
    detector = ObjectDetectionService({
        "camera_serial": "AY8V74300F4",
        "web_url": "http://localhost:7861/detect"
    }); detector.start()



    # 2. 主流程骨架
    try:
        # 初始化外部轴到初始位置
        print("=== 初始化外部轴位置 ===")
        # tts.speak("正在初始化机器人位置", block=True)
        # 检查机器人连接状态
        if not robot.is_connected():
            print("机器人连接失败")
            tts.speak("机器人连接失败，请检查网络", block=True)
            return
        
        # 移动外部轴到初始位置 [100, 0, 0, 0]
        init_result = robot.move_external_axis([2, 0, 0, 0])
        if init_result:
            print("外部轴初始化成功")
            # time.sleep(2)  # 等待移动完成
        else:
            print("外部轴初始化失败")
            # tts.speak("机器人初始化失败，请检查", block=True)
            return
        
        # # === 初始化夹爪 - 使用新的封装方法 ===
        # print("=== 初始化夹爪 ===")
        # try:
        #     # 使用JAKAIntegrated的夹爪初始化和打开方法
        #     if robot.robot_control.gripper_init():
        #         robot.robot_control.gripper_open()
        #         print("夹爪初始化并打开成功")
        #     else:
        #         print("夹爪初始化失败")
        #     time.sleep(1)  # 等待夹爪动作完成
        # except Exception as e:
        #     print(f"夹爪初始化失败: {e}")
        #     # 继续执行，不因为夹爪问题而停止程序

        # === 原来的夹爪代码（已注释） ===
        # try:
        #     # 打开夹爪 (grab_action(0) 表示张开夹爪)
        #     robot.robot_control.grab_action(0)
        #     print("夹爪已打开")
        #     time.sleep(1)  # 等待夹爪动作完成
        # except Exception as e:
        #     print(f"夹爪初始化失败: {e}")
        #     # 继续执行，不因为夹爪问题而停止程序


        # prep = move_to_prep_pose(robot, robot_config, "prepGraspPose")
        
        while True:
            # 语音唤醒环节
            print("=== 等待语音唤醒 ===")
            tts.speak("系统已就绪，请说你好唤醒我", block=False)
            
            # === 选择输入模式 ===
            print("\n=== 请选择输入模式 ===")
            print("1. 语音输入模式 (按 'v' 键)")
            print("2. 键盘输入模式 (按 'k' 键)")
            print("3. 退出程序 (按 'q' 键)")
            
            mode_key = wait_for_key_press("请选择模式 (v/k/q): ", timeout=10)  # 减少到10秒
            
            if mode_key == 'q':
                print("用户选择退出程序")
                return
            elif mode_key == 'v':
                print("选择语音输入模式")
                use_voice_mode = True
            elif mode_key == 'k':
                print("选择键盘输入模式")
                use_voice_mode = False
            else:
                print("无效选择，默认使用语音模式")
                use_voice_mode = True
            
            # === 唤醒检测 ===
            if use_voice_mode:
                # 语音唤醒模式
                print("=== 语音唤醒模式 ===")
                # tts.speak("请说你好唤醒我", block=False)
                
                # 启动唤醒检测
                voice_rec.start_wakeup()
                print("正在等待唤醒词'你好'...")
                
                # 等待唤醒
                if voice_rec.wait_for_wakeup(timeout=60):  # 60秒超时
                    print("检测到唤醒词！")
                    tts.speak("你好啊，我在", block=True)
                else:
                    print("唤醒超时，重新开始")
                    tts.speak("唤醒超时，请重新说你好", block=True)
                    continue
            else:
                # 键盘唤醒模式 - 优化版本
                print("=== 键盘唤醒模式 ===")
                print("按 'w' 键模拟唤醒词'你好'")
                print("按 'q' 键退出程序")
                
                key = wait_for_key_press("等待按键输入...", timeout=15)  # 减少到15秒
                if key == 'w':
                    print("检测到唤醒词！")
                    tts.speak("你好，我在", block=False)
                elif key == 'q':
                    print("用户选择退出程序")
                    return
                else:
                    print("按键超时或无效，重新开始")
                    continue
            
            # 命令识别环节 - 循环等待有效指令
            print("=== 等待语音命令 ===")
            
            while True:  # 新增：循环等待有效指令
                if use_voice_mode:
                    # 语音命令识别模式
                    print("=== 语音命令识别模式 ===")
                    # tts.speak("请说出您的指令", block=False)
                    
                    # 识别命令
                    cmd = voice_rec.recognize_command(record_seconds=5)
                    print(f"识别到的命令: {cmd}")
                else:
                    # 键盘命令识别模式 - 优化版本
                    print("=== 键盘命令识别模式 ===")
                    print("按 'c' 键模拟命令'帮我把桌上的药品拿过来'")
                    print("按 'q' 键退出程序")
                    print("按 's' 键切换回语音模式")
                    
                    key = wait_for_key_press("等待命令输入...", timeout=5)  # 减少到5秒
                    if key == 'c':
                        cmd = "帮我把桌上的药品拿过来"
                        print(f"模拟识别到的命令: {cmd}")
                    elif key == 'q':
                        print("用户选择退出程序")
                        return
                    elif key == 's':
                        print("切换到语音模式")
                        use_voice_mode = True
                        continue
                    else:
                        print("按键超时或无效，请重新输入")
                        tts.speak("未识别到有效指令，请重新说指令", block=True)
                        continue
                
                # 检查是否是目标命令 # 帮我把桌上的药品拿过来
                if "桌上" in cmd:
                    print("识别到目标命令！")
                    tts.speak("收到，即将前往桌子为您服务", block=False)
                    
                    # === AGV移动到桌子 ===
                    # tts.speak("AGV正在前往桌子", block=True)
                    print("AGV正在前往桌子...")
                    agv_ok = agv.move_to_marker("table")  # 假设AGV功能正常
                    if agv_ok:
                        # tts.speak("AGV已到达桌子", block=True)
                        print("AGV已到达桌子")
                    else:
                        tts.speak("AGV移动失败，请检查", block=True)
                        print("AGV移动失败")
                        return
                    
                    # === 智能机器人扫码流程 ===
                    print("开始智能扫码流程...")

                    # 1. 语音播报独立执行
                    tts.speak("机器人正在扫码", block=False)
                    
                    # 移动外部轴到扫码位置
                    ext_scan_pos = [3, 0, 0, 35]  # 扫码位置
                    robot.move_external_axis(ext_scan_pos)
                    
                    # # === 相机位置调整提示 ===
                    # print("=== 相机位置调整 ===")
                    # print("当前相机位置: [3, 0, 0, 35]")
                    # print("如果只检测到1个二维码，可以调整相机位置：")
                    # print("按 '1' 键：调整到位置 [0, 0, 0, 35] (更近)")
                    # print("按 '2' 键：调整到位置 [6, 0, 0, 35] (更远)")
                    # print("按 '3' 键：调整到位置 [3, 0, 0, 25] (角度更平)")
                    # print("按 '4' 键：调整到位置 [3, 0, 0, 45] (角度更陡)")
                    # print("按 's' 键：开始扫码")
                    
                    # adjust_key = wait_for_key_press("请选择相机位置调整 (1/2/3/4/s): ", timeout=8)  # 减少到8秒
                    # if adjust_key == '1':
                    #     ext_scan_pos = [0, 0, 0, 35]
                    #     robot.move_external_axis(ext_scan_pos)
                    #     print("已调整到更近位置")
                    # elif adjust_key == '2':
                    #     ext_scan_pos = [6, 0, 0, 35]
                    #     robot.move_external_axis(ext_scan_pos)
                    #     print("已调整到更远位置")
                    # elif adjust_key == '3':
                    #     ext_scan_pos = [3, 0, 0, 25]
                    #     robot.move_external_axis(ext_scan_pos)
                    #     print("已调整到更平角度")
                    # elif adjust_key == '4':
                    #     ext_scan_pos = [3, 0, 0, 45]
                    #     robot.move_external_axis(ext_scan_pos)
                    #     print("已调整到更陡角度")
                    # elif adjust_key == 's':
                    #     print("使用默认位置开始扫码")
                    # else:
                    #     print("使用默认位置开始扫码")
                    
                    # # === 二维码扫码获取目标tag ===
                    # tts.speak("正在扫码", block=True)
                    print("开始扫码二维码...")
                    
                    # 扫码获取目标tags（支持多个二维码）
                    try:
                        # # 添加调试信息
                        # print("=== 扫码调试信息 ===")
                        # print(f"使用相机序列号: {qr.config.get('camera_serial', '未知')}")
                        # print("请确保多个二维码都在相机视野内")
                        # print("建议：将多个二维码放在同一平面上，距离相机30-50cm")
                        
                        qr_results = qr.scan_qr_codes(timeout=10)  # 减少到20秒
                        
                        # 详细输出扫码结果
                        print(f"=== 扫码结果详情 ===")
                        # print(f"返回结果类型: {type(qr_results)}")
                        # print(f"返回结果长度: {len(qr_results) if qr_results else 0}")
                        # print(f"返回结果内容: {qr_results}")
                        
                        if qr_results and len(qr_results) > 0:
                            target_tags = qr_results  # 获取所有二维码内容
                            tts.speak(f"扫码成功，检测到{len(target_tags)}个目标", block=True)
                            print(f"扫码成功，目标tags: {target_tags}")
                            
                            # # 如果只检测到1个二维码，给出提示
                            # if len(target_tags) == 1:
                            #     print("⚠️  只检测到1个二维码，可能的原因：")
                            #     print("   1. 视野内只有1个二维码")
                            #     print("   2. 其他二维码距离太远或角度不对")
                            #     print("   3. 其他二维码质量不好或模糊")
                            #     print("   4. 相机位置需要调整")
                                
                            #     # 询问是否继续
                            #     print("\n是否继续处理这1个目标？")
                            #     print("按 'y' 继续，按 'n' 重新扫码")
                            #     continue_key = wait_for_key_press("请选择 (y/n): ", timeout=5)  # 减少到5秒
                            #     if continue_key == 'n':
                            #         print("重新开始扫码...")
                            #         continue  # 重新扫码
                            
                            # === 依次处理每个目标 ===
                            success_count = 0

                            # if len(target_tags) == 1:
                            target_tags = ["西瓜霜润喉片", "红霉素软膏"]
                            for i, target_tag in enumerate(target_tags):
                                target_index = i + 1
                                total_targets = len(target_tags)
                                
                                print(f"\n=== 开始处理第 {target_index}/{total_targets} 个目标 ===")
                                print("----target_tag-------:", target_tag)   
                                if "西瓜霜润喉片" in target_tag:
                                    pos_type = 1
                                if "红霉素软膏" in target_tag:
                                    pos_type = 2
                                # 处理单个目标
                                print('----------pos_type--------:',pos_type)
                                success = process_single_target(
                                    tts, agv, robot, detector, 
                                    target_tag, target_index, total_targets,pos_type,idx=i
                                )
                            
                                if success:
                                    success_count += 1
                                else:
                                    tts.speak(f"第{target_index}个目标处理失败，继续下一个", block=True)
                                    print(f"第{target_index}个目标处理失败")
                                
                                # 如果不是最后一个目标，等待一下再处理下一个
                                if target_index < total_targets:
                                    time.sleep(2)
                            
                            # 总结处理结果
                            if success_count == total_targets:
                                tts.speak(f"所有{total_targets}个目标处理完成", block=True)
                                print(f"所有{total_targets}个目标处理完成")
                            elif success_count > 0:
                                tts.speak(f"处理完成，成功{success_count}个，失败{total_targets - success_count}个", block=True)
                                print(f"处理完成，成功{success_count}个，失败{total_targets - success_count}个")
                            else:
                                tts.speak("所有目标处理失败", block=True)
                                print("所有目标处理失败")
                                
                        else:
                            tts.speak("扫码失败，请检查二维码", block=True)
                            print("扫码失败")
                            print("可能的原因：")
                            print("1. 二维码不在相机视野内")
                            print("2. 二维码距离太远或太近")
                            print("3. 光线不足或过强")
                            print("4. 二维码模糊或损坏")
                            return
                    except Exception as e:
                        print(f"扫码过程中出现异常: {e}")
                        tts.speak("扫码出现异常，请检查相机", block=True)
                        return

                    # === 处理完成，跳出内层循环 ===
                    break  # 跳出内层循环，继续外层循环

                else:
                    print("未识别到有效指令")
                    tts.speak("未识别到有效指令，请重新说指令", block=True)
                    # 继续等待指令，不返回唤醒流程
                    continue  # 继续内层循环，等待下一个指令
                
    finally:
        tts.stop()
        agv.stop()
        robot.stop()
        qr.stop()
        detector.stop()
        voice_rec.close()
        # 关闭Web服务
        web_proc.terminate()

def test_detection_grasp_only(target_labels=None):
    """
    单独测试视觉检测+抓取功能
    不包含语音、AGV等功能，专注于检测和抓取流程
    :param target_labels: 要检测的目标标签列表，如 ["西瓜霜润喉片", "红霉素软膏"]
    """
    print("=== 视觉检测+抓取功能测试 ===")

    # 默认测试目标
    if target_labels is None:
        target_labels = ["西瓜霜润喉片", "红霉素软膏"]

    print(f"测试目标: {target_labels}")

    # 启动检测Web服务
    web_proc = start_detection_web()

    try:
        # 初始化必要的服务
        print("初始化服务...")

        # 机器人控制服务
        robot = RobotControlService({
            "robot_ip": "192.168.10.90",
            "ext_base_url": "http://192.168.10.90:5000/api/extaxis"
        })
        robot.start()

        # 检测服务
        detector = ObjectDetectionService({
            "camera_serial": "AY8V74300F4",
            "web_url": "http://localhost:7861/detect"
        })
        detector.start()

        # 检查机器人连接状态
        if not robot.is_connected():
            print("❌ 机器人连接失败")
            return False

        print("✅ 机器人连接成功")

        # # 初始化外部轴到初始位置
        # print("初始化外部轴位置...")
        # init_result = robot.move_external_axis([2, 0, 0, 0])
        # if init_result:
        #     print("✅ 外部轴初始化成功")
        # else:
        #     print("❌ 外部轴初始化失败")
        #     return False

        # 初始化夹爪 - 使用新的封装方法
        print("初始化夹爪...")
        try:
            if robot.robot_control.gripper_init():
                robot.robot_control.gripper_open()
                print("✅ 夹爪初始化并打开成功")
            else:
                print("⚠️ 夹爪初始化失败")
            time.sleep(1)
        except Exception as e:
            print(f"⚠️ 夹爪初始化失败: {e}")

        # === 原来的夹爪代码（已注释） ===
        # try:
        #     robot.robot_control.grab_action(0)
        #     print("✅ 夹爪已打开")
        #     time.sleep(1)
        # except Exception as e:
        #     print(f"⚠️ 夹爪初始化失败: {e}")

        # 加载机器人配置
        robot_config = load_robot_config()
        if not robot_config:
            print("❌ 加载机器人配置失败")
            return False

        print("✅ 机器人配置加载成功")

        # 测试每个目标
        success_count = 0
        total_targets = len(target_labels)

        for i, target_label in enumerate(target_labels):
            target_index = i + 1
            print(f"\n=== 测试目标 {target_index}/{total_targets}: {target_label} ===")

            # 调用现有的处理函数，但不使用TTS和AGV
            success = process_single_target(
                tts=None,  # 不使用TTS
                agv=None,  # 不使用AGV
                robot=robot,
                detector=detector,
                target_tag=target_label,
                target_index=target_index,
                total_targets=total_targets
            )

            if success:
                success_count += 1
                print(f"✅ 目标 {target_label} 处理成功")
            else:
                print(f"❌ 目标 {target_label} 处理失败")

            # 如果不是最后一个目标，等待一下
            if target_index < total_targets:
                print("等待3秒后处理下一个目标...")
                time.sleep(3)

        # 输出测试结果
        print(f"\n=== 测试结果 ===")
        print(f"总目标数: {total_targets}")
        print(f"成功数: {success_count}")
        print(f"失败数: {total_targets - success_count}")
        print(f"成功率: {success_count/total_targets*100:.1f}%")

        if success_count == total_targets:
            print("🎉 所有目标测试通过！")
            return True
        elif success_count > 0:
            print("⚠️ 部分目标测试通过")
            return True
        else:
            print("❌ 所有目标测试失败")
            return False

    except Exception as e:
        print(f"❌ 测试过程中出现异常: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # 清理资源
        print("\n清理资源...")
        try:
            robot.stop()
            detector.stop()
            web_proc.terminate()
        except:
            pass
        print("测试结束")

def test_detection_only(target_labels=None):
    """
    仅测试检测功能，不执行抓取
    用于快速验证检测服务是否正常
    """
    print("=== 仅检测功能测试 ===")

    # 默认测试目标
    if target_labels is None:
        target_labels = ["西瓜霜润喉片", "红霉素软膏"]

    print(f"测试目标: {target_labels}")

    # 启动检测Web服务
    web_proc = start_detection_web()

    try:
        # 初始化检测服务
        detector = ObjectDetectionService({
            "camera_serial": "AY8V74300F4",
            "web_url": "http://localhost:7861/detect"
        })
        detector.start()

        # 执行检测
        print("开始检测...")
        detection_result = detector.detect_objects(target_labels)

        if detection_result["success"]:
            labels = detection_result["labels"]
            locs = detection_result["locs"]
            confs = detection_result["confs"]
            depth_data = detection_result["depth_data"]

            print("✅ 检测成功！")
            print(f"检测到的目标数量: {len(labels)}")
            print(f"标签: {labels}")
            print(f"位置: {locs}")
            print(f"置信度: {confs}")

            if depth_data:
                import numpy as np
                depth_array = np.array(depth_data)
                print(f"深度数据形状: {depth_array.shape}")
                print(f"深度数据范围: {depth_array.min():.3f} - {depth_array.max():.3f}")

            return True
        else:
            print(f"❌ 检测失败: {detection_result.get('error', '未知错误')}")
            return False

    except Exception as e:
        print(f"❌ 测试过程中出现异常: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # 清理资源
        print("清理资源...")
        try:
            detector.stop()
            web_proc.terminate()
        except:
            pass
        print("测试结束")

if __name__ == "__main__":
    import sys

    # 检查命令行参数
    if len(sys.argv) > 1:
        if sys.argv[1] == "test_detection":
            # 仅测试检测功能
            test_labels = sys.argv[2:] if len(sys.argv) > 2 else None
            test_detection_only(test_labels)
        elif sys.argv[1] == "test_grasp":
            # 测试检测+抓取功能
            test_labels = sys.argv[2:] if len(sys.argv) > 2 else None
            test_detection_grasp_only(test_labels)
        else:
            print("用法:")
            print("  python3 main_voice_agv_demo.py                    # 运行完整程序")
            print("  python3 main_voice_agv_demo.py test_detection     # 仅测试检测功能")
            print("  python3 main_voice_agv_demo.py test_grasp         # 测试检测+抓取功能")
            print("  python3 main_voice_agv_demo.py test_detection 目标1 目标2  # 指定测试目标")
    else:
        # 运行完整程序
        main()