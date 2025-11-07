
import cv2
import json
from http import HTTPStatus
import dashscope
import numpy as np
from dashscope import MultiModalConversation
import os


PI=3.1415926

def loadJsonFile(jsonFile):
    with open(jsonFile,"r",encoding='utf8') as file:
        data=json.load(file)
        return data
    


# # 配置日志记录器
# def setup_logging(log_directory,file_name):
#     logger = logging.getLogger('logger')
#     logger.setLevel(logging.DEBUG)  # 设置日志级别

#     # 确保日志目录存在
#     if not os.path.exists(log_directory):
#         os.makedirs(log_directory)

#     # 创建一个文件处理器，并将日志级别设置为DEBUG
#     file_handler = logging.FileHandler(os.path.join(log_directory, 
#                                                     f'log_{file_name}_{datetime.datetime.now():%Y%m%d%H%M%S}.log'),
#                                                     encoding='utf-8')
#     file_handler.setLevel(logging.DEBUG)

#     # 创建一个日志格式
#     formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#     file_handler.setFormatter(formatter)

#     # 添加文件处理器到日志记录器
#     logger.addHandler(file_handler)
#     return logger

# # 使用日志记录器记录信息
# def log_message(message):
#     logger=logging.getLogger('logger')
#     logger.debug(message)

dashscope.api_key=os.getenv('DASHSCOPE_API_KEY')

# def draw_box(image, obj_locations, obj_lables, color=(0, 255, 0), font_scale=0.9, thickness=2):
#     """
#     在图像上绘制检测框和标签
#     :param image: 输入图像 (OpenCV 格式)
#     :param obj_positions: 检测框的坐标列表，每个框为 [x0, y0, x1, y1]
#     :param obj_names: 对应的标签名称列表
#     :param color: 检测框和标签的颜色，默认为绿色 (0, 255, 0)
#     :param font_scale: 字体大小，默认为 0.9
#     :param thickness: 检测框和字体的线宽，默认为 2
#     :return: 绘制后的图像
#     """
#     for current_obj_pos, obj_name in zip(obj_locations, obj_lables):
#         x0, y0, x1, y1 = current_obj_pos
#         # 绘制检测框
#         cv2.rectangle(image, (x0, y0), (x1, y1), color, thickness)
        
#         # 在框上方绘制标签
#         cv2.putText(image, obj_name, (x0, y0 - 10), cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness)
    
#     return image


# def conversation_call_test(image_file, text):
#     messages = [
#         {
#             "role": "system",
#             "content": [
#                 {"text": "你需要将用户给出的目标物体在图中框取出来，并返回坐标"},
#                 # {"prompt": "你需要将用户给出的物体在图中框取出来,坐标的原点设为左上角顶点，并且y轴向右增大而x轴向下增大，图像分辨率为4032*3024"}
#             ]
#         },
#         {
#             "role": "user",
#             "content": [
#                 {"image": image_file},  # file:///home/jaka/Documents/speech-to-control/mouse_box.jpeg
#                 {"text": text},
#                 # {"prompt": "你需要将用户给出的物体在图中框取出来,坐标的原点设为左上角顶点，并且y轴向右增大而x轴向下增大，图像分辨率为4032*3024"}
#             ]
#         }
#     ]
#     response = MultiModalConversation.call(model='qwen-vl-chat-v1',
#                                            # seed=random.randint(1,20000),
#                                            messages=messages)
#     if response.status_code == HTTPStatus.OK:
#         ans = response.output.choices[0].message.content
#         print('ans:',ans)
#     else:
#         ans = None
#         print(response.code)  # The error code.
#         print(response.message)  # The error message.
#     return ans






def simple_multimodal_conversation_call(image_file, text):
    """Simple single round multimodal conversation call.
    """
    messages = [
        {
            "role": "system",
            "content": [
                {"text": "Caption with Grounding"},
            ]

        },
        {
            "role": "user",
            "content": [
                {"image": image_file},  
                {"text": text},
            ]
        }
    ]

    response = MultiModalConversation.call(model='qwen-vl-max-2025-01-25',  
                                           # seed=random.randint(1,20000),
                                           messages=messages,
                                           result_format='message',
                                           response_format={'type': 'json_object'})
    # The response status_code is HTTPStatus.OK indicate success,
    # otherwise indicate request is failed, you can get error code
    # and message from code and message.

    if response.status_code == HTTPStatus.OK:
        ans = response.output.choices[0].message.content
    else:
        ans = None
        print(response.code)  # The error code.
        print(response.message)  # The error message.
    return ans

