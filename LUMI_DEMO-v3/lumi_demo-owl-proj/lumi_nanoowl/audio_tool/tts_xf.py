# -*- coding:utf-8 -*-
#
#   author: iflytek
#
#  本demo测试时运行的环境为：Windows + Python3.7
#  本demo测试成功运行时所安装的第三方库及其版本如下：
#   cffi==1.12.3
#   gevent==1.4.0
#   greenlet==0.4.15
#   pycparser==2.19
#   six==1.12.0
#   websocket==0.2.1
#   websocket-client==0.56.0
#   合成小语种需要传输小语种文本、使用小语种发音人vcn、tte=unicode以及修改文本编码方式
#  错误码链接：https://www.xfyun.cn/document/error-code （code返回错误码时必看）
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
import websocket
import datetime
import hashlib
import base64
import hmac
import json
from urllib.parse import urlencode
import time
import ssl
from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime
import _thread as thread
import os
import numpy as np
import wave


STATUS_FIRST_FRAME = 0  # 第一帧的标识
STATUS_CONTINUE_FRAME = 1  # 中间帧标识
STATUS_LAST_FRAME = 2  # 最后一帧的标识


class Ws_Param(object):
    # 初始化
    def __init__(self, APPID, APIKey, APISecret, Text, speed=50):
        self.APPID = APPID
        self.APIKey = APIKey
        self.APISecret = APISecret
        self.Text = Text
        self.speed = speed
        # 公共参数(common)
        self.CommonArgs = {"app_id": self.APPID}
        # 业务参数(business)，包含语速设置
                # 业务参数(business)，更多个性化参数可在官网查看
        # self.BusinessArgs = {"aue": "raw", "auf": "audio/L16;rate=16000", "vcn": "x4_yezi", "tte": 
        # "utf8"}
        self.BusinessArgs = {"aue": "raw", "auf": "audio/L16;rate=16000", "vcn": "x4_yezi", "tte": 
        "utf8"}
        self.Data = {"status": 2, "text": str(base64.b64encode(self.Text.encode('utf-8')), "UTF8")}
        self.BusinessArgs = {
            "aue": "raw",
            "auf": "audio/L16;rate=16000",
            "vcn": "aisjinger",
            "tte": "utf8",
            "speed": str(self.speed)  # 语速参数 (0-100)
        }
        #使用小语种须使用以下方式，此处的unicode指的是 utf16小端的编码方式，即"UTF-16LE"”
        #self.Data = {"status": 2, "text": str(base64.b64encode(self.Text.encode('utf-16')), "UTF8")}
        self.Data = {"status": 2, "text": str(base64.b64encode(self.Text.encode('utf-8')), "UTF8")}

    # 生成url
    def create_url(self):
        url = 'wss://tts-api.xfyun.cn/v2/tts'
        # 生成RFC1123格式的时间戳
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        # 拼接字符串
        signature_origin = "host: " + "ws-api.xfyun.cn" + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + "/v2/tts " + "HTTP/1.1"
        # 进行hmac-sha256进行加密
        signature_sha = hmac.new(self.APISecret.encode('utf-8'), signature_origin.encode('utf-8'),
                                 digestmod=hashlib.sha256).digest()
        signature_sha = base64.b64encode(signature_sha).decode(encoding='utf-8')

        authorization_origin = "api_key=\"%s\", algorithm=\"%s\", headers=\"%s\", signature=\"%s\"" % (
            self.APIKey, "hmac-sha256", "host date request-line", signature_sha)
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
        # 将请求的鉴权参数组合为字典
        v = {
            "authorization": authorization,
            "date": date,
            "host": "ws-api.xfyun.cn"
        }
        # 拼接鉴权参数，生成url
        url = url + '?' + urlencode(v)
        # print("date: ",date)
        # print("v: ",v)
        # 此处打印出建立连接时候的url,参考本demo的时候可取消上方打印的注释，比对相同参数时生成的url与自己代码生成的url是否一致
        # print('websocket url :', url)
        return url

def on_message(ws, message):
    try:
        message =json.loads(message)
        code = message["code"]
        sid = message["sid"]
        audio = message["data"]["audio"]
        audio = base64.b64decode(audio)
        status = message["data"]["status"]
        print(f"讯飞TTS返回 code={code}, status={status}")
        # print(message)
        if code != 0:
            errMsg = message["message"]
            print("sid:%s call error:%s code is:%s" % (sid, errMsg, code))
        else:
            with open('./demo.pcm', 'ab') as f:
                f.write(audio)
        if status == 2:
            print("ws is closed")
            ws.close()
            # PCM转WAV
            pcm_path = './demo.pcm'
            wav_path = './exhabition-1.wav'
            with open(pcm_path, 'rb') as pcmfile:
                pcm_data = pcmfile.read()
            audio_data = np.frombuffer(pcm_data, dtype=np.int16)
            with wave.open(wav_path, 'wb') as wavfile:
                wavfile.setnchannels(1)
                wavfile.setsampwidth(2)
                wavfile.setframerate(16000)
                wavfile.writeframes(audio_data.tobytes())
            print("WAV文件已保存为", wav_path)
    except Exception as e:
        print("receive msg,but parse exception:", e)



