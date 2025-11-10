import time
import cv2
import os
# from orbbecCamera import Camera
from multi_camera_manager import Camera
from jaka_utilfs.jaka import *
from jaka_utilfs.tools import loadJsonFile, saveOriginImg, generatorNearPoints, pixel_to_world

# import threading
# import glob
# import random
# from audio_tool.audio_tools import play_wav, get_device, play_random_wav_from_folder, play_tts
from audio_tool.audio_tools import play_tts
import numpy as np
import requests

step_flag = None # -1：catch 1：put
IO_TOOL = 1 # Grab IO
PI=3.1415926

def try_inverse_with_rz(robot, grip_loc, ref_pos, max_delta=30, step=5):
    """
    尝试不同rz角度（角度制），如果不可达，再尝试调整ry、rx，直到逆解成功。
    返回(base2obj_pos, grip_loc) 或 (None, None)
    """
    original_rz = grip_loc[5]
    original_ry = grip_loc[4]
    original_rx = grip_loc[3]
    original_rz_deg = np.rad2deg(original_rz)
    original_ry_deg = np.rad2deg(original_ry)
    original_rx_deg = np.rad2deg(original_rx)
    tried = set()
    # 先尝试原始rz角度
    for delta in range(0, max_delta + 1, step):
        for sign in [1, -1] if delta != 0 else [1]:
            new_rz_deg = original_rz_deg + sign * delta
            if (new_rz_deg,) in tried:
                continue
            tried.add((new_rz_deg,))
            grip_loc[5] = np.deg2rad(new_rz_deg)
            if hasattr(robot, 'kine_inverse_origin'):
                base2obj_pos = robot.kine_inverse_origin(ref_pos, tuple(grip_loc))
            else:
                base2obj_pos = robot.kine_inverse(ref_pos, tuple(grip_loc))
            if base2obj_pos[0] == 0:
                return base2obj_pos, tuple(grip_loc)
    # 如果rz全部尝试失败，尝试调整ry
    for delta in range(0, max_delta + 1, step):
        for sign in [1, -1] if delta != 0 else [1]:
            new_ry_deg = original_ry_deg + sign * delta
            if ("ry", new_ry_deg) in tried:
                continue
            tried.add(("ry", new_ry_deg))
            grip_loc[4] = np.deg2rad(new_ry_deg)
            grip_loc[5] = original_rz  # 恢复rz
            if hasattr(robot, 'kine_inverse_origin'):
                base2obj_pos = robot.kine_inverse_origin(ref_pos, tuple(grip_loc))
            else:
                base2obj_pos = robot.kine_inverse(ref_pos, tuple(grip_loc))
            if base2obj_pos[0] == 0:
                return base2obj_pos, tuple(grip_loc)
    # 如果ry也失败，尝试调整rx
    for delta in range(0, max_delta + 1, step):
        for sign in [1, -1] if delta != 0 else [1]:
            new_rx_deg = original_rx_deg + sign * delta
            if ("rx", new_rx_deg) in tried:
                continue
            tried.add(("rx", new_rx_deg))
            grip_loc[3] = np.deg2rad(new_rx_deg)
            grip_loc[4] = original_ry  # 恢复ry
            grip_loc[5] = original_rz  # 恢复rz
            if hasattr(robot, 'kine_inverse_origin'):
                base2obj_pos = robot.kine_inverse_origin(ref_pos, tuple(grip_loc))
            else:
                base2obj_pos = robot.kine_inverse(ref_pos, tuple(grip_loc))
            if base2obj_pos[0] == 0:
                return base2obj_pos, tuple(grip_loc)
    return None, None


