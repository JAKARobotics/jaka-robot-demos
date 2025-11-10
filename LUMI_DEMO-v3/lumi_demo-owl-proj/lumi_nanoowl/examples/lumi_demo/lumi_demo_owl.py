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
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
# from orbbecCamera import Camera
from multi_camera_manager import Camera

# 自定义画框函数，支持自定义颜色
def draw_owl_output(image, output, text, draw_text=True, colors=None):
    import cv2
    import numpy as np
    is_pil = not isinstance(image, np.ndarray)
    if is_pil:
        image = np.asarray(image)
        if not image.flags.writeable:
            image = image.copy()
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.75
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
        if draw_text:
            offset_y = 12
            offset_x = 0
            label_text = text[label_index]
            cv2.putText(
                image,
                label_text,
                (box[0] + offset_x, box[1] + offset_y),
                font,
                font_scale,
                colors[label_index],
                2,# thickness
                cv2.LINE_AA
            )
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

# COCO80类别
COCO80 = [
    "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat", "traffic light",
    "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat", "dog", "horse", "sheep", "cow",
    "elephant", "bear", "zebra", "giraffe", "backpack", "umbrella", "handbag", "tie", "suitcase", "frisbee",
    "skis", "snowboard", "sports ball", "kite", "baseball bat", "baseball glove", "skateboard", "surfboard",
    "tennis racket", "bottle", "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana", "apple",
    "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair", "couch",
    "potted plant", "bed", "dining table", "toilet", "tv", "laptop", "mouse", "remote", "keyboard", "cell phone",
    "microwave", "oven", "toaster", "sink", "refrigerator", "book", "clock", "vase", "scissors", "teddy bear",
    "hair drier", "toothbrush", "screwdriver", "wrench", "pliers", "hammer", "tape measure", "electric drill", "Glue gun", "Wire", "Metal ring", "Metal clamp", "double-sided tape","medicine"
]

# 颜色定义
ORANGE = (255, 128, 0)
BLUE = (0, 128, 255)

if __name__ == "__main__":
    '''
    python3 tree_demo.py --camera 4 --resolution 640x400 \
    ../../data/owl_image_encoder_patch32.engine

    python3 lumi_demo_owl.py ../../data/owl_image_encoder_patch32.engine \
    --owl_model_path /opt/nanoowl/owlvit-base-pacth32 \
    --port 7860 \
    --host 0.0.0.0 \
    --camera 0 \
    --resolution 1280x800
  
    python3 examples/lumi_demo/lumi_demo_owl.py data/owl_image_encoder_patch32.engine --camera-sn AY8V74300CZ

    python3 lumi_demo_owl.py /opt/nanoowl/data/owl_image_encoder_patch32.engine --camera-sn AY8V74300CZ
    AY8V74300Y8  AY8V74300NK AY8V743013S
    '''


    # 解析命令行参数
    parser = argparse.ArgumentParser()
    parser.add_argument("image_encode_engine", type=str)
    parser.add_argument("--owl_model_path", type=str, default='/opt/nanoowl/owlvit-base-pacth32')  # 新增
    parser.add_argument("--image_quality", type=int, default=50)
    parser.add_argument("--port", type=int, default=7860) # 7860
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument("--camera-sn", type=str, default='AY8V74300F4', help="指定要使用的相机序列号")
    parser.add_argument("--resolution", type=str, default="1280x800", help="Camera resolution as WIDTHxHEIGHT")
    args = parser.parse_args()
    width, height = map(int, args.resolution.split("x"))

    CAMERA_DEVICE = args.camera
    IMAGE_QUALITY = args.image_quality
    CAMERA_SN = args.camera_sn

    # 初始化TreePredictor和OwlPredictor，加载模型和推理引擎
    t0 = time.time()
    predictor = TreePredictor(
        owl_predictor=OwlPredictor(
            image_encoder_engine=args.image_encode_engine,
            model_path=args.owl_model_path  # 新增
        )
    )
    print("--模型加载耗时：", time.time() - t0)

    prompt_data = None

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
                # 检测并画框推送
                # --- 开放类别检测 ---
                if not current_tags or len(current_tags) == 0:
                    tags = COCO80
                else:
                    tags = current_tags
                image_pil = Image.fromarray(cv2.cvtColor(color_img, cv2.COLOR_BGR2RGB))
                obj_labels, obj_locs, obj_confs = det_owl_image(predictor, image_pil, current_conf, tags, current_iou)
                # 构造 output 对象
                class Output:
                    pass
                output = Output()
                output.labels = [tags.index(l) for l in obj_labels] if obj_labels else []
                output.boxes = [l[:4] for l in obj_locs] if obj_locs else []
                output.scores = obj_confs if obj_confs else []
                # 画框：目标物橙色，其他蓝色
                colors = []
                if not current_tags or len(current_tags) == 0:
                    # 全部蓝色
                    colors = [BLUE for _ in tags]
                else:
                    # 目标物橙色，其余蓝色
                    for t in tags:
                        if t in current_tags:
                            colors.append(ORANGE)
                        else:
                            colors.append(BLUE)
                image_with_boxes = draw_owl_output(image_pil, output, text=tags, draw_text=True, colors=colors)
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
            image_pil = Image.fromarray(cv2.cvtColor(latest_color_img, cv2.COLOR_BGR2RGB))
            # 检测所有COCO80类别
            obj_labels, obj_locs, obj_confs = det_owl_image(predictor, image_pil, current_conf, COCO80, current_iou)
            # 只在检测到有效目标时返回
            if obj_labels and len(obj_labels) > 0:
                # 只返回目标物信息
                result_labels = []
                result_locs = []
                result_confs = []
                for l, loc, conf in zip(obj_labels, obj_locs, obj_confs):
                    if l in current_tags:
                        result_labels.append(l)
                        result_locs.append(loc)
                        result_confs.append(conf)
                # 构造 output 对象
                class Output:
                    pass
                output = Output()
                output.labels = [COCO80.index(l) for l in obj_labels] if obj_labels else []
                output.boxes = [l[:4] for l in obj_locs] if obj_locs else []
                output.scores = obj_confs if obj_confs else []
                # 画框：目标物橙色，其他蓝色
                colors = []
                for t in COCO80:
                    if t in current_tags:
                        colors.append(ORANGE)
                    else:
                        colors.append(BLUE)
                image_with_boxes = draw_owl_output(image_pil, output, text=COCO80, draw_text=True, colors=colors)
                image_with_boxes_bgr = cv2.cvtColor(np.array(image_with_boxes), cv2.COLOR_RGB2BGR)
                _, jpeg = cv2.imencode(".jpg", image_with_boxes_bgr)
                for ws in websockets:
                    await ws.send_bytes(jpeg.tobytes())
                result = {
                    'labels': result_labels,
                    'locs': result_locs,
                    'confs': result_confs,
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
