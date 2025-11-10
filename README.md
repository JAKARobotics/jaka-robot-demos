# jaka-robot-demos
Demo repository for JAKA robots

## 项目目录

### [LUMI_DEMO-v1](./LUMI_DEMO-v1/) - 原地固定位置视觉抓取

基于视觉大模型的机器人分拣应用，适用于**单站点固定位置**的视觉抓取场景。

**主要功能：**
- ✅ 基于阿里云视觉大模型的物体检测
- ✅ 手眼标定（`AutoCalibProccess.py`）
- ✅ 视觉识别与抓取（`visualDetect_ali.py`）
- ✅ 3D深度信息获取（Orbbec相机）

**适用场景：** 固定工位、单一工作区域的视觉分拣任务

**详细文档：**
- [README.md](./LUMI_DEMO-v1/README.md) - 快速入门
- [visualDetect_ali 使用说明](./LUMI_DEMO-v1/visualDetect_ali_使用说明.md) - 详细使用指南
- [AutoCalibProccess 使用说明](./LUMI_DEMO-v1/AutoCalibProccess_使用说明.md) - 标定指南

---

### [LUMI_DEMO-v2](./LUMI_DEMO-v2/) - 多站点移动分拣 ⭐

基于视觉大模型的**移动式多站点分拣**机器人应用，支持AGV联动和外部轴控制。

**主要功能：**
- ✅ **多站点任务调度**：机器人可移动到不同站点执行分拣任务
- ✅ **AGV联动**：支持与AGV（自动导引车）协同作业
- ✅ **外部轴控制**：支持机器人安装在外部轴上，扩大工作范围
- ✅ **智能任务分配**：根据站点配置自动调度任务
- ✅ 多站点手眼标定
- ✅ 视觉识别与抓取

**适用场景：** 多站点、移动式分拣、AGV协同作业等复杂场景

**详细文档：**
- [项目使用说明](./LUMI_DEMO-v2/项目使用说明.md) - 完整使用指南
- [标定说明](./LUMI_DEMO-v2/标定.md) - 标定相关文档

---

### [LUMI_DEMO-v3](./LUMI_DEMO-v3/) - 语音交互智能分拣 🎤🤖

基于 **NanoOWL** 和 **语音唤醒**的智能交互式机器人应用，支持语音控制、实时目标检测和自动化任务执行。

**演示视频：**

https://github.com/user-attachments/assets/f381e13f-12a6-46af-a55c-c2592527c4f3

**主要功能：**
- ✅ **语音唤醒与交互**：基于 Whisper 的语音识别，支持自定义唤醒词（默认："lumi"）
- ✅ **实时目标检测**：基于 NanoOWL（OWL-ViT）的零样本目标检测
- ✅ **语音合成反馈**：支持两种 TTS 方案
  - **讯飞 TTS**：在线服务，需要 API 密钥，音质稳定
  - **MeloTTS**：本地离线方案，无需 API，支持多语言（中文、英文、日语、韩语等），可在 CPU 上实时推理
- ✅ **二维码识别**：基于 Orbbec 相机的二维码自动扫描和解析
- ✅ **多相机支持**：支持多个 Orbbec 相机同时工作
- ✅ **AGV 协同**：支持 AGV 移动和机械臂控制
- ✅ **任务编排**：复杂任务的自动化执行（如药品抓取任务）
- ✅ **Docker 容器化部署**：ARM 架构（aarch64）优化，基于 NVIDIA Jetson Orin 平台

**系统架构：**
```
start_voice_wakeup_system.py (启动脚本/入口)
    ↓
voice_wakeup_system.py (核心系统/主控制器)
    ↓
各个服务模块 (VoiceRecognitionService, VoiceSynthesisService 等)
    ↓
底层实现 (QR_SCAN.py, multi_camera_manager.py 等)
```

**核心组件：**
- **语音识别服务** (`services/voice_recognition_service.py`) - 基于 Whisper 的语音识别
- **语音合成服务** (`services/voice_synthesis_service.py`) - 支持讯飞 TTS 和 MeloTTS 两种方案
- **二维码扫描服务** (`services/qr_scan_service.py`) - 基于 Orbbec 相机的二维码识别
- **目标检测服务** (`services/object_detection_service.py`) - 基于 Owl 的目标检测
- **AGV 控制服务** (`services/agv_control_service.py`) - AGV 移动控制
- **机器人控制服务** (`services/robot_control_service.py`) - 机械臂控制

**适用场景：** 语音交互、智能仓储、移动式多站点分拣、人机协作、药品抓取等场景

**技术特点：**
- 🐳 **Docker 容器化**：完整的 Docker 部署方案，支持 ARM 架构
- 🚀 **NVIDIA Jetson 优化**：针对 Jetson Orin 平台进行 TensorRT 优化
- 🎯 **零样本检测**：无需训练即可检测任意目标
- 🎤 **实时语音交互**：低延迟语音识别和合成
- 🌐 **多语言支持**：MeloTTS 支持中文、英文、日语、韩语等多种语言

**详细文档：**
- [ARM Docker 部署指南](./LUMI_DEMO-v3/lumi_demo-owl-proj/lumi_nanoowl/ARM_Docker部署指南.md) - ARM 架构 Docker 部署完整指南
- [语音控制药品抓取应用使用说明](./LUMI_DEMO-v3/lumi_demo-owl-proj/lumi_nanoowl/语音控制药品抓取应用使用说明.md) - 完整功能说明和使用指南
- [项目使用说明](./LUMI_DEMO-v3/lumi_demo-owl-proj/lumi_nanoowl/项目使用说明.md) - 项目使用说明
- [README.md](./LUMI_DEMO-v3/lumi_demo-owl-proj/lumi_nanoowl/README.md) - NanoOWL 原始文档

---

## 快速选择

| 特性 | LUMI_DEMO-v1 | LUMI_DEMO-v2 | LUMI_DEMO-v3 |
|------|-------------|-------------|-------------|
| **工作模式** | 原地固定位置 | 多站点移动 | 语音交互+多站点 |
| **AGV支持** | ❌ | ✅ | ✅ |
| **外部轴** | ❌ | ✅ | ✅ |
| **语音交互** | ❌ | ❌ | ✅ |
| **TTS 方案** | - | - | 讯飞 TTS / MeloTTS |
| **目标检测** | 阿里云大模型 | 阿里云大模型 | NanoOWL (零样本) |
| **部署方式** | 本地安装 | 本地安装 | Docker (ARM) |
| **硬件平台** | x86_64 | x86_64 | ARM64 (Jetson) |
| **任务调度** | 单一任务循环 | 多站点智能调度 | 语音驱动+智能调度 |
| **适用场景** | 固定工位分拣 | 移动式多站点分拣 | 语音交互智能分拣 |

## 环境要求

### 通用要求
- Python 3.10+（v1, v2）
- Python 3.8+（v3）
- JAKA 机器人 SDK
- Orbbec 3D相机 SDK

### 平台特定要求
- **LUMI_DEMO-v1/v2**: x86_64 架构，需要阿里云 DashScope API
- **LUMI_DEMO-v3**: 
  - ARM64 架构（NVIDIA Jetson Orin）
  - Docker 环境
  - NVIDIA GPU 支持
  - TTS 方案选择：
    - **讯飞 TTS**：需要 API 密钥
    - **MeloTTS**：无需 API，本地运行，支持 GPU/CPU

详细环境配置请参考各目录下的文档。