def vl_ali(tags,img_path):
    text = "请帮我将"
    for i in range(len(tags)):
        if i==len(tags)-1:
            text+="和"
        elif i>0:
            text+="，"
        text+=tags[i]
    text+="这{}种物体在图中框取出来".format(len(tags))
    print(text)
    image_file = f"file://{img_path}"
    ans=simple_multimodal_conversation_call(image_file,text)


    if ans and isinstance(ans, list) and len(ans) > 0:
        ans_text = ans[0].get('text', '')
        try:
            json_data = json.loads(ans_text.strip('```json\n').strip('```'))
            objs = [item['label'] for item in json_data]
            objPos = [[item['bbox_2d'][0], item['bbox_2d'][1], item['bbox_2d'][2], item['bbox_2d'][3]] for item in json_data]

        except json.JSONDecodeError as e:
            print(f"JSON ERROR: {e}")
            objs = []
            objPos = []
    else:
        objs = []
        objPos = [] 

    return objs,objPos

# def show_chinese(img,text,pos):
#     """
#     :param img: opencv 图片
#     :param text: 显示的中文字体
#     :param pos: 显示位置
#     :return:    带有字体的显示图片（包含中文）
#     """
#     img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
#     font = ImageFont.truetype(font='msyh.ttc', size=36)
#     draw = ImageDraw.Draw(img_pil)
#     draw.text(pos, text, font=font, fill=(255, 0, 0))  # PIL中RGB=(255,0,0)表示红色
#     img_cv = np.array(img_pil)                         # PIL图片转换为numpy
#     img = cv2.cvtColor(img_cv, cv2.COLOR_RGB2BGR)      # PIL格式转换为OpenCV的BGR格式
#     return img

# def call_with_messages_compose(sentence):
#     messages = [{'role': 'system', 'content': 'You are a helpful assistant.'},
#                 {'role': 'user', 'content': sentence}]
#     response = dashscope.Generation.call(
#         dashscope.Generation.Models.qwen_max,
#         seed=random.randint(1,10000),
#         messages=messages,
#         result_format='message',  # set the result to be "message" format.
#     )
#     json_ans = list()
#     if response.status_code == HTTPStatus.OK:
#         str_ans=response.output.choices[0].message["content"]
#         print(str_ans)
#         try:
#             ans = str_ans.split('；') if '；' in str_ans else str_ans.split(';')
#             for tmp in ans:
#                 json_ans.append(tmp)
#         except:
#             json_ans.append(str_ans)
#     else:
#         print('Request id: %s, Status code: %s, error code: %s, error message: %s' % (
#             response.request_id, response.status_code,
#             response.code, response.message
#         ))
#     return json_ans

# def call_with_messages_sortTask(sentence,tmpKey):
#     messages = [{'role': 'system', 'content': 'You are a helpful assistant.'},
#                 {'role': 'user', 'content': sentence}]
#     response = dashscope.Generation.call(
#         dashscope.Generation.Models.qwen_max,
#         seed=random.randint(1, 10000),
#         messages=messages,
#         result_format='message',  # set the result to be "message" format.
#     )
#     json_ans = dict()
#     if response.status_code == HTTPStatus.OK:
#         str_ans=response.output.choices[0].message["content"]
#         print(str_ans)
#         # json_ans=dict()
#         try:
#             tmpKey = ["物体1","物体2"] if len(tmpKey)==0 else tmpKey

