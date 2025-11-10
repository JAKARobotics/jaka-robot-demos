# SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# 本脚本为基于aiohttp的Web服务，结合NanoOwl多目标检测模型，实现摄像头实时检测、WebSocket推送检测结果、动态文本提示等功能。
# 支持自定义模型、推理引擎、摄像头分辨率、Web端交互等。

'''
工作模式:
模式1：实时监控（无检测）
用户访问 Web 页面
持续推送原始相机画面
不进行任何检测

模式2：目标检测
前端发送检测请求（POST /detect）
更新 current_tags 全局变量
开始检测指定目标并画框
推送检测结果图像


数据流向
相机 → Camera类 → detection_loop → 
├─ 原始图像 → WebSocket推送 → 前端显示
└─ 检测图像 → 阿里API → 画框 → WebSocket推送 → 前端显示
'''

import asyncio
import argparse
from aiohttp import web, WSCloseCode
import logging
import weakref
import cv2
import time
import PIL.Image
import matplotlib.pyplot as plt
from typing import List, Optional
from nanoowl.tree import Tree
from nanoowl.tree_predictor import (
    TreePredictor
)
from nanoowl.tree_drawing import draw_tree_output
from nanoowl.owl_predictor import OwlPredictor
import numpy as np
import json
from infer_owl import det_owl_image
from PIL import Image
import sys
import os
from test_ali import vl_ali
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
# from orbbecCamera import Camera
from multi_camera_manager import Camera


