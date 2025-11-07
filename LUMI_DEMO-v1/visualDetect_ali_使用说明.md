# visualDetect_ali.py 使用说明

## 功能简介

`visualDetect_ali.py` 是一个基于视觉大模型的机器人自动分拣应用。它使用阿里云视觉大模型API识别待抓取物体和目标放置位置，通过Orbbec 3D相机获取深度信息，将像素坐标转换为机器人世界坐标，并控制JAKA机器人完成自动抓取和放置任务。

## 主要功能

- ✅ 基于阿里云视觉大模型的物体检测
- ✅ 3D深度信息获取（Orbbec相机）
- ✅ 像素坐标到世界坐标的转换
- ✅ 机器人运动学逆解计算
- ✅ 自动抓取和放置操作
- ✅ 循环检测和抓取（支持连续作业）
- ✅ 详细的调试信息输出

## 环境要求

### 硬件要求
- JAKA 机器人（已连接并配置IP）
- Orbbec 3D相机（已连接）
- 机器人末端执行器（夹爪/吸盘等）

### 软件要求
- Python 3.10+
- 已安装以下依赖：
  - `opencv-python`
  - `numpy`
  - `dashscope` (阿里云视觉大模型SDK)
  - `pyorbbecsdk` (Orbbec SDK)
  - JAKA SDK

### 环境变量配置

#### 1. 阿里云API密钥配置
```bash
export DASHSCOPE_API_KEY="your_api_key_here"
```

