import cv2
import json
from http import HTTPStatus
import dashscope
import numpy as np
from dashscope import MultiModalConversation
import os

# dashscope.api_key=os.getenv('DASHSCOPE_API_KEY')

# dashscope.api_key="sk-c9397316a4494728968dcc5ac2581509"
dashscope.api_key = "sk-6c7020bcf3a246e09baa71020269230a"


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
            text+=""
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


if __name__ == '__main__':

    img_path = "./data/Color/3.png"
    tags = ["风油精","创可贴","蒲地兰消炎片","西瓜霜消炎片","瓶装酒精","棕色瓶子碘酒",'布洛芬缓释胶囊','红霉素软膏','感冒灵颗粒']
    objs, objPos = vl_ali(tags, img_path)
    print("objs,objPos:", objs, objPos)

    # 读取原图
    img = cv2.imread(img_path)
    # 画框和标签
    for i, bbox in enumerate(objPos):
        x1, y1, x2, y2 = bbox
        cv2.rectangle(img, (x1, y1), (x2, y2), (0,255,0), 2)
        cv2.putText(img, objs[i], (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,255), 2)
    # 保存结果
    save_path = img_path.replace('.png', '_boxed.png')
    cv2.imwrite(save_path, img)
    print(f"保存画框结果到: {save_path}")