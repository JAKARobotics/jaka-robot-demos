import pyaudio  # 用于音频输入和输出，支持麦克风录音和扬声器播放
import logging
from datetime import datetime
import os
import wave
import numpy as np
import threading
import subprocess
import glob
import random
import time
import hashlib

def setup_logger():
    # 获取当前时间并格式化为字符串
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_dir = os.path.dirname(os.path.abspath(__file__))  # audio_tool 目录
    log_filename = os.path.join(log_dir, f"voice_interaction_{current_time}.log")

    # 日志轮转：只保留最新的10个日志文件
    log_files = [f for f in os.listdir(log_dir) if f.startswith("voice_interaction_") and f.endswith(".log")]
    if len(log_files) >= 10:
        # 按文件创建时间排序，删除最旧的
        log_files_full = [os.path.join(log_dir, f) for f in log_files]
        log_files_full.sort(key=lambda x: os.path.getctime(x))
        for old_log in log_files_full[:len(log_files_full)-9]:
            try:
                os.remove(old_log)
            except Exception as e:
                print(f"Failed to remove old log file {old_log}: {e}")

    # 创建一个日志记录器
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)  # 设置日志级别为 INFO

    # 创建一个文件处理器，用于将日志写入文件
    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)

    # 创建一个流处理器，用于将日志输出到终端
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    stream_handler.setFormatter(stream_formatter)

    # 避免重复添加 handler
    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)

    return logger



def get_device(output_name=None):
    logger = setup_logger()
    """
    根据指定的输入设备名称和输出设备名称，返回对应的设备 ID。
    如果未找到指定设备，则返回默认设备的 ID。
    :param input_name: 输入设备的名称（麦克风）。
    :param output_name: 输出设备的名称（扬声器）。
    :return: (input_device_id, output_device_id)
    """
    p = pyaudio.PyAudio()

    # 目标设备名称
    # input_name = "AIUI-USB-MC: USB Audio" 
    # input_name =  "XFM-DP-V0.0.18" #"AIUI-USB-MC: USB Audio"  # 替换为实际输入设备名称
    output_name = "USB Audio Device"       # 替换为实际输出设备名称

    

    # 获取默认设备 ID
    # default_input_id = p.get_default_input_device_info()['index']
    default_output_id = p.get_default_output_device_info()['index']

    # 初始化返回值
    # input_device_id = default_input_id
    output_device_id = default_output_id

    # 遍历所有音频设备
    for i in range(p.get_device_count()):
        device_info = p.get_device_info_by_index(i)
        # print("device_info:",device_info)

        device_name = device_info['name']
        print('device--------:',device_name)

        # 排除默认设备（如 pulse 或 default）
        if "pulse" in device_name.lower() or "default" in device_name.lower():
            continue

        # # 检查输入设备名称
        # if input_name and input_name.lower() in device_name.lower():
        #     logger.info(f"找到指定输入设备：{device_name}，ID：{i}")
        #     input_device_id = i

        # 检查输出设备名称
        if output_name and output_name.lower() in str(device_name).lower():
            logger.info(f"找到指定输出设备：{device_name}，ID：{i}")
            output_device_id = i

    # # 如果未找到指定设备，返回默认设备 ID
    # if input_name and input_device_id == default_input_id:
    #     logger.info(f"未找到指定输入设备 '{input_name}'，返回默认输入设备 ID：{default_input_id}")
    if output_name and output_device_id == default_output_id:
        logger.info(f"未找到指定输出设备 '{output_name}'，返回默认输出设备 ID：{default_output_id}")

    # return input_device_id, output_device_id
    return int(output_device_id) if output_device_id is not None else None


def get_output_device(output_name="USB Audio Device"):
    logger = setup_logger()
    p = pyaudio.PyAudio()
    # output_name = "USB Audio Device"       # 替换为实际输出设备名称
    # 获取默认设备 ID
    default_output_id = p.get_default_output_device_info()['index']
    # 初始化返回值
    output_device_id = default_output_id
    # 遍历所有音频设备
    for i in range(p.get_device_count()):
        device_info = p.get_device_info_by_index(i)
        # print("device_info:",device_info)

        device_name = device_info['name']
        # print('device--------:',device_name)
        # 排除默认设备（如 pulse 或 default）
        if "pulse" in device_name.lower() or "default" in device_name.lower():
            continue
        # 检查输出设备名称
        if output_name and output_name.lower() in str(device_name).lower():
            logger.info(f"找到指定输出设备：{device_name}，ID：{i}")
            output_device_id = i
    if output_name and output_device_id == default_output_id:
        logger.info(f"未找到指定输出设备 '{output_name}'，返回默认输出设备 ID：{default_output_id}")

    return int(output_device_id) if output_device_id is not None else None