#             # ans=str_ans.split('；')  # 情况1： allKey:allValue;    情况2：旋转角度: 30度; 运动类型: 左转;
#             ans = str_ans.split('；') if '；' in str_ans else str_ans.split(';')
#             if ":" in str_ans or "：" in str_ans:
#                 if "其他关键词:None" in str_ans:  # 关节位置;旋转角度:30度;运动类型:旋转;其他关键词:None
#                     str_ans=str_ans.replace("其他关键词:None","")
#                     if str_ans[-1]==";":
#                         str_ans=str_ans[:-1]
#                 for tmp in ans:
#                     if ":" in tmp or "：" in tmp:  # "你好；None；None；None；None；None；IO；None；None；物体1：白色的巧克力；物体2：旁边的白色盒子"
#                         tmp1=tmp.split('：') if '：' in str_ans else tmp.split(':')
#                         # print(tmp1)
#                         json_ans.update({str(tmp1[0]).strip():str(tmp1[1]).strip()})
#                 if len(json_ans.keys()) != len(tmpKey):
#                     for k in tmpKey:
#                         if k not in json_ans.keys():
#                             json_ans.update({k: "None"})
#                 # print(json_ans)
#                 # return json_ans
#             elif len(ans) == len(tmpKey):
#                 # 第五个关节；右；旋转；五十度；None；None；None；None；运动；None；None
#                 # 第五个关节；向右；旋转；五十度；None；None；None；None；None；None；None
#                 # None; None; None; None; None; None; None; None; 移动; 卷尺; 纸盒子旁边
#                 for tmp in ans:
#                     if "移动" in tmp or "转动" in tmp or "旋转" in tmp:
#                         continue
#                     # None;None;None;None;None;None;None;None;抓取;白色巧克力;白色盒子  -> TODO
#                     # TODO : 多物体未定义，
#                     else:
#                         if "物体1" not in json_ans.keys():
#                             json_ans.update({"物体1": str(tmp)})
#                         if "物体1" in json_ans.keys():
#                             json_ans.update({"物体2": str(tmp)})

#                 for tmpKey in tmpKey:  # 追加空闲key的value为None
#                     if tmpKey not in json_ans:
#                         json_ans[tmpKey] = "None"

#             # 你好；None；None；None；None；None；None；None；运动类型：抓取；物体1：白色的巧克力；物体2：旁边的白色盒子。
#             else:
#                 for spliteTmp in ans:
#                     if ":" in str_ans or "：" in str_ans:
#                         tmp1 = spliteTmp.split('：') if '：' in str_ans else spliteTmp.split(':')
#                         # print(tmp1)
#                         json_ans.update({str(tmp1[0]).strip(): str(tmp1[1]).strip()})
#                 for tmpKey in tmpKey:  # 追加空闲key的value为None
#                     if tmpKey not in json_ans:
#                         json_ans[tmpKey] = "None"

#         except:
#             ans = str_ans.split(';')
#             for tmp in ans:
#                 tmp1 = tmp.split(':')
#                 # print(tmp1)
#                 json_ans.update({str(tmp1[0]).strip(): str(tmp1[1]).strip()})
#             # print(json_ans)
#     else:
#         print('Request id: %s, Status code: %s, error code: %s, error message: %s' % (
#             response.request_id, response.status_code,
#             response.code, response.message
#         ))
#     # print(json_ans)
#     return json_ans


# def feedBackDataClean_sortTask(mapJsonData,feedBackData):
#     # 关节位置;旋转角度:30度;运动类型:旋转;其他关键词:None
#     if "其余关键词值" in feedBackData.keys():
#         for tmpKey in mapJsonData["sortTask"]["cmdKeys"]:
#             if tmpKey not in feedBackData:
#                 feedBackData[tmpKey] = "None"

#     # flagRepeatKeysTogther=False
#     countRepeatKeysTogther=0
#     for k in feedBackData.keys():
#         if k in mapJsonData["sortTask"]["cmdKeys"]:
#             countRepeatKeysTogther+=1
#     if countRepeatKeysTogther<len(mapJsonData["sortTask"]["cmdKeys"]):
#         tmpData = dict()
#         for k in feedBackData.keys():
#             if k in mapJsonData["sortTask"]["cmdKeys"]:
#                 tmpData[k] = feedBackData[k]
#             else:
#                 if "、" in k:
#                     for tmp in k.split("、"):
#                         tmpData[tmp] = feedBackData[k]
#                 elif "、 " in k:
#                     for tmp in k.split("、 "):
#                         tmpData[tmp] = feedBackData[k]
#         for k in mapJsonData["sortTask"]["cmdKeys"]:
#             if k not in tmpData.keys():
#                 tmpData[k] = 'None'
#         feedBackData = tmpData

#     for tmpKey in mapJsonData["sortTask"]["cmdKeys"]:  # feedBackData value中有 类似情况： '坐标系': '无明确值' 需要清洗数据
#         if feedBackData[tmpKey] in mapJsonData["sortTask"]["illegalVal"]:
#             feedBackData[tmpKey] = "None"