**获取API密钥：**
- [阿里云DashScope控制台](https://dashscope.console.aliyun.com/apiKey)
- 注册账号并创建API密钥

#### 2. JAKA SDK库路径配置
```bash
export LD_LIBRARY_PATH=/path/to/JAKA_SDK_LINUX:$LD_LIBRARY_PATH
```

## 配置文件说明

### 配置文件位置
`conf/userCmdControl.json` 和 `conf/CalibParams.json`

### userCmdControl.json 配置项

```json
{
  "cameraParams": {
    "align_mode": "SW",                    // 对齐模式
    "enable_sync": true,                   // 启用同步
    "saveImgPath": "./images/project1"     // 图像保存路径
  },
  
  "objects": {
    "moveObjects": "bottle",               // 待抓取物体名称（英文）
    "putObject": "people"                  // 目标放置位置名称（英文）
  },
  
  "robotParams": {
    "basePose": [1.78, -0.53, -1.08, ...], // 机器人初始姿态（6个关节角度，弧度）
    "relativeUpMotionHeight": 100,         // 抓取后抬起高度（mm）
    "RelativeOffset-Z": 50,                // 抓取位置Z方向偏移（mm）
    "RelativeOffset-Zput": 50,             // 放置位置Z方向偏移（mm）
    "RelativeOffset-X": 50,                // 抓取位置X方向偏移（mm）
    "RelativeOffset-Y": 30                 // 抓取位置Y方向偏移（mm）
  },
  
  "calibrateParams": {
    "robotIP": "192.168.10.90"             // 机器人IP地址
  },
  
  "genNearPointParams": {
    "nearPointInterval": 20,               // 深度搜索范围（像素）
    "nearPointTimes": 20                   // 深度搜索次数
  }
}
```

### CalibParams.json 配置项

标定结果文件，包含相机内参和手眼标定结果。通常通过 `AutoCalibProccess.py` 生成。

```json
{
  "CameraMatrix": [[...]],           // 相机内参矩阵
  "CameraDistCoeffs": [[...]],       // 相机畸变系数
  "RotationMat": [[...]],            // 相机到基坐标系的旋转矩阵
  "TranslationMat": [[...]]          // 相机到基坐标系的平移向量
}
```

### 配置项详细说明

| 配置项 | 说明 | 示例值 | 注意事项 |
|--------|------|--------|----------|
| `moveObjects` | 待抓取物体名称 | `"bottle"`, `"yellow doll"` | 使用英文名称，需与视觉模型识别结果一致 |
| `putObject` | 目标放置位置名称 | `"people"`, `"box"` | 使用英文名称，需与视觉模型识别结果一致 |
| `basePose` | 机器人初始姿态 | `[1.78, -0.53, ...]` | 6个关节角度（弧度），确保在机器人工作空间内 |
| `relativeUpMotionHeight` | 抬起高度 | `100` (mm) | 抓取后抬起的相对高度，避免碰撞 |
| `RelativeOffset-X/Y/Z` | 位置偏移 | `50`, `30`, `50` (mm) | 用于微调抓取位置，根据实际情况调整 |
| `RelativeOffset-Zput` | 放置Z偏移 | `50` (mm) | 放置时的Z方向偏移 |
| `nearPointInterval` | 深度搜索范围 | `20` (像素) | 当深度为0时，搜索周围点的范围 |
| `nearPointTimes` | 深度搜索次数 | `20` | 深度搜索的最大尝试次数 |

## 使用步骤

### 1. 准备工作

#### 1.1 安装依赖
```bash
cd LUMI_DEMO-v1
pip install -r requirements.txt
```

#### 1.2 配置阿里云API密钥
```bash
export DASHSCOPE_API_KEY="your_api_key_here"
```

或者添加到 `~/.bashrc` 或 `~/.zshrc`：
```bash
echo 'export DASHSCOPE_API_KEY="your_api_key_here"' >> ~/.bashrc
source ~/.bashrc
```

#### 1.3 配置JAKA SDK库路径
```bash
export LD_LIBRARY_PATH=/path/to/JAKA_SDK_LINUX:$LD_LIBRARY_PATH
```

#### 1.4 完成手眼标定
确保 `conf/CalibParams.json` 文件存在且正确。如果未标定，请先运行：
```bash
python AutoCalibProccess.py
```

#### 1.5 配置参数
编辑 `conf/userCmdControl.json`：
- 设置机器人IP地址
- 设置待抓取物体名称（`moveObjects`）
- 设置目标放置位置名称（`putObject`）
- 调整机器人初始姿态（`basePose`）
- 调整位置偏移参数（根据实际情况）

### 2. 运行程序

```bash
cd LUMI_DEMO-v1
python visualDetect_ali.py
```

### 3. 程序执行流程

程序启动后会：

1. **初始化连接**
   - 连接JAKA机器人
   - 初始化Orbbec相机
   - 加载配置文件

2. **移动到初始位置**
   - 机器人移动到 `basePose` 位置
   - 打开夹爪

3. **进入循环检测**
   - 获取相机图像（RGB + 深度）
   - 保存图像到指定路径
   - 调用阿里云视觉API检测物体
   - 处理检测结果
   - 计算世界坐标
   - 执行抓取和放置操作
   - 返回初始位置
   - 重复循环

## 工作流程详解

### 1. 图像采集
```
相机初始化 → 获取RGB图像 → 获取深度数据 → 保存图像
```

### 2. 物体检测
```
调用阿里云API → 返回检测结果 → 解析边界框 → 分类物体（抓取/放置）
```

### 3. 坐标转换
```
像素坐标 → 深度值 → 世界坐标 → 机器人基坐标系
```

**坐标转换流程：**
1. 计算物体中心点像素坐标
2. 获取对应位置的深度值
3. 如果深度为0，搜索周围点
4. 使用标定参数将像素坐标转换为世界坐标
5. 应用位置偏移（X, Y, Z）

### 4. 运动规划
```
计算抓取位置 → 计算抬起位置 → 逆运动学求解 → 选择运动路径
```

**运动路径类型：**
- **类型1 (mv_type=1)**: 基座 → 物体位置（直接抓取）
- **类型2 (mv_type=2)**: 基座 → 物体上方 → 物体位置（分步抓取）

### 5. 抓取操作
```
移动到物体上方 → 移动到物体位置 → 关闭夹爪 → 抬起 → 移动到放置位置上方 → 移动到放置位置 → 打开夹爪 → 抬起 → 返回初始位置
```

## 输出信息说明

程序运行时会输出详细的调试信息：

### 1. 图像信息
```
[图像保存] 保存图像到: /path/to/image.jpg
[图像保存] 图像已保存: /path/to/image.jpg
[图像检查] 保存的图像大小: 245.32 KB
[图像信息] 图像尺寸: 640x480
```

### 2. 检测结果
```
【检测结果】
检测到的物体数量: 2

物体 1:
  标签: bottle
  边界框坐标 (x1, y1, x2, y2): [100, 150, 200, 250]
  边界框宽度: 100 pixels
  边界框高度: 100 pixels
```

### 3. 坐标信息
```
【移动物体 1 坐标信息】
  像素坐标: (150, 200)
  深度值: 850 mm
  世界坐标 (X, Y, Z): (125.345, 230.567, 850.123) mm

【放置物体坐标信息】
  像素坐标: (320, 240)
  深度值: 900 mm
  世界坐标 (X, Y, Z): (200.123, 150.456, 900.789) mm
```

### 4. 运动状态
```
---Start Capture--
base move 2 obj-up success
obj move 2 obj-up success
---Start Place---
```

## 常见问题

### Q1: 检测不到物体或检测结果为空

**可能原因：**
- API密钥未设置或错误
- 物体名称配置错误（与API识别结果不一致）
- 图像质量问题（光线不足、模糊等）
- 物体不在相机视野内

**解决方法：**
1. 检查环境变量：`echo $DASHSCOPE_API_KEY`
2. 查看程序输出的API调用信息，确认API是否正常响应
3. 检查图像是否正常保存
4. 尝试使用更通用的物体名称（如 "object", "item"）
5. 查看 `utilfs/tools.py` 中的详细调试信息

### Q2: 深度值为0，无法获取深度信息

**可能原因：**
- 物体表面反光或透明
- 距离超出相机测量范围
- 物体边缘或背景

**解决方法：**
- 程序会自动搜索周围点的深度值
- 调整 `genNearPointParams` 中的搜索参数
- 改善光照条件
- 确保物体在相机有效测量范围内

### Q3: 机器人运动失败或报错

**可能原因：**
- 目标位置超出机器人工作空间
- 机器人未上电或未使能
- 运动路径中有障碍物
- 逆运动学求解失败

**解决方法：**
1. 检查机器人连接状态
2. 确认目标位置在机器人工作空间内
3. 调整 `basePose` 使机器人处于合适位置
4. 调整位置偏移参数（`RelativeOffset-X/Y/Z`）
5. 检查是否有碰撞风险

### Q4: 抓取位置不准确

**可能原因：**
- 手眼标定精度不够
- 位置偏移参数设置不当
- 物体检测边界框不准确

**解决方法：**
1. 重新进行手眼标定，提高标定精度
2. 根据实际抓取效果调整 `RelativeOffset-X/Y/Z`
3. 检查标定结果文件 `CalibParams.json` 是否正确
4. 使用更准确的物体检测结果

### Q5: API调用失败或超时

**可能原因：**
- 网络连接问题
- API密钥无效或过期
- API调用频率限制
- 图像文件过大

**解决方法：**
1. 检查网络连接：`ping dashscope.aliyuncs.com`
2. 验证API密钥有效性
3. 查看API返回的错误信息
4. 检查图像文件大小，必要时压缩图像

### Q6: 程序一直循环，无法停止

**解决方法：**
- 按 `Ctrl+C` 强制停止程序
- 程序设计为循环检测，如需单次执行，可修改 `detect_continue` 变量

## 调试技巧

### 1. 启用详细日志
程序已包含详细的调试信息输出，包括：
- API请求和响应
- 图像保存状态
- 检测结果
- 坐标转换结果
- 机器人运动状态

### 2. 检查图像质量
- 查看保存的图像文件
- 确认物体清晰可见
- 检查边界框是否准确

### 3. 验证坐标转换
- 对比像素坐标和世界坐标
- 使用标定板验证转换精度
- 检查深度值是否合理

### 4. 测试机器人运动
- 先手动测试机器人能否到达目标位置
- 逐步调整位置偏移参数
- 确认运动路径无碰撞

## 注意事项

### ⚠️ 安全警告

1. **运行前检查**
   - 确保机器人工作空间内无人员
   - 确认夹爪/末端执行器安装正确
   - 检查急停按钮可用

2. **运动安全**
   - 首次运行时建议降低运动速度
   - 确认 `basePose` 位置安全
   - 检查运动路径无障碍物

3. **物体检测**
   - 确保物体名称配置正确
   - 避免检测到错误物体
   - 确认放置位置安全

### 📋 使用建议

1. **首次使用**
   - 先进行手眼标定
   - 使用简单物体测试（如瓶子、盒子）
   - 逐步调整参数

2. **参数调整**
   - `RelativeOffset-X/Y/Z`: 根据抓取效果微调
   - `relativeUpMotionHeight`: 根据物体高度调整
   - `basePose`: 确保机器人处于合适位置

3. **物体选择**
   - 使用形状规则、颜色鲜明的物体
   - 避免透明、反光物体
   - 确保物体在相机视野内

4. **环境要求**
   - 充足的光照
   - 稳定的相机位置
   - 清晰的背景（避免干扰检测）

## 代码结构说明

### 主要函数

- **`kine_caculate()`**: 计算抓取/放置位置的运动学逆解
- **`jointMove()`**: 执行机器人关节运动
- **`vl_ali()`**: 调用阿里云视觉API进行物体检测
- **`pixel_to_world()`**: 像素坐标到世界坐标转换
- **`generatorNearPoints()`**: 生成周围搜索点（用于深度搜索）

### 工作流程

```
主循环:
  1. 获取图像（RGB + 深度）
  2. 保存图像
  3. 调用视觉API检测
  4. 处理检测结果
  5. 计算世界坐标
  6. 规划运动路径
  7. 执行抓取
  8. 执行放置
  9. 返回初始位置
  10. 重复
```

## 相关文档

- [AutoCalibProccess.py 使用说明](./AutoCalibProccess_使用说明.md) - 手眼标定程序
- [README.md](./README.md) - 项目总体说明
- [阿里云DashScope文档](https://help.aliyun.com/zh/dashscope/)
- [Orbbec SDK文档](https://github.com/orbbec/pyorbbecsdk)

## 更新日志

- 2025-01-07: 添加详细的调试信息输出
- 2025-01-07: 改进图像保存路径管理
- 2025-01-07: 添加坐标信息打印
- 2025-01-07: 增强API错误处理

