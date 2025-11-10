'''
语音识别
'''
from whisper_main.whisper import load_model
from whisper_main import whisper
import os
import pyaudio
import wave
import time
from audio_tool.audio_tools import get_input_device
import argparse

# 加载Whisper模型
model_path = "/opt/nanoowl/whisper_main/whisper_models/base.pt"
model = whisper.load_model(model_path, download_root=model_path)

# 音频参数设置
FORMAT = pyaudio.paInt16  # 采样格式：16位整型
CHANNELS = 1              # 单声道
RATE = 16000              # 采样率 16kHz
CHUNK = 1024              # 每次读取的帧数
RECORD_SECONDS = 5        # 默认录音时长（秒）

def record_and_recognize_loop(record_seconds, interval, input_name=None):
    """
    循环录音并进行语音识别。
    :param record_seconds: 每次录音时长（秒）
    :param interval: 每次识别间隔（秒）
    :param input_name: 输入设备名称（部分匹配）
    """
    while True:
        audio = pyaudio.PyAudio()
        # 获取输入设备ID（根据名称部分匹配，找不到则用默认设备）
        input_device_id = get_input_device(input_name)
        print(f"Using input device index: {input_device_id}")
        # 打开音频流，准备录音
        stream = audio.open(format=FORMAT,
                           channels=CHANNELS,
                           rate=RATE,
                           input=True,
                           input_device_index=input_device_id,
                           frames_per_buffer=CHUNK)
        print(f"Recording for {record_seconds} seconds...")
        frames = []
        # 按帧采集音频数据
        for _ in range(0, int(RATE / CHUNK * record_seconds)):
            data = stream.read(CHUNK)
            frames.append(data)
        print("Recording finished.")
        # 关闭音频流
        stream.stop_stream()
        stream.close()
        audio.terminate()
        # 保存为临时wav文件
        temp_audio_path = "temp_audio1.wav"
        with wave.open(temp_audio_path, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(pyaudio.PyAudio().get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))
        print(f"Saved to {temp_audio_path}, recognizing...")
        # 调用Whisper模型进行语音识别
        result = model.transcribe(temp_audio_path)
        print("STT result:", result["text"])
        # 删除临时文件
        os.remove(temp_audio_path)
        print(f"Waiting {interval} seconds before next recording...")
        time.sleep(interval)

if __name__ == "__main__":
    '''
    用法示例：
    python3 stt_whisper.py --input_device_name "AIUI-USB-MC" --record_seconds 5 --interval 1
    '''
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="Real-time speech recognition using Whisper and audio_tools input device.")
    parser.add_argument('--interval', type=float, default=1.0, help='Interval (seconds) between recognitions')
    parser.add_argument('--record_seconds', type=float, default=5.0, help='Recording duration (seconds)')
    parser.add_argument('--input_device_name', type=str, default="AIUI-USB-MC", help='Input device name (partial match)')
    args = parser.parse_args()
    # 启动循环录音识别
    record_and_recognize_loop(args.record_seconds, args.interval, args.input_device_name)