# visualDetect_ali.py 快速使用指南

## 快速开始

### 1. 环境配置

```bash
# 设置阿里云API密钥
export DASHSCOPE_API_KEY="your_api_key_here"

# 设置JAKA SDK库路径
export LD_LIBRARY_PATH=/path/to/JAKA_SDK_LINUX:$LD_LIBRARY_PATH
```

### 2. 配置参数

编辑 `conf/userCmdControl.json`：

```json
{
  "objects": {
    "moveObjects": "bottle",      // 待抓取物体（英文）
    "putObject": "box"            // 放置位置（英文）
  },
  "robotParams": {
    "basePose": [1.78, -0.53, ...],  // 机器人初始姿态
    "relativeUpMotionHeight": 100,    // 抬起高度(mm)
    "RelativeOffset-X": 50,          // X偏移(mm)
    "RelativeOffset-Y": 30,           // Y偏移(mm)
    "RelativeOffset-Z": 50           // Z偏移(mm)
  },
  "calibrateParams": {
    "robotIP": "192.168.10.90"        // 机器人IP
  }
}
```

### 3. 运行程序

```bash
python visualDetect_ali.py
```

## 工作流程

```
启动 → 连接机器人 → 移动到初始位置 → 
循环检测 → 获取图像 → 调用API检测 → 
计算坐标 → 抓取 → 放置 → 返回初始位置
```

## 关键配置项

| 配置项 | 说明 | 示例 |
|--------|------|------|
| `moveObjects` | 待抓取物体名称 | `"bottle"` |
| `putObject` | 放置位置名称 | `"box"` |
| `basePose` | 机器人初始姿态 | `[1.78, -0.53, ...]` |
| `RelativeOffset-X/Y/Z` | 位置偏移 | `50, 30, 50` (mm) |

## 常见问题

**Q: 检测不到物体？**  
A: 检查API密钥、物体名称配置、图像质量

**Q: 深度值为0？**  
A: 程序会自动搜索周围点，检查光照和物体材质

**Q: 机器人运动失败？**  
A: 检查工作空间、机器人状态、位置偏移参数

**Q: 抓取位置不准？**  
A: 重新标定、调整位置偏移参数

## 安全提示

⚠️ **运行前确保：**
- 工作空间内无人员
- 机器人急停可用
- 首次运行降低速度

详细说明请参考：`visualDetect_ali_使用说明.md`

