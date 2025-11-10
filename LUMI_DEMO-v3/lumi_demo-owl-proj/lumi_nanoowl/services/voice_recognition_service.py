#!/usr/bin/env python3
"""
语音识别服务
基于Whisper实现语音唤醒和命令识别功能
"""

import os
import time
import threading
import wave
import pyaudio
from whisper_main.whisper import load_model
from whisper_main import whisper
from typing import Optional
from audio_tool.audio_tools import get_input_device
from datetime import datetime

class VoiceRecognitionService:
    """基于Whisper的语音识别服务"""
    def __init__(self, config: dict):
        self.config = config
        self.wakeup_word = config.get("wakeup_word", "你好")
        self.record_seconds = config.get("record_seconds", 3)
        self.interval = config.get("interval", 3)
        self.input_device_name = config.get("input_device_name", None)
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
        self.CHUNK = 1024
        print("正在初始化PyAudio...")
        self.audio = pyaudio.PyAudio()
        print("PyAudio初始化成功")
        
        print(f"正在查找音频设备: {self.input_device_name}")
        self.input_device_id = get_input_device(self.input_device_name)
        print(f"使用音频设备索引: {self.input_device_id}")
        
        # 检测可用的音频设备
        print("检测可用的音频输入设备:")
        for i in range(self.audio.get_device_count()):
            try:
                device_info = self.audio.get_device_info_by_index(i)
                if device_info['maxInputChannels'] > 0:
                    print(f"  设备 {i}: {device_info['name']} (输入通道: {device_info['maxInputChannels']})")
            except Exception as e:
                print(f"  设备 {i}: 无法获取信息 ({e})")
        self.model_path = config.get("model_path", "/opt/nanoowl/whisper_main/whisper_models/base.pt")
        print(f"正在加载Whisper模型: {self.model_path}")
        try:
            self.model = whisper.load_model(self.model_path, download_root=self.model_path)
            print("Whisper模型加载成功")
        except Exception as e:
            print(f"Whisper模型加载失败: {e}")
            print("尝试使用默认模型...")
            try:
                self.model = whisper.load_model("base")
                print("默认模型加载成功")
            except Exception as e2:
                print(f"默认模型也加载失败: {e2}")
                raise e2
        
        # 语言限制设置
        self.language = config.get("language", "zh")  # zh: 中文, en: 英文, auto: 自动检测
        self.allowed_languages = config.get("allowed_languages", ["zh", "en"])  # 允许的语言列表
        print(f"Language setting: {self.language}, Allowed languages: {self.allowed_languages}")
        
        # 语音文件保存设置
        self.save_audio_files = config.get("save_audio_files", False)  # 是否保存语音文件
        self.audio_save_dir = config.get("audio_save_dir", "./debug_audio")  # 语音文件保存目录
        self.audio_counter = 0  # 语音文件计数器
        
        # 创建保存目录
        if self.save_audio_files:
            os.makedirs(self.audio_save_dir, exist_ok=True)
            print(f"语音文件将保存到: {self.audio_save_dir}")
        
        self._wakeup_thread = None
        self._wakeup_event = threading.Event()
        self._wakeup_result = False
        self._running = False

    def _get_audio_filename(self, prefix="audio"):
        """生成带时间戳的音频文件名"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.audio_counter += 1
        return f"{prefix}_{timestamp}_{self.audio_counter:03d}.wav"

    def _record_once(self, record_seconds=None, save_file=True):
        record_seconds = record_seconds or self.record_seconds
        
        try:
            print(f"正在打开音频流...")
            stream = self.audio.open(format=self.FORMAT,
                                    channels=self.CHANNELS,
                                    rate=self.RATE,
                                    input=True,
                                    input_device_index=self.input_device_id,
                                    frames_per_buffer=self.CHUNK)
            print(f"音频流打开成功，开始录音 {record_seconds} 秒...")
            
            frames = []
            total_chunks = int(self.RATE / self.CHUNK * record_seconds)
            
            for i in range(total_chunks):
                try:
                    data = stream.read(self.CHUNK, exception_on_overflow=False)
                    frames.append(data)
                    if i % 10 == 0:  # 每10个chunk打印一次进度
                        progress = (i / total_chunks) * 100
                        print(f"录音进度: {progress:.1f}%")
                except Exception as e:
                    print(f"录音过程中出错: {e}")
                    break
            
            print("录音完成，正在关闭音频流...")
            stream.stop_stream()
            stream.close()
            print("音频流已关闭")
            
        except Exception as e:
            print(f"录音初始化失败: {e}")
            # 尝试使用默认设备
            try:
                print("尝试使用默认音频设备...")
                stream = self.audio.open(format=self.FORMAT,
                                        channels=self.CHANNELS,
                                        rate=self.RATE,
                                        input=True,
                                        frames_per_buffer=self.CHUNK)
                print("使用默认设备录音成功")
                
                frames = []
                total_chunks = int(self.RATE / self.CHUNK * record_seconds)
                
                for i in range(total_chunks):
                    data = stream.read(self.CHUNK, exception_on_overflow=False)
                    frames.append(data)
                
                stream.stop_stream()
                stream.close()
                
            except Exception as e2:
                print(f"默认设备也失败: {e2}")
                raise e2
        
        # 生成音频文件名
        if save_file and self.save_audio_files:
            audio_filename = self._get_audio_filename("record")
            temp_audio_path = os.path.join(self.audio_save_dir, audio_filename)
        else:
            temp_audio_path = "temp_audio1.wav"
        
        # 保存音频文件
        with wave.open(temp_audio_path, 'wb') as wf:
            wf.setnchannels(self.CHANNELS)
            wf.setsampwidth(self.audio.get_sample_size(self.FORMAT))
            wf.setframerate(self.RATE)
            wf.writeframes(b''.join(frames))
        
        if save_file and self.save_audio_files:
            print(f"语音文件已保存: {temp_audio_path}")
        
        return temp_audio_path

    def _recognize_once(self, record_seconds=None, save_file=True):
        temp_audio_path = self._record_once(record_seconds, save_file)
        print(f"Saved to {temp_audio_path}, recognizing...")
        
        # 根据语言设置进行识别
        if self.language == "auto":
            # 自动检测语言
            result = self.model.transcribe(temp_audio_path)
        else:
            # 指定语言识别
            result = self.model.transcribe(temp_audio_path, language=self.language)
        
        # 检查识别结果的语言是否在允许列表中
        detected_text = result["text"]
        detected_language = result.get("language", "unknown")
        
        print(f"STT result: {detected_text}, detected language: {detected_language}")
        
        # 如果检测到语言不在允许列表中，返回空字符串
        if detected_language not in self.allowed_languages and detected_language != "unknown":
            print(f"Language {detected_language} not in allowed languages: {self.allowed_languages}")
            if not save_file or not self.save_audio_files:
                os.remove(temp_audio_path)
            return ""
        
        # 只有在不保存文件时才删除临时文件
        if not save_file or not self.save_audio_files:
            os.remove(temp_audio_path)
        
        return detected_text

    def _wakeup_loop(self):
        print(f"[Wakeup] 开始循环检测唤醒词: '{self.wakeup_word}'，每{self.interval}s检测一次")
        while not self._wakeup_event.is_set():
            text = self._recognize_once(self.record_seconds, save_file=True)
            if self.wakeup_word.lower() in text.lower():
                print(f"[Wakeup] 检测到唤醒词: {self.wakeup_word}")
                self._wakeup_result = True
                break
            print(f"[Wakeup] 未检测到唤醒词，等待{self.interval}s后重试...")
            time.sleep(self.interval)
        print("[Wakeup] 唤醒检测线程退出")

    def start_wakeup(self):
        """启动唤醒词检测线程"""
        if self._wakeup_thread and self._wakeup_thread.is_alive():
            print("[Wakeup] 唤醒检测已在运行")
            return
        self._wakeup_event.clear()
        self._wakeup_result = False
        self._wakeup_thread = threading.Thread(target=self._wakeup_loop, daemon=True)
        self._wakeup_thread.start()

    def wait_for_wakeup(self, timeout=None):
        """阻塞等待唤醒词检测结果"""
        self._wakeup_thread.join(timeout)
        return self._wakeup_result

    def stop_wakeup(self):
        """停止唤醒词检测线程"""
        self._wakeup_event.set()
        if self._wakeup_thread:
            self._wakeup_thread.join()

    def recognize_command(self, record_seconds=None):
        """在需要时进行一次语音识别，返回识别文本"""
        return self._recognize_once(record_seconds, save_file=True)

    def close(self):
        self.audio.terminate()

# 测试用例
if __name__ == "__main__":
    print("=== 语音识别测试 ===")
    print("此测试将保存所有录音文件到 ./debug_audio 目录")
    print("用于调试语音识别问题")
    print()
    
    print("正在初始化语音识别服务...")
    
    config = {
        "wakeup_word": "你好",
        "record_seconds": 3,
        "interval": 2,
        "input_device_name": "AIUI-USB-MC",
        "model_path": "/opt/nanoowl/whisper_main/whisper_models/base.pt",
        "language": "zh",
        "allowed_languages": ["zh", "en"],
        "save_audio_files": True,
        "audio_save_dir": "./debug_audio"
    }
    
    try:
        service = VoiceRecognitionService(config)
        print("语音识别服务初始化完成")
    except Exception as e:
        print(f"语音识别服务初始化失败: {e}")
        print("程序退出")
        exit(1)
    
    try:
        print("开始语音识别测试...")
        print("请说一些话进行测试，每次录音3秒")
        print("按 Ctrl+C 退出测试")
        print()
        
        test_count = 0
        while True:
            test_count += 1
            print(f"=== 第 {test_count} 次测试 ===")
            print("请说话...")
            
            # 直接进行语音识别，不等待唤醒词
            result = service.recognize_command(record_seconds=3)
            
            print(f"识别结果: '{result}'")
            if result.strip():
                print("✓ 识别成功")
            else:
                print("✗ 识别失败或为空")
            
            print()
            
            # 询问是否继续
            try:
                choice = input("按回车继续测试，输入 'q' 退出: ").strip()
                if choice.lower() == 'q':
                    break
            except KeyboardInterrupt:
                print("\n测试被中断")
                break
                
    except KeyboardInterrupt:
        print("\n测试被中断")
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
    finally:
        print("测试结束，音频文件已保存到 ./debug_audio 目录")
        service.close() 