# 自定义画框函数，支持自定义颜色
def draw_owl_output(image, output, text, draw_text=True, colors=None):
    import cv2
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
    import os
    
    is_pil = not isinstance(image, np.ndarray)
    if is_pil:
        image = np.asarray(image)
        if not image.flags.writeable:
            image = image.copy()
    
    if colors is None:
        # 默认彩虹色
        cmap = plt.cm.get_cmap("rainbow", len(text))
        colors = []
        for i in range(len(text)):
            color = cmap(i)
            color = [int(255 * value) for value in color]
            colors.append(tuple(color))
    
    num_detections = len(output.labels)
    for i in range(num_detections):
        box = output.boxes[i]
        label_index = int(output.labels[i])
        box = [int(x) for x in box]
        pt0 = (box[0], box[1])
        pt1 = (box[2], box[3])
        cv2.rectangle(
            image,
            pt0,
            pt1,
            colors[label_index],
            4
        )
    
    # 如果有文本需要绘制，使用PIL绘制中文
    if draw_text and num_detections > 0:
        # 转换为PIL图像
        pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil_image)
        
        # 尝试加载中文字体
        font_size = 20
        try:
            # 尝试多个常见的中文字体路径
            font_paths = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/System/Library/Fonts/PingFang.ttc",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
                "/usr/share/fonts/truetype/ubuntu/Ubuntu-Regular.ttf"
            ]
            font = None
            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        font = ImageFont.truetype(font_path, font_size)
                        break
                    except:
                        continue
            
            if font is None:
                # 如果找不到字体文件，使用默认字体
                font = ImageFont.load_default()
        except:
            font = ImageFont.load_default()
        
        # 绘制文本
        for i in range(num_detections):
            box = output.boxes[i]
            label_index = int(output.labels[i])
            label_text = text[label_index]
            color = colors[label_index]
            
            # 计算文本位置
            text_x = box[0]
            text_y = box[1] - 25  # 在框的上方显示文本
            
            # 绘制文本背景（可选）
            try:
                # 获取文本边界框
                bbox = draw.textbbox((0, 0), label_text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                # 绘制背景矩形
                bg_color = (0, 0, 0, 128)  # 半透明黑色
                draw.rectangle(
                    [text_x, text_y, text_x + text_width, text_y + text_height],
                    fill=bg_color
                )
            except:
                pass
            
            # 绘制文本
            draw.text((text_x, text_y), label_text, font=font, fill=color)
        
        # 转换回OpenCV格式
        image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    
    if is_pil:
        from PIL import Image as PILImage
        image = PILImage.fromarray(image)
    return image

latest_color_img = None
latest_depth_data = None
websockets = weakref.WeakSet()

# 新增：全局变量，保存当前检测tag和参数
current_tags = []
current_conf = 0.2
current_iou = 0.8

# # COCO80类别
# COCO80 = [
#     "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat", "traffic light",
#     "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat", "dog", "horse", "sheep", "cow",
#     "elephant", "bear", "zebra", "giraffe", "backpack", "umbrella", "handbag", "tie", "suitcase", "frisbee",
#     "skis", "snowboard", "sports ball", "kite", "baseball bat", "baseball glove", "skateboard", "surfboard",
#     "tennis racket", "bottle", "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana", "apple",
#     "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair", "couch",
#     "potted plant", "bed", "dining table", "toilet", "tv", "laptop", "mouse", "remote", "keyboard", "cell phone",
#     "microwave", "oven", "toaster", "sink", "refrigerator", "book", "clock", "vase", "scissors", "teddy bear",
#     "hair drier", "toothbrush", "screwdriver", "wrench", "pliers", "hammer", "tape measure", "electric drill", "Glue gun", "Wire", "Metal ring", "Metal clamp", "double-sided tape","medicine"
# ]
COCO80 = []

# 颜色定义
ORANGE = (255, 128, 0)
BLUE = (0, 128, 255)

if __name__ == "__main__":
    '''  
    python3 lumi_demo_ali.py --camera-sn AY8V74300F4

    '''
    # 解析命令行参数
    parser = argparse.ArgumentParser()
    parser.add_argument("--image_quality", type=int, default=50)
    parser.add_argument("--port", type=int, default=7861) # 7860
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--camera-sn", type=str, default='AY8V74300F4', help="指定要使用的相机序列号")
    parser.add_argument("--resolution", type=str, default="1280x800", help="Camera resolution as WIDTHxHEIGHT")
    args = parser.parse_args()
    width, height = map(int, args.resolution.split("x"))

    IMAGE_QUALITY = args.image_quality
    CAMERA_SN = args.camera_sn

    # 获取可视化用的彩色列表
    def get_colors(count: int):
        cmap = plt.cm.get_cmap("rainbow", count)
        colors = []
        for i in range(count):
            color = cmap(i)
            color = [int(255 * value) for value in color]
            colors.append(tuple(color))
        return colors

    # OpenCV BGR转PIL RGB
    def cv2_to_pil(image):
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        return PIL.Image.fromarray(image)

    # 处理Web首页请求，返回前端页面
    async def handle_index_get(request: web.Request):
        logging.info("handle_index_get")
        return web.FileResponse("./lumi_index.html")

    # WebSocket处理，接收前端prompt，编码后存入全局变量
    async def websocket_handler(request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        websockets.add(ws)
        try:
            async for msg in ws:
                pass
        finally:
            websockets.discard(ws)
        return ws

    # 关闭WebSocket时的清理操作
    async def on_shutdown(app: web.Application):
        for ws in set(app['websockets']):
            await ws.close(code=WSCloseCode.GOING_AWAY,
                        message='Server shutdown')

    # 摄像头检测主循环，实时读取帧、推理、画框、编码JPEG并推送WebSocket
    async def detection_loop(app: web.Application):
        global latest_color_img, latest_depth_data, current_tags, current_conf, current_iou
        cam = Camera(serial_number=CAMERA_SN)
        while True:
            color_img, depth_data, _ = cam.getColorDepthData()
            if color_img is not None and depth_data is not None:
                latest_color_img = color_img.copy()
                latest_depth_data = depth_data.copy()
                # --- 开放类别检测 ---
                if not current_tags or len(current_tags) == 0:
                    # 只推送原始相机图像，不检测不画框
                    image_bgr = color_img
                    _, jpeg = cv2.imencode(".jpg", image_bgr)
                    for ws in websockets:
                        await ws.send_bytes(jpeg.tobytes())
                else:
                    tags = current_tags
                    img_path = "/tmp/tmp.jpg"
                    cv2.imwrite(img_path, color_img)
                    obj_labels, obj_locs = vl_ali(tags, img_path)
                    obj_confs = [0.99] * len(obj_labels)
                    # 构造 output 对象
                    class Output:
                        pass
                    output = Output()
                    output.labels = [tags.index(l) for l in obj_labels] if obj_labels else []
                    output.boxes = [l[:4] for l in obj_locs] if obj_locs else []
                    output.scores = obj_confs if obj_confs else []
                    # 画框：所有检测到的目标都是橙色
                    colors = [ORANGE] * len(tags)
                    image_with_boxes = draw_owl_output(PIL.Image.fromarray(cv2.cvtColor(color_img, cv2.COLOR_BGR2RGB)), output, text=tags, draw_text=True, colors=colors)
                    image_with_boxes_bgr = cv2.cvtColor(np.array(image_with_boxes), cv2.COLOR_RGB2BGR)
                    _, jpeg = cv2.imencode(".jpg", image_with_boxes_bgr)
                    for ws in websockets:
                        await ws.send_bytes(jpeg.tobytes())
            await asyncio.sleep(0.03)  # 30fps

    # aiohttp应用的检测循环上下文管理
    async def run_detection_loop(app):
        task = asyncio.create_task(detection_loop(app))
        yield
        task.cancel()
        await task

    # aiohttp Web服务启动配置
    logging.basicConfig(level=logging.INFO)
    app = web.Application()
    app['websockets'] = websockets
    app.router.add_get("/", handle_index_get)
    app.router.add_route("GET", "/ws", websocket_handler)
    app.on_shutdown.append(on_shutdown)
    app.cleanup_ctx.append(run_detection_loop)

    # 新增：主程序请求检测的HTTP接口
    async def detect_handler(request):
        global latest_color_img, latest_depth_data, current_tags, current_conf, current_iou
        if latest_color_img is None or latest_depth_data is None:
            return web.json_response({'error': 'No frame available'}, status=503)
        data = await request.json()
        # 更新全局检测参数
        current_tags = data.get('tags', [])
        current_conf = float(data.get('conf', 0.2))
        current_iou = float(data.get('iou', 0.8))
        timeout = 10  # 最多等待10秒
        interval = 0.2
        waited = 0
        while True:
            img_path = "/tmp/tmp.jpg"
            cv2.imwrite(img_path, latest_color_img)
            # obj_labels, obj_locs = vl_ali(COCO80, img_path)
            # 只检测传入的目标tags，不使用COCO80
            obj_labels, obj_locs = vl_ali(current_tags, img_path)
            obj_confs = [0.99] * len(obj_labels)
            # 只在检测到有效目标时返回
            if obj_labels and len(obj_labels) > 0:
                # 构造 output 对象
                class Output:
                    pass
                output = Output()
                output.labels = [current_tags.index(l) for l in obj_labels] if obj_labels else []
                output.boxes = [l[:4] for l in obj_locs] if obj_locs else []
                output.scores = obj_confs if obj_confs else []
                # 画框：所有检测到的目标都是橙色
                colors = [ORANGE] * len(current_tags)
                image_with_boxes = draw_owl_output(PIL.Image.fromarray(cv2.cvtColor(latest_color_img, cv2.COLOR_BGR2RGB)), output, text=current_tags, draw_text=True, colors=colors)
                image_with_boxes_bgr = cv2.cvtColor(np.array(image_with_boxes), cv2.COLOR_RGB2BGR)
                _, jpeg = cv2.imencode(".jpg", image_with_boxes_bgr)
                for ws in websockets:
                    await ws.send_bytes(jpeg.tobytes())
                result = {
                    'labels': obj_labels,
                    'locs': obj_locs,
                    'confs': obj_confs,
                    'depth_data': latest_depth_data.tolist()
                }
                return web.json_response(result)
            await asyncio.sleep(interval)
            waited += interval
            if waited >= timeout:
                # 超时返回空结果
                return web.json_response({'labels': [], 'locs': [], 'confs': [], 'depth_data': latest_depth_data.tolist(), 'error': 'timeout'})

    app.router.add_post("/detect", detect_handler)

    web.run_app(app, host=args.host, port=args.port)