def get_input_device(input_name = "AIUI-USB-MC"):
    logger = setup_logger()
    p = pyaudio.PyAudio()

    # 目标设备名称
    # input_name = "AIUI-USB-MC: USB Audio" 
    # 获取默认设备 ID
    default_input_id = p.get_default_input_device_info()['index']
    # 初始化返回值
    input_device_id = default_input_id
    # 遍历所有音频设备
    for i in range(p.get_device_count()):
        device_info = p.get_device_info_by_index(i)
        # print("device_info:",device_info)
        device_name = device_info['name']
        # print('device--------:',device_name)
        # 排除默认设备（如 pulse 或 default）
        if "pulse" in device_name.lower() or "default" in device_name.lower():
            continue
        # 检查输入设备名称
        if input_name and input_name.lower() in device_name.lower():
            logger.info(f"找到指定输入设备：{device_name}，ID：{i}")
            input_device_id = i
    # 如果未找到指定设备，返回默认设备 ID
    if input_name and input_device_id == default_input_id:
        logger.info(f"未找到指定输入设备 '{input_name}'，返回默认输入设备 ID：{default_input_id}")

    return int(input_device_id) if input_device_id is not None else None
        
    

def play_wav(wav_path, device_id=None, volume=1.0):
    """
    播放指定路径的wav格式音频文件。
    :param wav_path: wav文件路径
    :param device_id: 输出设备ID（可选），不传则自动获取
    :param volume: 音量缩放系数（0.0~1.0），默认1.0
    """
    logger = setup_logger()
    if device_id is None:
        device_id = get_device()
    try:
        wf = wave.open(wav_path, 'rb')
    except Exception as e:
        logger.error(f"无法打开音频文件: {wav_path}, 错误: {e}")
        return

    p = pyaudio.PyAudio()

    # 获取音频文件信息
    file_channels = wf.getnchannels()
    file_rate = wf.getframerate()
    file_format = p.get_format_from_width(wf.getsampwidth())

    # 获取设备信息并检查兼容性
    try:
        device_info = p.get_device_info_by_index(device_id)
        max_output_channels = device_info['maxOutputChannels']

        # 如果文件通道数超过设备支持的最大通道数，调整为设备支持的通道数
        output_channels = min(file_channels, max_output_channels)
        if output_channels == 0:
            output_channels = 1  # 至少使用1个通道

        logger.info(f"音频文件: {file_channels}通道, {file_rate}Hz")
        logger.info(f"输出设备: 最大{max_output_channels}通道, 使用{output_channels}通道")

    except Exception as e:
        logger.warning(f"无法获取设备信息: {e}, 使用默认配置")
        output_channels = 1  # 默认使用单声道

    try:
        stream = p.open(
            format=file_format,
            channels=output_channels,
            rate=file_rate,
            output=True,
            output_device_index=device_id
        )
    except Exception as e:
        logger.error(f"无法打开音频输出流: {e}")
        # 尝试使用更保守的设置
        try:
            logger.info("尝试使用保守设置: 单声道, 44100Hz, 16bit")
            stream = p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=44100,
                output=True,
                output_device_index=device_id
            )
            output_channels = 1
            file_rate = 44100
        except Exception as e2:
            logger.error(f"保守设置也失败: {e2}")
            wf.close()
            p.terminate()
            return

    chunk = 8192
    data = wf.readframes(chunk)
    sample_width = wf.getsampwidth()
    dtype = None
    if sample_width == 2:
        dtype = np.int16
    elif sample_width == 1:
        dtype = np.uint8
    elif sample_width == 4:
        dtype = np.int32
    else:
        logger.error(f"暂不支持的采样宽度: {sample_width}")
        stream.stop_stream()
        stream.close()
        wf.close()
        p.terminate()
        return

    while data:
        audio_array = np.frombuffer(data, dtype=dtype)

        # 处理通道数不匹配的情况
        if file_channels != output_channels:
            # 重新整形为多通道数据
            if file_channels > 1:
                audio_array = audio_array.reshape(-1, file_channels)
                if output_channels == 1:
                    # 多声道转单声道：取平均值
                    audio_array = np.mean(audio_array, axis=1).astype(dtype)
                elif output_channels < file_channels:
                    # 减少通道数：只取前N个通道
                    audio_array = audio_array[:, :output_channels].flatten()
            else:
                # 单声道转多声道：复制数据
                if output_channels > 1:
                    audio_array = np.repeat(audio_array.reshape(-1, 1), output_channels, axis=1).flatten()

        # 音量缩放
        if dtype == np.uint8:
            # 8bit PCM 以128为中心
            audio_array = ((audio_array.astype(np.int16) - 128) * volume + 128).clip(0, 255).astype(np.uint8)
        else:
            max_val = np.iinfo(dtype).max
            min_val = np.iinfo(dtype).min
            audio_array = (audio_array.astype(np.float32) * volume).clip(min_val, max_val).astype(dtype)

        stream.write(audio_array.tobytes())
        data = wf.readframes(chunk)

    stream.stop_stream()
    stream.close()
    wf.close()
    p.terminate()
    logger.info(f"播放完成: {wav_path}")