def kine_caculate(robot, ref_pos, base_loc, world_loc, mapJsonData, step_type, max_delta=30, step=5):
    base2objup_pos = None
    objup2obj_pos = None
    grasp_flag = None
    mv_type = -1

    grip_loc = tuple(world_loc.tolist() + list(base_loc[3:]))  # A
    # obj cartesian_pose
    grip_loc = list(grip_loc)
    grip_loc[0] += mapJsonData["robotParams"]["RelativeOffset-X"]
    grip_loc[1] += mapJsonData["robotParams"]["RelativeOffset-Y"]

    if step_type == -1:
        # catch
        grip_loc[2] += mapJsonData["robotParams"]["RelativeOffset-Z"]
    elif step_type == 1:
        # put
        grip_loc[2] += mapJsonData["robotParams"]["RelativeOffset-Zput"]

    # obj-up cartesian_pose
    grip_loc_up = grip_loc[:]
    grip_loc_up[2] = grip_loc_up[2] + mapJsonData["robotParams"]["relativeUpMotionHeight"]

    # base 2 obj
    base2obj_pos, grip_loc_used = try_inverse_with_rz(robot, grip_loc[:], ref_pos, max_delta, step)
    if base2obj_pos is None:
        # 全部尝试失败
        grasp_flag = 1  # 标记为失败
        return mv_type, tuple(grip_loc), tuple(grip_loc_up), None, None, None, grasp_flag

    # base 2 obj-up
    base2objup_pos, grip_loc_up_used = try_inverse_with_rz(robot, grip_loc_up[:], ref_pos, max_delta, step)
    # if base2obj-up failure, turn to base2a
    if base2objup_pos is None or base2objup_pos[0] != 0:
        grasp_flag = base2obj_pos[0]
        mv_type = 1
    # if base2obj-up success, turn to obj-up2obj
    elif base2objup_pos[0] == 0:
        # 尝试 objup2obj 逆解
        if hasattr(robot, 'kine_inverse_origin'):
            objup2obj_pos = robot.kine_inverse_origin(base2objup_pos[1], grip_loc_used)
        else:
            objup2obj_pos = robot.kine_inverse(base2objup_pos[1], grip_loc_used)
        if objup2obj_pos[0] == 0:
            grasp_flag = objup2obj_pos[0]
            mv_type = 2
        else:
            grasp_flag = base2obj_pos[0]
            mv_type = 1
    return mv_type, grip_loc_used, grip_loc_up_used, base2obj_pos, base2objup_pos, objup2obj_pos, grasp_flag


def jointMove(robot, mv_type,base2obj_pos,base2objup_pos,objup2obj_pos,grab_status):
    # base move 2 obj-up 2 obj 
    if mv_type == 2: # base move 2 obj-up
        # Check which method to use based on what's available in the robot object
        if hasattr(robot, 'joint_move_origin'):
            ret_base2objup = robot.joint_move_origin(base2objup_pos[1], 1, 0)
        else:
            ret_base2objup = robot.joint_move(joint_pos=base2objup_pos[1], move_mode=0, is_block=True, speed=30)
            
        if ret_base2objup == 0 or (isinstance(ret_base2objup, tuple) and ret_base2objup[0] == 0):
            # time.sleep(1)
            
            if hasattr(robot, 'joint_move_origin'):
                ret_move2obj = robot.joint_move_origin(objup2obj_pos[1], 1, 0)
            else:
                ret_move2obj = robot.joint_move(joint_pos=objup2obj_pos[1], move_mode=0, is_block=True, speed=30)
                
            if ret_move2obj == 0 or (isinstance(ret_move2obj, tuple) and ret_move2obj[0] == 0):
                robot.grab_action(grab_status)
                time.sleep(1)
                
                if hasattr(robot, 'joint_move_origin'):
                    moveRet = robot.joint_move_origin(base2objup_pos[1], 1, 0)
                else:
                    moveRet = robot.joint_move(joint_pos=base2objup_pos[1], move_mode=0, is_block=True, speed=30)
                    
                if moveRet == 0 or (isinstance(moveRet, tuple) and moveRet[0] == 0):
                    print("obj move 2 obj-up success")
                else:
                    print("obj move 2 obj-up failure")
                # time.sleep(1)

            else:
                print("obj-up move 2 obj failure")    
        else:
            print("base move 2 obj-up failure")   
    # base 2 obj
    if mv_type == 1:
        if hasattr(robot, 'joint_move_origin'):
            ret_move2obj = robot.joint_move_origin(base2obj_pos[1], 1, 0)
        else:
            ret_move2obj = robot.joint_move(joint_pos=base2obj_pos[1], move_mode=0, is_block=True, speed=30)
            
        if ret_move2obj == 0 or (isinstance(ret_move2obj, tuple) and ret_move2obj[0] == 0):
            # time.sleep(1)
            robot.grab_action(grab_status)
            time.sleep(1)
            print('next: obj move 2 put-up')
        else:
            print("base move 2 obj failure")
    return 

