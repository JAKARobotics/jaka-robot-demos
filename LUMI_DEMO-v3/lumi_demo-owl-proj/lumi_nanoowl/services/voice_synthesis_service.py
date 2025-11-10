#!/usr/bin/env python3
"""
语音合成服务
基于讯飞TTS实现语音合成功能
"""

import os
import time
import threading
from typing import Optional
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audio_tool.tts_xf import synthesize_to_wav
from audio_tool.audio_tools import get_output_device, play_wav

class VoiceSynthesisService:
    """语音合成服务"""
    
    def __init__(self, config: dict):
        """
        初始化语音合成服务
        :param config: 配置字典，包含appid, apikey, apisecret, output_device_name, volume等
        """
        self.config = config
        self.is_running = False
        self.speech_queue = []
        self.speech_lock = threading.Lock()
        
        # 讯飞TTS配置
        self.appid = config.get("appid", "1be4dc2a")
        self.apikey = config.get("apikey", "e4e0a90722f7c18e8e40e9a414f7a100")
        self.apisecret = config.get("apisecret", "YTI3YjllMTYwZjczMDJlZTUwZjI3NjI5")
        
        # 输出设备名称和ID
        self.output_device_name = config.get("output_device_name", None)
        self.output_device_id = get_output_device(self.output_device_name)
        print(f"Using output device index: {self.output_device_id}")
        
        # 音量设置 (0.0-1.0)
        self.volume = config.get("volume", 1.0)
        print(f"TTS volume set to: {self.volume}")
        
        # 音频文件路径
        self.audio_dir = "./temp_audio"
        os.makedirs(self.audio_dir, exist_ok=True)
        
        # 播放线程
        self.play_thread = None
    
    def start(self):
        """启动语音合成服务"""
        if self.is_running:
            return
        
        self.is_running = True
        self.play_thread = threading.Thread(target=self._play_loop, daemon=True)
        self.play_thread.start()
        print("语音合成服务已启动")
    
    def stop(self):
        """停止语音合成服务"""
        self.is_running = False
        if self.play_thread:
            self.play_thread.join(timeout=2)
        print("语音合成服务已停止")
    
    def speak(self, text: str, block: bool = False):
        """
        语音合成并播放
        :param text: 要合成的文本
        :param block: 是否阻塞等待播放完成
        """
        if not self.is_running:
            print("语音合成服务未启动")
            return
        
        if block:
            # 阻塞模式：直接合成并播放
            self._synthesize_and_play(text)
        else:
            # 非阻塞模式：加入队列
            with self.speech_lock:
                self.speech_queue.append(text)
    
    def _synthesize_and_play(self, text: str):
        """合成并播放语音（采样率强制为44100Hz，指定输出设备）"""
        try:
            # 生成临时文件路径
            timestamp = int(time.time() * 1000)
            wav_path = os.path.join(self.audio_dir, f"speech_{timestamp}.wav")
            
            # 调用讯飞TTS合成
            synthesize_to_wav(text, wav_path, self.appid, self.apikey, self.apisecret)
            
            # 检查采样率并重采样到44100Hz（如果需要）
            import soundfile as sf
            from scipy.signal import resample
            info = sf.info(wav_path)
            if info.samplerate != 44100:
                print(f"检测到采样率为{info.samplerate}，自动重采样到44100Hz")
                y, sr = sf.read(wav_path)
                n_samples = int(len(y) * 44100 / info.samplerate)
                y_resampled = resample(y, n_samples)
                sf.write(wav_path, y_resampled, 44100)
                print("重采样完成")
            
            # 用audio_tools的play_wav播放到指定输出设备
            play_wav(wav_path, device_id=self.output_device_id, volume=self.volume)
            
            # 清理临时文件
            try:
                os.remove(wav_path)
            except:
                pass
                
        except Exception as e:
            print(f"语音合成失败: {e}")
    
    def _play_loop(self):
        """播放循环线程"""
        while self.is_running:
            try:
                # 检查队列中是否有待播放的文本
                text_to_speak = None
                with self.speech_lock:
                    if self.speech_queue:
                        text_to_speak = self.speech_queue.pop(0)
                
                if text_to_speak:
                    self._synthesize_and_play(text_to_speak)
                else:
                    time.sleep(0.1)  # 短暂休眠
                    
            except Exception as e:
                print(f"播放循环出错: {e}")
                time.sleep(1)
    
    def clear_queue(self):
        """清空播放队列"""
        with self.speech_lock:
            self.speech_queue.clear()

# 使用示例
def example_usage():
    config = {
        "appid": "1be4dc2a",
        "apikey": "e4e0a90722f7c18e8e40e9a414f7a100",
        "apisecret": "YTI3YjllMTYwZjczMDJlZTUwZjI3NjI5",
        "output_device_name": "USB Audio Device"  # 替换为你的输出设备名
    }
    service = VoiceSynthesisService(config)
    service.start()
    try:
        # 合成并播放一段文字（阻塞模式）
        service.speak("你好啊，语音合成测试", block=True)
        # 合成并播放多段文字（非阻塞队列模式）
        service.speak("这是第二句话，测试队列播放。", block=True)
        service.speak("第三句话，依次播放。", block=True)
        # 等待队列播放完成
        time.sleep(5)
    finally:
        service.stop()

if __name__ == "__main__":
    example_usage() 