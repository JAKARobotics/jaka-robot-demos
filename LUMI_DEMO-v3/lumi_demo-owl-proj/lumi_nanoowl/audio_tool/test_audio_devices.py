import pyaudio

def list_audio_devices():
    p = pyaudio.PyAudio()
    print("=== 音频设备列表 ===")
    for i in range(p.get_device_count()):
        try:
            device_info = p.get_device_info_by_index(i)
            name = device_info['name']
            is_input = device_info['maxInputChannels'] > 0
            is_output = device_info['maxOutputChannels'] > 0
            highlight = ''
            if 'AIUI-USB-MC' in name:
                highlight = '  <=== 发现目标输入设备'
            if 'USB Audio Device' in name:
                highlight = '  <=== 发现目标输出设备'
            print(f"设备 {i}: {name}{highlight}")
            # print(f"  输入通道: {device_info['maxInputChannels']}")
            # print(f"  输出通道: {device_info['maxOutputChannels']}")
            # print(f"  默认采样率: {device_info['defaultSampleRate']}")
        except Exception as e:
            print(f"设备 {i} 信息获取失败: {e}")
    print("==================")
    p.terminate()

if __name__ == "__main__":
    list_audio_devices() 