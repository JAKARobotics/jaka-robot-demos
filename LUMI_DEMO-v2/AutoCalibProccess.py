"""
AutoCalibProccess.py - 机器人手眼标定程序

功能：
    - 交互式采集标定板图像和机器人TCP位姿
    - 自动检测标定板角点
    - 执行手眼标定计算
    - 保存标定结果

使用方法：
    1. 配置 conf/userCmdControl.json 中的参数
    2. 运行程序: python AutoCalibProccess.py
    3. 按 'k' 键采集数据（建议15-30组）
    4. 按 'p' 键开始标定
    5. 按 'q' 键退出程序

详细说明请参考: AutoCalibProccess_使用说明.md
"""
from utilfs.handToEyeCalibration import *
import cv2
from OrbbecSDK.orbbecCamera import Camera
import getch
from utilfs.jaka import *
from utilfs.tools import loadJsonFile,findCorners
import os
from datetime import datetime

PI=3.1415926

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONF_DIR = os.path.join(SCRIPT_DIR, 'conf')
PROJECTS_DIR = os.path.join(SCRIPT_DIR, 'calibrate_projects')

# Load configuration file using absolute path
config_path = os.path.join(CONF_DIR, 'userCmdControl.json')
mapJsonData = loadJsonFile(config_path)

boardRowNums=mapJsonData["calibrateParams"]["boardRowNums"]
boardCowNums = mapJsonData["calibrateParams"]["boardCowNums"]
boardLength = mapJsonData["calibrateParams"]["boardLength"]

# Get project name from config
project_name = mapJsonData["calibrateParams"].get("projectName", "default_project")
if not project_name or project_name.strip() == "":
    project_name = f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# Create project directory structure
project_dir = os.path.join(PROJECTS_DIR, project_name)
project_images_dir = os.path.join(project_dir, 'images')
project_conf_dir = os.path.join(project_dir, 'conf')

# Create directories if they don't exist
for dir_path in [project_dir, project_images_dir, project_conf_dir]:
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
        print(f"创建项目目录: {dir_path}")

print(f"当前项目名称: {project_name}")
print(f"项目目录: {project_dir}")

# Set paths with project name prefix
CalibrateImageSaveDir = project_images_dir
save_path = os.path.join(project_dir, f'{project_name}_robotTcpPos.txt')
calib_result_save_path = os.path.join(project_conf_dir, f'{project_name}_CalibParams.json')

print(f'标定图像保存目录: {CalibrateImageSaveDir}')
print(f'机器人位姿保存路径: {save_path}')
print(f'标定结果保存路径: {calib_result_save_path}')

tcp = JAKA(mapJsonData["calibrateParams"]["robotIP"])
oberrecCamera = Camera()



startIndex=0
robotPoses = []
calibrateImages = []
print('--------------请按下k进行数据采集-------')
print('--------------请按下p开始标定-------')
print('--------------请按下q退出程序-------')
while True:
    key = getch.getch()  # 读取按键
    keystr = key
    print(keystr)

    if keystr == 'k':
        print("开始采集数据...")
        currentTcpPos = tcp.get_tcp_pos()
        print("currentTcpPos: ",currentTcpPos)

        color_image = oberrecCamera.getColorImage()
        print("get color_image  success.")

        if findCorners(color_image,boardRowNums,boardCowNums):
            robotPoses.append(currentTcpPos)
            calibrateImages.append(color_image)
            # Save image with project name prefix
            image_filename = f'{project_name}_calib_image_{startIndex:04d}.png'
            cv2.imwrite(os.path.join(CalibrateImageSaveDir, image_filename), color_image)
            startIndex+=1
            print(f"本次数据采集成功，已保存: {image_filename}")
        else:
            print("舍弃本次采集...")

    if keystr == 'p':
        print("开始标定...")
        if len(calibrateImages)==len(robotPoses):
            print("数据一致,开始标定")
            np.savetxt(save_path,robotPoses, fmt='%f', delimiter=',')
            print(f"位姿保存成功: {save_path}")
            
            calibrator = Calibration(boardRowNums, boardCowNums, boardLength, project_name=project_name)
            calibrator.process(calibrateImages, robotPoses, calib_result_save_path=calib_result_save_path)
            print(f"\n标定完成！所有文件已保存到项目目录: {project_dir}")
            print(f"  - 标定图像: {project_images_dir}")
            print(f"  - 机器人位姿: {save_path}")
            print(f"  - 标定结果: {calib_result_save_path}")
        else:
            print(f"图像和位姿数量不一致... (图像: {len(calibrateImages)}, 位姿: {len(robotPoses)})")

    if keystr == 'q':
        print("退出程序...")
        break