# 收到websocket错误的处理
def on_error(ws, error):
    print("### error:", error)


# 收到websocket关闭的处理
def on_close(ws):
    print("### closed ###")


# 收到websocket连接建立的处理
def on_open(ws):
    def run(*args):
        d = {"common": wsParam.CommonArgs,
             "business": wsParam.BusinessArgs,
             "data": wsParam.Data,
             }
        d = json.dumps(d)
        print("------>开始发送文本数据")
        ws.send(d)
        if os.path.exists('./demo.pcm'):
            os.remove('./demo.pcm')

    thread.start_new_thread(run, ())





def synthesize_to_wav(text, wav_path, appid, apikey, apisecret):
    """
    合成文本为wav文件，保存到wav_path。
    """
    import websocket
    import ssl
    import json
    import base64
    import numpy as np
    import wave
    import os
    from wsgiref.handlers import format_date_time
    from datetime import datetime
    from time import mktime
    import hmac
    import hashlib
    from urllib.parse import urlencode
    import _thread as thread
    
    class Ws_Param(object):
        def __init__(self, APPID, APIKey, APISecret, Text):
            self.APPID = APPID
            self.APIKey = APIKey
            self.APISecret = APISecret
            self.Text = Text
            self.CommonArgs = {"app_id": self.APPID}
            # self.BusinessArgs = {"aue": "raw", "auf": "audio/L16;rate=16000", "vcn": "x4_yezi", "tte": "utf8"}
            self.BusinessArgs = {"aue": "raw", "auf": "audio/L16;rate=16000", "vcn": "aisjinger", "tte": "utf8"}
            self.Data = {"status": 2, "text": str(base64.b64encode(self.Text.encode('utf-8')), "UTF8")}
        def create_url(self):
            url = 'wss://tts-api.xfyun.cn/v2/tts'
            now = datetime.now()
            date = format_date_time(mktime(now.timetuple()))
            signature_origin = "host: " + "ws-api.xfyun.cn" + "\n"
            signature_origin += "date: " + date + "\n"
            signature_origin += "GET " + "/v2/tts " + "HTTP/1.1"
            signature_sha = hmac.new(self.APISecret.encode('utf-8'), signature_origin.encode('utf-8'), digestmod=hashlib.sha256).digest()
            signature_sha = base64.b64encode(signature_sha).decode(encoding='utf-8')
            authorization_origin = "api_key=\"%s\", algorithm=\"%s\", headers=\"%s\", signature=\"%s\"" % (
                self.APIKey, "hmac-sha256", "host date request-line", signature_sha)
            authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
            v = {"authorization": authorization, "date": date, "host": "ws-api.xfyun.cn"}
            url = url + '?' + urlencode(v)
            return url
    
    pcm_path = wav_path + ".tmp.pcm"
    if os.path.exists(pcm_path):
        os.remove(pcm_path)
    if os.path.exists(wav_path):
        os.remove(wav_path)
    
    wsParam = Ws_Param(appid, apikey, apisecret, text)
    wsUrl = wsParam.create_url()
    result = {"done": False, "error": None}
    
    def on_message(ws, message):
        try:
            message = json.loads(message)
            code = message["code"]
            audio = message["data"]["audio"]
            audio = base64.b64decode(audio)
            status = message["data"]["status"]
            if code != 0:
                result["error"] = message.get("message", "TTS error")
            else:
                with open(pcm_path, 'ab') as f:
                    f.write(audio)
            if status == 2:
                ws.close()
                # PCM转WAV
                with open(pcm_path, 'rb') as pcmfile:
                    pcm_data = pcmfile.read()
                audio_data = np.frombuffer(pcm_data, dtype=np.int16)
                with wave.open(wav_path, 'wb') as wavfile:
                    wavfile.setnchannels(1)
                    wavfile.setsampwidth(2)
                    wavfile.setframerate(16000)
                    wavfile.writeframes(audio_data.tobytes())
                result["done"] = True
        except Exception as e:
            result["error"] = str(e)
            ws.close()
    def on_error(ws, error):
        result["error"] = str(error)
        ws.close()
    def on_close(ws, close_status_code, close_msg):
        pass
    def on_open(ws):
        def run(*args):
            d = {"common": wsParam.CommonArgs, "business": wsParam.BusinessArgs, "data": wsParam.Data}
            d = json.dumps(d)
            ws.send(d)
        thread.start_new_thread(run, ())
    ws = websocket.WebSocketApp(wsUrl, on_message=on_message, on_error=on_error, on_close=on_close)
    ws.on_open = on_open
    ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
    if not result["done"]:
        raise RuntimeError(f"TTS synthesis failed: {result['error']}")
    if os.path.exists(pcm_path):
        os.remove(pcm_path)



if __name__ == "__main__":
    # 测试时候在此处正确填写相关信息即可运行
    wsParam = Ws_Param(APPID='', APISecret='',
                       APIKey='',
                       Text="")
    websocket.enableTrace(False)
    wsUrl = wsParam.create_url()
    ws = websocket.WebSocketApp(wsUrl, on_message=on_message, on_error=on_error, on_close=on_close)
    ws.on_open = on_open
    ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})