def play_random_wav_from_folder(folder_path, volume=1.0):
    import glob
    import random
    import os
    wav_files = glob.glob(os.path.join(folder_path, "*.wav"))
    if not wav_files:
        print("没有找到可用的音频文件")
        return
    wav_path = random.choice(wav_files)
    print(f"播放音频: {wav_path}")
    play_wav_aplay(wav_path, volume=volume)


def play_wav_aplay(wav_path, volume=1.0):
    """
    用aplay异步播放wav文件，volume为0.0~1.0，若系统支持amixer则先设置音量。
    """
    import subprocess
    import shutil
    # 若系统支持amixer，可设置主音量（假设卡号0，通道Master）
    if shutil.which('amixer'):
        vol_percent = int(volume * 100)
        subprocess.call(['amixer', 'set', 'Master', f'{vol_percent}%'])
    # aplay异步播放
    subprocess.Popen(['aplay', wav_path])


def play_random_wav_sequential(folder_path, volume=1.0, device_id=None):
    wav_files = glob.glob(f"{folder_path}/*.wav")
    if not wav_files:
        print("没有找到可用的音频文件")
        return
    while True:
        wav_path = random.choice(wav_files)
        print(f"播放音频: {wav_path}")
        play_wav(wav_path, device_id=device_id, volume=volume)
        # 可选：每次播放后休息1秒
        time.sleep(5)


def play_tts(text, volume=1.0, block=False, device_id=None, output_device_name=None):
    """
    使用讯飞TTS合成语音并播放
    :param text: 要合成的文本
    :param volume: 播放音量 (0.0~10.0)，支持更大的音量范围
    :param block: 是否阻塞等待播放完成
    :param device_id: 音频设备ID，None则自动获取
    :param output_device_name: 输出设备名称，用于指定特定的音频设备
    """
    logger = setup_logger()

    try:
        # 导入TTS模块
        try:
            from .tts_xf import synthesize_to_wav
        except ImportError:
            from tts_xf import synthesize_to_wav

        # 讯飞TTS配置
        appid = '1be4dc2a'
        apikey = 'e4e0a90722f7c18e8e40e9a414f7a100'
        apisecret = 'YTI3YjllMTYwZjczMDJlZTUwZjI3NjI5'

        # 生成缓存文件名（基于文本内容的hash）
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        cache_dir = os.path.join(os.path.dirname(__file__), 'tts_cache')
        os.makedirs(cache_dir, exist_ok=True)
        wav_path = os.path.join(cache_dir, f'tts_{text_hash}.wav')

        # 如果缓存文件不存在，则合成
        if not os.path.exists(wav_path):
            logger.info(f"合成TTS语音: {text}")
            synthesize_to_wav(text, wav_path, appid, apikey, apisecret)
            logger.info(f"TTS合成完成: {wav_path}")
        else:
            logger.info(f"使用TTS缓存: {wav_path}")

        # 获取输出设备ID
        if device_id is None:
            if output_device_name:
                device_id = get_output_device(output_device_name)
            else:
                device_id = get_output_device()

        logger.info(f"使用输出设备ID: {device_id}, 音量: {volume}")

        if block:
            # 阻塞播放
            play_wav(wav_path, device_id=device_id, volume=volume)
        else:
            # 非阻塞播放
            def play_async():
                play_wav(wav_path, device_id=device_id, volume=volume)

            thread = threading.Thread(target=play_async, daemon=True)
            thread.start()

        logger.info(f"TTS播放完成: {text}")

    except ImportError as e:
        logger.error(f"TTS模块导入失败: {e}")
        print(f"TTS功能不可用: {e}")
        # 回退到系统TTS或简单的文本输出
        print(f"[TTS回退] {text}")
    except Exception as e:
        logger.error(f"TTS播放失败: {e}")
        print(f"TTS播放出错: {e}")
        # 回退到文本输出
        print(f"[TTS错误] {text}")