def show_unreachable_warning(image, status_text, auto_execute=False):
    """显示不可达警告窗口"""
    print('Warning: Position unreachable!')
    print(f"STATUS: {status_text}")
    
    # 如果不是自动执行模式，显示窗口等待用户确认
    if not auto_execute:
        # 在显示窗口中添加状态文本
        cv2.putText(image, f"STATUS: {status_text}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)
        cv2.namedWindow("Object Detection - UNREACHABLE", cv2.WINDOW_NORMAL)
        cv2.imshow("Object Detection - UNREACHABLE", image)
        print("Press any key to continue...")
        cv2.waitKey(0)  # 等待任意按键
        cv2.destroyAllWindows()
    
    print('Continuing to next detection cycle...')

# 程序启动时
# device_id = get_device()

def get_detection_from_web(tags, conf=0.2, iou=0.8, web_url="http://localhost:7860/detect"):
    data = {
        "tags": tags,
        "conf": conf,
        "iou": iou
    }
    resp = requests.post(web_url, json=data)
    result = resp.json()
    if 'error' in result:
        print("Web服务未准备好帧，稍后重试")
        return [], [], [], None
    # 还原深度数据
    depth_data = np.array(result['depth_data'], dtype=np.float32)
    return result['labels'], result['locs'], result['confs'], depth_data

def run_detection(robot=None, auto_execute=False, camera_serial_number=None, detect_mode="realtime", tags=None):
    """
    只保留抓取模式（grasp_only）：
    检测到目标后，依次判断每个目标是否可抓取（逆解成功），可抓取则立即执行抓取动作。
    每次抓取后机器人回到基准位。检测不到目标时，播放wav语音。
    detect_mode: 'realtime'（递出后立即检测），'batch'（一次检测抓完所有目标）
    tags: 外部传入的检测目标物列表（如['可乐']），优先级高于配置文件
    """
    mapJsonData = loadJsonFile('./conf/userCmdControl-doll.json')
    calibParams = loadJsonFile('./conf/CalibParams-head0717.json')
    # 检测结果图片保存目录
    det_img_save_dir =mapJsonData["detection_results"]
    if not os.path.exists(det_img_save_dir):
        os.makedirs(det_img_save_dir)
    # 机器人初始化
    if robot is None:
        robot = JAKA(mapJsonData["calibrateParams"]["robotIP"], connect=True)
        robot._login()
    base_loc = mapJsonData["robotParams"]["basePose"]
    put_loc = mapJsonData["robotParams"]["putPose"]
    put_loc2 = mapJsonData["robotParams"]["putPose2"]
    robot.joint_move_origin(base_loc, 1, 0)
    print("机器人回到基准位")
    robot.grab_action(0)  # 张开夹爪
    time.sleep(1)
    # 优先使用传入的tags，否则用配置文件
    if tags is not None and len(tags) > 0:
        mv_obj = tags[0]
    else:
        mv_obj = mapJsonData["objects"]["moveObjects"]
    tags = [mv_obj]
    print(f"仅抓取模式：只检测 '{mv_obj}'")

    detect_continue = True
    while detect_continue:
        # 检测目标
        obj_labels, obj_locs, obj_confs, depth_data = get_detection_from_web(tags, conf=0.2, iou=0.8)
        print("检测到目标:", obj_labels, obj_locs, obj_confs)
        if len(obj_labels) == 0:
            print('--------')
            print("未检测到目标，播放语音")
            tts_volume_value = mapJsonData.get("ttsVolume", 2.0)
            play_tts("未检测到目标。", volume=tts_volume_value, block=True)
            continue

        # 依次处理每个目标
        any_grasped = False  # 新增
        for idx, (label, loc) in enumerate(zip(obj_labels, obj_locs)):
            print(f"处理目标{idx+1}: {label}, 坐标: {loc}")
            center_x = int((loc[0] + loc[2]) / 2)
            center_y = int((loc[1] + loc[3]) / 2)
            mv_obj_depth = depth_data[int(center_y)][int(center_x)]
            if int(mv_obj_depth) == 0:
                print("中心点深度为0，尝试周围点")
                gen_center_points = generatorNearPoints([center_x, center_y], mapJsonData["genNearPointParams"]["nearPointInterval"], mapJsonData["genNearPointParams"]["nearPointTimes"])
                for point in gen_center_points:
                    try:
                        x, y = int(point[0]), int(point[1])
                        mv_obj_depth = depth_data[int(y)][int(x)]
                    except Exception:
                        continue
                    if int(mv_obj_depth) != 0:
                        break
            print(f"目标深度: {mv_obj_depth}")
            obj_world_loc = pixel_to_world([center_x, center_y], mv_obj_depth, calibParams["CameraMatrix"], calibParams["RotationMat"], calibParams["TranslationMat"])
            # # ------------z轴安全高度限制---------
            # min_z = mapJsonData["robotParams"].get("minZforSafe", None)
            # if min_z is not None and obj_world_loc[2] < min_z:
            #     print(f"z轴高度{obj_world_loc[2]:.3f}过低，修正为安全高度{min_z:.3f}")
            #     obj_world_loc[2] = min_z
            # print(f"目标世界坐标: {obj_world_loc}")
            #---

            ref_pos = robot.getjoints()
            base_loc_now = robot.get_tcp_pos()
            # 逆解判断可达性
            mv_type, grip_loc, grip_up_loc, base2obj_pos, base2objup_pos, objup2obj_pos, grasp_flag = kine_caculate(robot, ref_pos, base_loc_now, obj_world_loc, mapJsonData, step_type=-1)
            if grasp_flag == 0:
                # # 播放随机音频（非阻塞，稳定）
                # play_random_wav_from_folder('/home/jaka/AI_CODES/lumi_demo/audio_tool/auido_file-doll', volume=3.0)
                # TTS语音合成并播放
                tts_volume_value = mapJsonData.get("ttsVolume", 2.0)
                play_tts(f"检测到目标{label}，已准备抓取。", volume=tts_volume_value)
                print(f"目标{idx+1}可抓取，执行抓取动作")
                jointMove(robot, mv_type, base2obj_pos, base2objup_pos, objup2obj_pos, grab_status=1)
                # print("抓取完成，回到基准位")
                # robot.joint_move_origin(base_loc, 1, 0)
                
                time.sleep(0.5)
                print("抓取完成，传递出去")
                robot.joint_move_origin(put_loc, 1, 0)
                robot.joint_move_origin(put_loc2,1,0)
                time.sleep(1)
                robot.grab_action(0)  # 张开夹爪
                time.sleep(3)

                robot.joint_move_origin(base_loc, 1, 0)
                # 根据detect_mode决定是否break
                if detect_mode == "realtime":
                    break
                # 抓取成功
                any_grasped = True
            else:
                print(f"目标{idx+1}不可达，跳过")

        # 处理完所有目标后
        if not any_grasped:
            print("所有目标都不可达，播放语音")
            # play_random_wav_from_folder('/home/jaka/AI_CODES/lumi_demo/audio_tool/audio_file-nodoll', volume=1.0)
            tts_volume_value = mapJsonData.get("ttsVolume", 2.0)
            play_tts("未检测到可抓取的目标，请调整物体位置后重试。", volume=tts_volume_value, block=True)

            

if __name__=='__main__':
    
    import argparse
    parser = argparse.ArgumentParser(description='运行视觉检测和抓取任务')
    parser.add_argument('--auto', action='store_true', help='自动执行模式，不等待用户确认')
    parser.add_argument('--camera-sn', type=str, default='AY8V74300F4', help='指定要使用的相机序列号')  # AY8V74300F4  hand #  AY8V74300CZ head
    parser.add_argument('--list-cameras', action='store_true', help='列出所有可用的相机')
    parser.add_argument('--detect-mode', type=str, choices=['realtime', 'batch'], default='realtime', help='检测模式：realtime为递出后立即检测，batch为一次检测抓完所有目标')
    args = parser.parse_args()
    if args.list_cameras:
        try:
            print("正在搜索连接的Orbbec相机...")
            temp_cam = Camera()
            devices = temp_cam.list_connected_devices()
            temp_cam.close()
            if not devices:
                print("没有找到连接的Orbbec相机")
            else:
                print("\n可用的Orbbec相机:")
                for device in devices:
                    print(f"索引: {device['index']}, 名称: {device['name']}, 序列号: {device['serial_number']}")
                print("\n使用方法: python visualDetect_ali.py --camera-sn <序列号>")
                if args.camera_sn is None and devices:
                    args.camera_sn = devices[0]["serial_number"]
                    print(f"\n自动选择第一个相机: {args.camera_sn}")
        except Exception as e:
            print(f"列出相机时出错: {e}")
            import traceback
            traceback.print_exc()
        exit(0)
    try:
        print(f"使用相机序列号: {args.camera_sn if args.camera_sn else '默认'}")
        run_detection(auto_execute=args.auto, camera_serial_number=args.camera_sn, detect_mode=args.detect_mode)
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"运行过程中出错: {e}")
        import traceback
        traceback.print_exc()


        

 