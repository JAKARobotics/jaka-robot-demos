# """
# 原始夹爪控制代码 - 已封装到JAKAIntegrated类中
# 该文件中的夹爪控制功能已经被封装到 jaka_utilfs/jaka_integrated.py 中的以下方法：
# - gripper_init(): 初始化夹爪
# - gripper_open(): 打开夹爪
# - gripper_close(): 关闭夹爪
# - grab_action(): 兼容原有接口的夹爪动作方法

# 使用方法：
# robot = JAKAIntegrated("192.168.10.90")
# robot.gripper_init()  # 初始化夹爪
# robot.gripper_open()  # 打开夹爪
# robot.gripper_close() # 关闭夹爪
# """

# import time
# from JAKA_SDK_ARM import jkrc

# # === 原始夹爪控制代码（已注释，功能已封装到JAKAIntegrated类中） ===

# # 机器人连接
# robot = jkrc.RC("192.168.10.90")  # 替换为你的机器人IP
# robot.login()
# robot.power_on()
# robot.disable_robot()  # 设置TIO前必须下使能


# chnid = 2
# chnmode = 0
# mod_rtu_comm = {
#     'chn_id':1,
#     'slave_id':1,
#     'baudrate': 115200,
#     'databit': 8,
#     'stopbit': 1,
#     'parity': 79
# }
# # set params
# robot.set_tio_vout_param(1,0)  # ebable tio； 24V
# robot.set_tio_pin_mode(2,1)    # rs485l; Ai
# time.sleep(1)
# robot.set_rs485_chn_mode(1,0)
# r = robot.set_rs485_chn_comm({
#     'chn_id':1,
#     'slave_id':1,
#     'baudrate': 115200,
#     'databit': 8,
#     'stopbit': 1,
#     'parity': 79
# })

# robot.enable_robot()

# # send command
# # 初始化夹爪
# command = bytearray.fromhex("01 06 01 00 00 01")  # must be bytearray object
# print(command)
# ret = robot.send_tio_rs_command(1, command)
# print("==", ret)
# time.sleep(2)

# # # close gripper
# command2 = bytearray.fromhex("01 06 01 03 00 00")
# ret1 = robot.send_tio_rs_command(1, command2)
# print('close:',ret1)
# time.sleep(2)
# # ret2 = demo.get_rs485_chn_comm()
# # print(ret2)

# # # open gripper
# command2 = bytearray.fromhex("01 06 01 03 01 F4")
# ret1 = robot.send_tio_rs_command(1, command2)
# print('open:',ret1)
# time.sleep(2)
# # ret2 = demo.get_rs485_chn_comm()
# # print(ret2)





# # 配置TIO接口为RS485 Modbus RTU模式
# robot.set_tio_vout_param(1, 0)      # 开启TIO电源，24V输出
# robot.set_tio_pin_mode(2, 1)        # 设置AI2为RS485L模式
# robot.set_rs485_chn_mode(1, 0)      # 通道1为Modbus RTU
# # 设置通讯参数：通道1，从站ID=1，波特率115200，8N1
# robot.set_rs485_chn_comm({
#     'chn_id': 1,
#     'slave_id': 1,
#     'baudrate': 115200,
#     'databit': 8,
#     'stopbit': 1,
#     'parity': 78  # 78 = 无校验
# })

# robot.enable_robot()  # 重新上使能
# time.sleep(1)










# # # 构造Modbus RTU指令（根据PDF指令格式）
# # def send_modbus_command(command_hex_str):
# #     command = bytearray.fromhex(command_hex_str)
# #     ret = robot.send_tio_rs_command(0x1, command)  # 通道1
# #     print(f"发送指令: {command_hex_str} -> 返回: {ret}")
# #     time.sleep(1.5)  # 等待夹爪响应

# # try:
# #     # 1. 初始化夹爪（回零位）
# #     send_modbus_command("01 06 01 00 00 01 49")  # 初始化指令（0x0100写入0x0001）

# #     # 2. 设置夹持力为30%
# #     send_modbus_command("01 06 01 01 00 1E 59")

# #     # 3. 移动到500位置
# #     send_modbus_command("01 06 01 03 01 F4 78 21")

# #     # 4. 可选：读取夹爪状态（0x0201读取夹持状态）
# #     read_status = "01 03 02 02 00 01 24 72"
# #     command = bytearray.fromhex(read_status)
# #     ret = robot.send_tio_rs_command(1, command)
# #     print(f"状态查询返回: {ret}")

# # except Exception as e:
# #     print(f"执行失败: {e}")

# # finally:
# #     robot.logout()