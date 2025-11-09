## 大模型分拣应用 
### 描述
基于视觉大模型进行机器人分拣应用场景 

### 账号注册链接：
- [阿里大模型账号注册](https://help.aliyun.com/zh/dashscope/?spm=a2c4g.11186623.0.0.36b87defCVLRg8)
- [dashscope_api_key获取](https://dashscope.console.aliyun.com/apiKey)

### 环境配置说明
- pip install -r requirements.txt
- [Orbbec相机配置](https://github.com/orbbec/pyorbbecsdk)
- JAKA机器人： 需要添加JAKA_SDK_LINUX文件夹路径到环境变量，export LD_LIBRARY_PATH=/xx/xx/


### 程序说明 
- conf/CalibParams.json 相机手眼标定结果
- conf/userCmdControl.json  配置文件，运行程序前需要提前配置相应参数
```
{
  
  "cameraParams": {
    "align_mode":"SW",
    "enable_sync":true,    
    "saveImgPath": "./images/project1"  # 保存检测图像路径
  },

  "objects": {
    "moveObjects": "yellow doll",  # 待抓取物体
    "putObject": "box"            # 待放置位置 
  },

  "robotParams": {
    "basePose": [1.779982726648774, -0.5317580611819244, -1.0753665373391599, -0.5535891796159754, -1.1916992728855895, 1.244266479103587],  # 自定义机器人的初始姿态
    "relativeUpMotionHeight": 100,  # 抓取后抬起的相对高度（mm）
    "RelativeOffset-Z":50,          # 微调抓取位置Z方向位置（mm）
    "RelativeOffset-Zput":50,       # 微调放置时位置Z方向位置（mm）
    "RelativeOffset-X": 50,         # 微调抓取位置X方向位置（mm）
    "RelativeOffset-Y": 30          # 微调抓取位置Y方向位置（mm）
  },

  "calibrateParams": {
    "robotIP": "192.168.10.90",     # 机器人IP
    "CalibrateImageSaveDir": "./lumi_handCam/",     # 标定结果保存路径
    "boardRowNums": 8,                              # 标定板参数    
    "boardCowNums": 11,                             # 标定板参数
    "boardLength": 10                               # 标定板参数
  },

  "genNearPointParams":{
    "nearPointInterval": 20,   # 搜索范围，单位像素
    "nearPointTimes": 20       # 搜索次数
  }
}
```
- AutoCalibProccess.py 用于手动手眼标定 （已有CalibParams.json是基于lumi扶手位置相机进行标定的结果，可以直接使用。）
- visualDetect_ali.py 基于视觉进行机器人分拣应用，识别**待抓取物体**和**目标位置**，将物体抓取后放到目标位置。 