#     # 其他关键词值默认为None，因此不额外列出。输出结果为：旋转角度: 30度;运动类型: 左转;
#     return feedBackData

# 将机器人向前移动10cm
# 你好，机器人上使能，机器人末端圆弧运动,使用世界坐标系，工具IO，退出拖拽模式，将机器人左臂向前移动10mm左右°。总结出并只输出前一句话中关于 机械臂的位置、关节、方向、动作、角度、距离、IO、坐标系、运动类型、是否上下电、是否上下使能 这十一个关键词的值，没有填NLL，输出结果用分号分割
# def call_with_messages(sentence,tmpKey):
#     messages = [{'role': 'system', 'content': 'You are a helpful assistant.'},
#                 {'role': 'user', 'content': sentence}]
#                 # {'role': 'user', 'content': '你好，机器人上使能，机器人末端圆弧运动,使用世界坐标系，工具IO，退出拖拽模式，将机器人向前移动10mm左右°。总结出并只输出前一句话中涉及机械臂的位置、关节、方向、动作、角度、IO、坐标系、运动类型、是否上电、是否上使能、SDK版本、进入拖拽模式这十四个关键词的值，没有填NLL，输出结果用分号分割'}]

#     response = dashscope.Generation.call(
#         dashscope.Generation.Models.qwen_max,
#         messages=messages,
#         result_format='message',  # set the result to be "message" format.
#     )
#     json_ans = dict()
#     if response.status_code == HTTPStatus.OK:
#         str_ans=response.output.choices[0].message["content"]
#         print(str_ans)
#         # json_ans=dict()
#         try:
#             tmpKey = ["运动目标位置", "关节位置", "运动方向", "运动速度", "旋转角度", "运动距离", "IO", "坐标系",
#                       "运动类型","上下电", "上下使能"] if len(tmpKey)==0 else tmpKey

#             # ans=str_ans.split('；')  # 情况1： allKey:allValue;    情况2：旋转角度: 30度; 运动类型: 左转;
#             ans = str_ans.split('；') if '；' in str_ans else str_ans.split(';')
#             if ":" in str_ans or "：" in str_ans:
#                 if "其他关键词:None" in str_ans:  # 关节位置;旋转角度:30度;运动类型:旋转;其他关键词:None
#                     str_ans=str_ans.replace("其他关键词:None","")
#                     if str_ans[-1]==";":
#                         str_ans=str_ans[:-1]
#                 for tmp in ans:
#                     if ":" in tmp or "：" in tmp:  # "你好；None；None；None；None；None；IO；None；None；物体1：白色的巧克力；物体2：旁边的白色盒子"
#                         tmp1=tmp.split('：') if '：' in str_ans else tmp.split(':')
#                         # print(tmp1)
#                         json_ans.update({str(tmp1[0]).strip():str(tmp1[1]).strip()})
#                 if len(json_ans.keys()) != len(tmpKey):
#                     for k in tmpKey:
#                         if k not in json_ans.keys():
#                             json_ans.update({k: "None"})
#                 # print(json_ans)
#                 # return json_ans
#             elif len(ans) == len(tmpKey):
#                 # 第五个关节；右；旋转；五十度；None；None；None；None；运动；None；None
#                 # 第五个关节；向右；旋转；五十度；None；None；None；None；None；None；None
#                 # None; None; None; None; None; None; None; None; 移动; 卷尺; 纸盒子旁边
#                 for tmp in ans:
#                     if "个关节" in tmp:
#                         json_ans.update({"关节位置": str(tmp).strip()})
#                     elif "直线" in tmp or "旋转" in tmp:
#                         json_ans.update({"运动类型": str(tmp).strip()})
#                     elif "右" in tmp or "左" in tmp  or "前" in tmp or "后" in tmp:
#                         json_ans.update({"运动方向": str(tmp).strip()})
#                     elif "初始点" in tmp or "起始点" in tmp or "原点" in tmp:
#                         json_ans.update({"运动类型": str(tmp).strip()})
#                     elif parseJointMoveLocation(tmp,"IsContainNum"):
#                         if "度" in tmp:
#                             json_ans.update({"旋转角度": str(tmp).strip()})
#                         elif "mm" in tmp or "cm" in tmp or "毫米" in tmp or "厘米" in tmp:
#                             json_ans.update({"运动距离": str(tmp).strip()})
#                         elif "rad/s" in tmp or "弧度每秒" in tmp or "弧度/s" in tmp:
#                             json_ans.update({"运动速度": str(tmp).strip()})
#                         else:
#                             json_ans.update({"旋转角度": str(tmp).strip()})
#                             json_ans.update({"运动距离": str(tmp).strip()})
#                             json_ans.update({"运动速度": str(tmp).strip()})
#                     # None;None;None;None;None;None;None;None;抓取;白色巧克力;白色盒子  -> TODO
#                     # TODO : 多物体未定义，
#                     else:
#                         if "物体1" not in json_ans.keys():
#                             json_ans.update({"物体1": str(tmp)})
#                         if "物体1" in json_ans.keys():
#                             json_ans.update({"物体2": str(tmp)})


