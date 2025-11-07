# AutoCalibProccess.py 快速使用指南

## 快速开始

### 1. 配置参数
编辑 `conf/userCmdControl.json`：
```json
{
  "calibrateParams": {
    "projectName": "my_calibration",    // 项目名称
    "robotIP": "192.168.10.90",         // 机器人IP
    "boardRowNums": 8,                  // 标定板内角点行数
    "boardCowNums": 11,                 // 标定板内角点列数
    "boardLength": 10                   // 标定板方格边长(mm)
  }
}
```

### 2. 运行程序
```bash
python AutoCalibProccess.py
```

### 3. 操作流程
1. **准备标定板** - 放置在相机视野内
2. **移动机器人** - 到不同位置和姿态
3. **按 k 键** - 采集数据（重复15-30次）
4. **按 p 键** - 开始标定
5. **按 q 键** - 退出程序

## 按键说明

| 按键 | 功能 |
|------|------|
| **k** | 采集当前位姿和图像 |
| **p** | 执行标定计算 |
| **q** | 退出程序 |

## 输出文件

所有文件保存在：`calibrate_projects/{project_name}/`

- `images/` - 标定图像
- `conf/{project_name}_CalibParams.json` - 标定结果
- `{project_name}_robotTcpPos.txt` - 机器人位姿

## 常见问题

**Q: 总是提示"舍弃本次采集"？**  
A: 检查标定板参数（boardRowNums, boardCowNums）是否正确

**Q: 无法连接机器人？**  
A: 检查 robotIP 配置和网络连接

**Q: 标定精度不高？**  
A: 增加采集数据量（30组以上），确保位姿分布均匀

详细说明请参考：`AutoCalibProccess_使用说明.md`

