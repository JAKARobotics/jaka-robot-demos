from nanoowl.owl_predictor import OwlPredictor
from PIL import Image
import numpy as np
import time

# 初始化全局 predictor（避免每次都加载模型）
# 1. 测量模型加载时间

'''
  class OwlPredictor:
      def __init__(self, image_encoder_engine=None, model_path=None):
          # 如果 model_path 是 huggingface 名字，则会联网下载权重并初始化
          # 如果 image_encoder_engine 是 engine 路径，则直接加载本地 engine，速度极快
          如果先给模型名字，会先从huggingface下载模型
'''

t0 = time.time()
# 删除全局的 owl_predictor = OwlPredictor(...)
# 只保留 det_owl_image，要求传入 predictor

def det_owl_image(predictor, image, conf, tags, iou=0.3):
    if isinstance(conf, float):
        thresholds = [conf] * len(tags)
    else:
        thresholds = conf
    text_encodings = predictor.owl_predictor.encode_text(tags)
    output = predictor.owl_predictor.predict(
        image=image,
        text=tags,
        text_encodings=text_encodings,
        threshold=thresholds,
        pad_square=False
    )
    obj_labels = []
    obj_locs = []
    obj_confs = []
    for i, label_idx in enumerate(output.labels):
        label = tags[int(label_idx)]
        box = output.boxes[i]
        conf_val = output.scores[i]
        obj_labels.append(label)
        obj_locs.append([int(box[0]), int(box[1]), int(box[2]), int(box[3]), 0.0])
        obj_confs.append(float(conf_val))
    return obj_labels, obj_locs, obj_confs

if __name__ == "__main__":
    '''
    python3 infer_owl.py --image './assets/owl_glove_small.jpg' --tags 'glove, owl' 
    '''
    import argparse
    parser = argparse.ArgumentParser(description='测试OWL目标检测')
    parser.add_argument('--image', type=str, required=True, help='输入图片路径')
    parser.add_argument('--tags', type=str, required=True, help='检测类别，逗号分隔')
    parser.add_argument('--conf', type=float, default=0.5, help='置信度阈值')
    parser.add_argument('--save_path', type=str, default='./owl_det_results', help='检测结果图片保存目录（可选）')
    args = parser.parse_args()

    tags = [t.strip() for t in args.tags.split(',') if t.strip()]
    conf = args.conf
    img_path = args.image
    save_path = args.save_path

    # 2. 测量单张图片推理时间
    t1 = time.time()
    # 创建 OwlPredictor 实例
    owl_predictor = OwlPredictor(
        image_encoder_engine="./data/owl_image_encoder_patch32.engine",
        model_path="/opt/nanoowl/owlvit-base-pacth32"
    )
    # 调用 det_owl_image，传入 predictor 实例
    obj_labels, obj_locs, obj_confs = det_owl_image(owl_predictor, Image.open(img_path), conf, tags, save_path=save_path)
    print("单张图片推理耗时: %.3f 秒" % (time.time() - t1))

    print('obj_labels:', obj_labels)
    print('obj_locs:', obj_locs)
    print('obj_confs:', obj_confs)
    print("检测结果:")
    for i, res in enumerate(obj_locs):
        print(f"目标 {i+1}: 类别={obj_labels[i]}, 置信度={obj_confs[i]:.2f}, 框=({res[0]}, {res[1]}, {res[2]}, {res[3]}), 角度={res[4]:.2f}")