#                 for tmpKey in tmpKey:  # 追加空闲key的value为None
#                     if tmpKey not in json_ans:
#                         json_ans[tmpKey] = "None"

#             # 你好；None；None；None；None；None；None；None；运动类型：抓取；物体1：白色的巧克力；物体2：旁边的白色盒子。
#             else:
#                 for spliteTmp in ans:
#                     if ":" in str_ans or "：" in str_ans:
#                         tmp1 = spliteTmp.split('：') if '：' in str_ans else spliteTmp.split(':')
#                         # print(tmp1)
#                         json_ans.update({str(tmp1[0]).strip(): str(tmp1[1]).strip()})
#                 for tmpKey in tmpKey:  # 追加空闲key的value为None
#                     if tmpKey not in json_ans:
#                         json_ans[tmpKey] = "None"

#         except:
#             ans = str_ans.split(';')
#             for tmp in ans:
#                 tmp1 = tmp.split(':')
#                 # print(tmp1)
#                 json_ans.update({str(tmp1[0]).strip(): str(tmp1[1]).strip()})
#             # print(json_ans)
#     else:
#         print('Request id: %s, Status code: %s, error code: %s, error message: %s' % (
#             response.request_id, response.status_code,
#             response.code, response.message
#         ))
#     # print(json_ans)
#     return json_ans


# # def loadJsonFile(jsonFile):
# #     with open(jsonFile,"r",encoding='utf8') as file:
# #         data=json.load(file)
# #         return data


    
# # def prepare_data(path, size):
#     with open(path, 'r', encoding='utf-8') as f:
#         batch_docs = []
#         for line in f:
#             batch_docs.append(json.loads(line.strip()))
#             if len(batch_docs) == size:
#                 yield batch_docs[:]
#                 batch_docs.clear()

#         if batch_docs:
#             yield batch_docs


# # def generate_embeddings(text):
#     rsp = TextEmbedding.call(model=TextEmbedding.Models.text_embedding_v1,
#                              input=text)

#     embeddings = [record['embedding'] for record in rsp.output['embeddings']]
#     return embeddings if isinstance(text, list) else embeddings[0]

# # def vetcot2collect(confJson):
#     # 初始化 DashVector client
#     conf = loadJsonFile(confJson)
#     client = Client(
#         api_key=conf["api_key"], # 'sk-2QKtFSOSICUPRXXtkivk4SKBUOIzH23516028FDFE11EEA4214E009C2843BF',
#         endpoint=conf["endpoint"] # 'vrs-cn-x0r3pcwj900024.dashvector.cn-hangzhou.aliyuncs.com'
#     )

#     try:
#         # 指定集合名称和向量维度
#         rsp = client.create('sample', 1536)
#         assert rsp

#     except:
#         collection = client.get('sample')
#         assert collection

#         batch_size = 10
#         for docs in list(prepare_data('conf/ccl.json', batch_size)):
#             # 批量 embedding
#             embeddings = generate_embeddings([doc['title'] for doc in docs])

#             # 批量写入数据
#             rsp = collection.insert(
#                 [
#                     Doc(id=str(doc['id']), vector=embedding, fields={"title": doc['title']})
#                     for doc, embedding in zip(docs, embeddings)
#                 ]
#             )
#             assert rsp
#         return True
# # def initDashVectorClient(confJson):
#     conf=loadJsonFile(confJson)
#     # 初始化 DashVector client
#     client = Client(
#         api_key=conf["api_key"],
#         endpoint=conf["endpoint"]
#     )
#     try:
#         # 指定集合名称和向量维度
#         rsp = client.create('sample', 1536)  #1536
#         assert rsp
#         print('rsp--------------:',rsp)
#         collection = client.get('sample')
#         assert collection
#         return collection
#     except:
#         collection = client.get('sample')
#         assert collection
#         return collection

