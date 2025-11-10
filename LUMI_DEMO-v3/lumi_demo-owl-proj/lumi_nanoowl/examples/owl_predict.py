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

# 本脚本用于演示如何使用 OwlPredictor 对输入图片进行多目标检测，并将检测结果可视化保存。
# 支持自定义模型、推理引擎、检测阈值、文本提示等参数。

import argparse
import PIL.Image
import time
import torch
from nanoowl.owl_predictor import (
    OwlPredictor
)
from nanoowl.owl_drawing import (
    draw_owl_output
)


if __name__ == "__main__":

    # 解析命令行参数
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", type=str, default="../assets/6.jpg", help="输入图片路径") # ../assets/owl_glove_small.jpg
    parser.add_argument("--prompt", type=str, default="['screwdriver', 'wrench', 'pliers', 'hammer', 'tape measure', 'electric drill', 'Glue gun', 'Wire', 'Metal ring', 'Metal clamp', 'double-sided tape']", help="检测目标的文本提示，逗号分隔")
    parser.add_argument("--threshold", type=str, default="0.2,0.2,0.2,0.2,0.2,0.2,0.2,0.2,0.2,0.2,0.2", help="每个目标的置信度阈值，逗号分隔")
    parser.add_argument("--output", type=str, default="../owl_predict_out/owl_predict_out.jpg", help="输出图片路径")
    parser.add_argument("--model", type=str, default="google/owlvit-base-patch32", help="OwlViT模型名或本地路径")
    parser.add_argument("--image_encoder_engine", type=str, default="../data/owl_image_encoder_patch32.engine", help="TensorRT引擎文件路径")
    parser.add_argument("--profile", action="store_true", help="是否进行推理性能测试")
    parser.add_argument("--num_profiling_runs", type=int, default=5, help="性能测试时的推理次数")
    args = parser.parse_args()

    # 处理文本提示，转为字符串列表
    prompt = args.prompt.strip("][()")
    text = prompt.split(',')
    print(text)

    # 处理阈值参数，转为float或float列表
    thresholds = args.threshold.strip("][()")
    thresholds = thresholds.split(',')
    if len(thresholds) == 1:
        thresholds = float(thresholds[0])
    else:
        thresholds = [float(x) for x in thresholds]
    print(thresholds)
    
    # # 初始化OwlPredictor，加载模型和推理引擎
    # predictor = OwlPredictor(
    #     args.model,
    #     image_encoder_engine=args.image_encoder_engine
    # )

    predictor = OwlPredictor(
            image_encoder_engine=args.image_encoder_engine,
            model_path=args.model # 新增
    )



    # 加载输入图片
    image = PIL.Image.open(args.image)
    print('----image loaded---:')   # 输出图片
    
    # 编码文本提示
    text_encodings = predictor.encode_text(text)

    # 执行一次推理，获得检测结果
    output = predictor.predict(
        image=image, 
        text=text, 
        text_encodings=text_encodings,
        threshold=thresholds,
        pad_square=False
    )
    print('----output---:',output)   # 输出检测结果
    '''
    ----output---: OwlDecodeOutput(labels=tensor([0, 1], device='cuda:0'), scores=tensor([0.3269, 0.1018], device='cuda:0', grad_fn=<IndexBackward0>), boxes=tensor([[275.1943,  82.1108, 463.6406, 399.5898],
        [235.1426, 343.7935, 503.5078, 497.2944]], device='cuda:0'), input_indices=tensor([0, 0], device='cuda:0'))
    '''

    # 如果指定profile参数，则进行多次推理并统计FPS
    if args.profile:
        print('----profile---:',args.profile)   # 输出profile
        torch.cuda.current_stream().synchronize()
        t0 = time.perf_counter_ns()
        for i in range(args.num_profiling_runs):
            output = predictor.predict(
                image=image, 
                text=text, 
                text_encodings=text_encodings,
                threshold=thresholds,
                pad_square=False
            )
        torch.cuda.current_stream().synchronize()
        t1 = time.perf_counter_ns()
        dt = (t1 - t0) / 1e9
        print(f"PROFILING FPS: {args.num_profiling_runs/dt}")

    # 可视化检测结果并保存到输出图片
    print("--draw_owl_output---")
    image = draw_owl_output(image, output, text=text, draw_text=True)

    image.save(args.output)