def play_tts_simple(text, volume=2.0):
    """
    简化版TTS播放函数，兼容旧代码
    :param text: 要合成的文本
    :param volume: 播放音量
    """
    play_tts(text, volume=volume, block=True)


def play_tts_async(text, volume=1.0, device_id=None):
    """
    异步TTS播放函数
    :param text: 要合成的文本
    :param volume: 播放音量
    :param device_id: 音频设备ID
    """
    play_tts(text, volume=volume, block=False, device_id=device_id)


def play_tts_with_device(text, volume=1.0, output_device_name="USB Audio Device", block=True):
    """
    指定设备的TTS播放函数
    :param text: 要合成的文本
    :param volume: 播放音量
    :param output_device_name: 输出设备名称
    :param block: 是否阻塞等待播放完成
    """
    play_tts(text, volume=volume, block=block, output_device_name=output_device_name)


def test_tts():
    """
    测试TTS功能
    """
    print("测试TTS功能...")
    test_text = "你好，这是TTS语音合成测试。"

    try:
        # 测试基本TTS
        print("1. 测试基本TTS播放...")
        play_tts(test_text, volume=1.0, block=True)

        # 测试指定设备TTS
        print("2. 测试指定设备TTS播放...")
        play_tts_with_device(test_text, volume=2.0, output_device_name="USB Audio Device")

        # 测试异步TTS
        print("3. 测试异步TTS播放...")
        play_tts_async(test_text, volume=1.5)
        time.sleep(3)  # 等待异步播放完成

        print("TTS测试完成！")

    except Exception as e:
        print(f"TTS测试失败: {e}")


def get_available_audio_devices():
    """
    获取可用的音频设备列表
    :return: 设备信息列表
    """
    try:
        import pyaudio
        p = pyaudio.PyAudio()
        devices = []

        for i in range(p.get_device_count()):
            try:
                device_info = p.get_device_info_by_index(i)
                devices.append({
                    'index': i,
                    'name': device_info['name'],
                    'max_input_channels': device_info['maxInputChannels'],
                    'max_output_channels': device_info['maxOutputChannels'],
                    'default_sample_rate': device_info['defaultSampleRate']
                })
            except Exception as e:
                print(f"获取设备 {i} 信息失败: {e}")

        p.terminate()
        return devices

    except ImportError:
        print("PyAudio未安装，无法获取设备列表")
        return []
    except Exception as e:
        print(f"获取音频设备列表失败: {e}")
        return []

# 用法示例
if __name__ == '__main__':
    # input_device_id, output_device_id = get_device_old()
    output_device_id = get_device()
    # 示例：随机播放一个wav文件
    # play_random_wav_from_folder('/home/jaka/AI_CODES/lumi_demo/audio_tool/audio_file-nodoll', volume=1.0)


    play_random_wav_sequential('/opt/nanoowl/audio_tool/test_demo', volume=8)  # 改参数5 就可以变大声   你可以在场地改不同数值测试


 


    # wav_path = "/home/jaka/AI_CODES/lumi_demo/audio_tool/audio_file-nodoll/lumi_doll-1.wav"
    # play_wav(wav_path, output_device_id, volume=0.5)  # 50%音量
    # play_wav(wav_path, output_device_id, volume=1.0)  # 原始音量
    # play_wav(wav_path, output_devicei_id, volume=0.2)  # 20%音量