# # TODO
# # def parseStr2ListInt(strs):
#     flagUnit=1
#     mappingNumber = {
#         "零": 0,
#         "一": 1,
#         "二": 2,
#         "三": 3,
#         "四": 4,
#         "五": 5,
#         "六": 6,
#         "七": 7,
#         "八": 8,
#         "九": 9,
#         "十": 10,
#         "百": 100,
#         "0": 0,
#         "1": 1,
#         "2": 2,
#         "3": 3,
#         "4": 4,
#         "5": 5,
#         "6": 6,
#         "7": 7,
#         "8": 8,
#         "9": 9
#     }
#     mappingUnit={
#         "mm":1,
#         "毫米":1,
#         "cm":10,
#         "厘米":10,
#         "dm":100,
#         "分米":100,
#         # "m":1000,
#         # "米":1000
#     }
#     for k in mappingUnit.keys():
#         if k in strs:
#             flagUnit=mappingUnit[k]
#     # pattern=r"\d+"
#     # numbers=re.findall(pattern,strs) if re.findall(pattern,strs) else [0]
#     startIndex = 0
#     ss = ""
#     while strs[startIndex] not in mappingNumber:
#         startIndex += 1
#     while strs[startIndex] in mappingNumber:
#         ss += strs[startIndex]
#         startIndex += 1
#     numbers = transform(ss)
#     print('pre params is : '+strs + ',\tand parse params is: '+str(int(numbers)*flagUnit))
#     return int(numbers)*flagUnit

# def parseJointMoveLocation(strs,joninType):
#     '''
#     ！！！ 只支持单关节运动，多关节一起旋转运动待语音转换模块输出测试 ！！！
#     location: 二关节  2关节
#     angle: 三十五度  35度
#     :param strs:
#     :param joninType: location,angle
#     :return: jointLocal,rotate angle
#     '''
#     mappingNumber={
#         "零":0,
#         "一":1,
#         "二":2,
#         "三":3,
#         "四":4,
#         "五":5,
#         "六":6,
#         "七":7,
#         "八":8,
#         "九":9,
#         "十":10,
#         "百": 100,
#         "0": 0,
#         "1":1,
#         "2":2,
#         "3":3,
#         "4":4,
#         "5":5,
#         "6":6,
#         "7":7,
#         "8":8,
#         "9":9
#     }
#     if joninType=="location":
#         for tmp in strs:
#             if tmp in mappingNumber and mappingNumber[tmp]<7:
#                 return mappingNumber[tmp]
#         return None
#     elif joninType=="angle":
#         if strs=='None':
#             return 50.0/180.0*PI
#         startIndex=0
#         ss=""
#         while strs[startIndex] not in mappingNumber:
#             startIndex+=1
#         while strs[startIndex] in mappingNumber:
#             ss+=strs[startIndex]
#             startIndex += 1
#         angles = transform(ss)
#         # print("angles： "+str(angles))
#         return float(angles)/180.0*PI if angles else 0  #math.radians(angles)
#     elif joninType=="IsContainNum":
#         for tmp in strs:
#             if tmp in mappingNumber:
#                 return True
#         return False
# def parseJointMoveLocation2(strs,joninType):
#     '''
#     ！！！ 只支持单关节运动，多关节一起旋转运动待语音转换模块输出测试 ！！！
#     location: 二关节  2关节
#     angle: 三十五度  35度
#     :param strs:
#     :param joninType: location,angle
#     :return: jointLocal,rotate angle
#     '''
#     mappingNumber={
#         "零":0,
#         "一":1,
#         "二":2,
#         "三":3,
#         "四":4,
#         "五":5,
#         "六":6,
#         "七":7,
#         "八":8,
#         "九":9,
#         "十":10,
#         "百": 100,
#         "0": 0,
#         "1":1,
#         "2":2,
#         "3":3,
#         "4":4,
#         "5":5,
#         "6":6,
#         "7":7,
#         "8":8,
#         "9":9
#     }
#     if joninType=="location":
#         for tmp in strs:
#             if tmp in mappingNumber and mappingNumber[tmp]<7:
#                 return mappingNumber[tmp]
#         return None
#     elif joninType=="angle":
#         startIndex=0
#         angles = 0
#         while strs[startIndex] not in mappingNumber:
#             startIndex+=1
#         while strs[startIndex] in mappingNumber:
#             if mappingNumber[strs[startIndex]]==10 or mappingNumber[strs[startIndex]]==100:
#                 angles = angles * mappingNumber[strs[startIndex]]
#                 startIndex += 1
#                 continue
#             angles=angles*10+mappingNumber[strs[startIndex]]
#             startIndex+=1
#         print("angles： "+str(angles))
#         return  angles/180.0*PI    #math.radians(angles)
#     else:
#         return None

# def feedBackDataClean(mapJsonData,feedBackData):
    # 关节位置;旋转角度:30度;运动类型:旋转;其他关键词:None
    if "其余关键词值" in feedBackData.keys():
        for tmpKey in mapJsonData["cmdKeys"]:
            if tmpKey not in feedBackData:
                feedBackData[tmpKey] = "None"

    # flagRepeatKeysTogther=False
    countRepeatKeysTogther=0
    for k in feedBackData.keys():
        if k in mapJsonData["cmdKeys"]:
            countRepeatKeysTogther+=1
    if countRepeatKeysTogther<len(mapJsonData["cmdKeys"]):
        tmpData = dict()
        for k in feedBackData.keys():
            if k in mapJsonData["cmdKeys"]:
                tmpData[k] = feedBackData[k]
            else:
                if "、" in k:
                    for tmp in k.split("、"):
                        tmpData[tmp] = feedBackData[k]
                elif "、 " in k:
                    for tmp in k.split("、 "):
                        tmpData[tmp] = feedBackData[k]
        for k in mapJsonData["cmdKeys"]:
            if k not in tmpData.keys():
                tmpData[k] = 'None'
        feedBackData = tmpData

    for tmpKey in mapJsonData["cmdKeys"]:  # feedBackData value中有 类似情况： '坐标系': '无明确值' 需要清洗数据
        if feedBackData[tmpKey] in mapJsonData["illegalVal"]:
            feedBackData[tmpKey] = "None"

    # 其他关键词值默认为None，因此不额外列出。输出结果为：旋转角度: 30度;运动类型: 左转;

    return feedBackData

# # 绝对运动
# def generateFBPosABS(homePose_world,mappingDirect,mappingValue,moveDistance=50):
#     # moveDistance: defaultTherod
#     current_xyz=list()
#     models_vertor = np.linalg.norm(list(homePose_world)[:3])
#     if mappingDirect=="1":  # 前后
#         current_xyz = [homePose_world[0]] + [homePose_world[1] + (homePose_world[1] / models_vertor) * int(moveDistance) * int(mappingValue)] + list(homePose_world[2:])
#     elif mappingDirect=="2": # 左右
#         current_xyz = [homePose_world[0] + (homePose_world[0] / models_vertor) * int(moveDistance) * int(mappingValue)] + list(homePose_world[1:])
#     elif mappingDirect=="3": # 上下
#         current_xyz = list(homePose_world[:2]) + [homePose_world[2] + (homePose_world[2] / models_vertor) * int(moveDistance) * int(mappingValue)] + list(homePose_world[3:])
#     return current_xyz

# # 相对运动
# def generateFBPosINCR(homePose_world,mappingDirect,mappingValue,moveDistance=50):
#     # moveDistance: defaultTherod
#     current_xyz=[0,0,0,0,0,0]
#     if mappingDirect=="1":  # 前后
#         current_xyz[1]=int(moveDistance) * int(mappingValue)
#     elif mappingDirect=="2": # 左右
#         current_xyz[0] = int(moveDistance) * int(mappingValue)
#     elif mappingDirect=="3": # 上下
#         current_xyz[2] = int(moveDistance) * int(mappingValue)
#     return current_xyz

def pixel_to_world(pixel_xy, depth, K, R_camera_to_world, T_camera_to_world):
    u, v = pixel_xy
    #  # Intrinsic parameters
    fx, fy = K[0][0], K[1][1]  
    cx, cy = K[0][2], K[1][2]  

    x_n = (u - cx) / fx
    y_n = (v - cy) / fy

    X_c = depth * x_n
    Y_c = depth * y_n
    Z_c = depth

    P_camera=np.array([X_c,Y_c,Z_c])
    T_camera_to_world=np.array(T_camera_to_world).reshape(3)
    P_world=np.dot(np.array(R_camera_to_world),P_camera)+T_camera_to_world
    print('Pix_to_world:' ,P_world)
    return P_world

# def rotation_and_translation_to_base(x_offset, y_offset, z_offset, roll_degrees, pitch_degrees, yaw_degrees):

#     # 将角度从度转换为弧度
#     roll_rad = np.radians(roll_degrees)
#     pitch_rad = np.radians(pitch_degrees)
#     yaw_rad = np.radians(yaw_degrees)

#     # 使用欧拉角（roll, pitch, yaw）构造旋转矩阵
#     R = Rotation.from_euler('xyz', [yaw_rad, pitch_rad, roll_rad]).as_matrix()  # 注意这里的顺序是按照yaw-pitch-roll，因为是从基座到相机的方向

#     # 构建偏移矩阵（这里直接使用偏移值，注意顺序应与旋转矩阵的定义相匹配）
#     T = np.array([x_offset, y_offset, z_offset])

#     return R, T


# def calculate_transform_matrix(x_offset, y_offset, rotation_angle_deg):
#     # 将角度转换为弧度
#     rotation_angle_rad = np.deg2rad(rotation_angle_deg)

#     # 构建旋转矩阵R
#     R = np.array([
#         [np.cos(rotation_angle_rad), -np.sin(rotation_angle_rad), 0],
#         [np.sin(rotation_angle_rad), np.cos(rotation_angle_rad), 0],
#         [0, 0, 1]
#     ])

#     # 构建平移向量T并转换为齐次形式
#     T = np.array([x_offset, y_offset, 0])
#     T = np.append(T, [1])  # 添加1以构造齐次坐标

#     # 创建并返回4x4的变换矩阵H
#     H = np.eye(4)
#     H[:3, :3] = R
#     H[:3, 3] = T[:3]

#     return H

def findCorners(img,boardWidth,boardHeight):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ret, corners = cv2.findChessboardCorners(gray, (boardWidth, boardHeight), None)
    return ret

def generatorNearPoints(current_pos,near_point_interval=2,nums=2):
    # currentPos = [10, 10]
    points = []
    points.append(current_pos)
    for i in range(1, nums + 1):
        left_top_x = current_pos[0] - near_point_interval * i
        left_top_y = current_pos[1] - near_point_interval * i

        right_bottom_x = current_pos[0] + near_point_interval * i
        right_bottom_y = current_pos[1] + near_point_interval * i

        for i in range(left_top_x, right_bottom_x + near_point_interval, near_point_interval):
            points.append([i, left_top_y])
            points.append([i, right_bottom_y])
        for j in range(left_top_y + near_point_interval, right_bottom_y, near_point_interval):
            points.append([left_top_y, j])
            points.append([right_bottom_y, j])

    return points

# def is_point_in_rectangle(pxy,rect):
#    '''
#    判断点(px, py)是否在矩形(x1, y1, x2, y2)内
#    '''
#    return rect[0]<=pxy[0]<=rect[2] and rect[1]<=pxy[1]<=rect[3]

def saveOriginImg(color_image,save_dir):
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    # 获取目录下已有的文件数量
    files = os.listdir(save_dir)
    img_name = f"{len(files) + 1}.jpg"
    # 构造保存路径
    img_path = os.path.join(save_dir, img_name)
    
    # 保存图像
    cv2.imwrite(img_path, color_image)
    return os.path.abspath(img_path)



# if __name__ == '__main__':
#     t=time.time()
#     sentence='你好，机器人下使能，机器人下电，机器人末端圆弧运动,使用世界坐标系，工具IO，退出拖拽模式，将机器人左臂向前移动10mm左右°。总结出并只输出前一句话中关于 机械臂的位置、关节、方向、动作、角度、距离、IO、坐标系、运动类型、上下电、上下使能 这十一个关键词的值，没有填None，输出结果用分号分割'
#     call_with_messages(sentence)
#     print(f'coast:{time.time() - t:.8f}s')
