from cgi import print_directory
from ultralytics import YOLO
import numpy as np
import cv2
import math
import os
 
# 加载预训练模型
model = YOLO(r"/home/jaka/AI_CODES/lumi_demo/doll_lumi/doll_lumi6/weights/best.pt")

def det_yolo(img_path, conf, tags, iou=0.8, device=None, save_path=None):
    """
    输入:
        img_path: 图片路径
        conf: 置信度阈值
        tags: 检测类别（list[str]）
        iou: iou阈值
        save_path: 检测结果图片保存目录（可选）
    输出:
        obj_labels: list[str]
        obj_locs: list[list[int, int, int, int, float]]  # [x1, y1, x2, y2, angle]
        obj_confs: list[float]
        顺序严格一一对应，按conf递减
    """
    results = model.predict(
        source=img_path,
        conf=conf,
        iou=iou,
        imgsz=1280,
        half=False,
        device=device,
        max_det=1000,
        vid_stride=1,
        stream_buffer=False,
        visualize=False,
        augment=False,
        agnostic_nms=False,
        classes=None,
        retina_masks=True,
        embed=None,
        show=False,
        save=False,
        save_frames=False,
        save_txt=False,
        save_conf=False,
        save_crop=False,
        show_labels=False,
        show_conf=False,
        show_boxes=False,
        line_width=1
    )
    dets = []
    # For drawing
    img_for_draw = cv2.imread(img_path)
    draw_enabled = img_for_draw is not None
    for result in results:
        obb_boxes = getattr(result, 'obb', None)
        if obb_boxes is not None and hasattr(obb_boxes, 'xyxyxyxy'):
            xyxyxyxys = obb_boxes.xyxyxyxy
            for i, xyxyxyxy in enumerate(xyxyxyxys):
                points = xyxyxyxy.cpu().numpy().reshape(4, 2)
                rect = cv2.minAreaRect(points.astype(np.float32))
                angle = rect[2]
                if angle < -45:
                    angle = 90 + angle
                box = cv2.boxPoints(rect).astype(int)
                x1, y1 = box[:,0].min(), box[:,1].min()
                x2, y2 = box[:,0].max(), box[:,1].max()
                cls = int(obb_boxes.cls[i].item())
                conf_val = obb_boxes.conf[i].item()
                label = result.names[cls]
                if label in tags:
                    dets.append({
                        'label': label,
                        'loc': [x1, y1, x2, y2],
                        'angle': float(angle),
                        'conf': conf_val
                    })
                    # Draw rotated box
                    if draw_enabled:
                        cv2.drawContours(img_for_draw, [box], 0, (0, 255, 0), 2)
                        cv2.putText(img_for_draw, f"{label} {conf_val:.2f}", (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)
        else:
            boxes = getattr(result, 'boxes', None)
            if boxes is None or len(boxes) == 0:
                continue
            for i in range(len(boxes)):
                cls = int(boxes.cls[i].item())
                conf_val = boxes.conf[i].item()
                label = result.names[cls]
                if label in tags:
                    xyxy = boxes.xyxy[i].cpu().numpy().astype(int).tolist()
                    angle = 0.0
                    dets.append({
                        'label': label,
                        'loc': xyxy,
                        'angle': angle,
                        'conf': conf_val
                    })
                    # Draw rectangle
                    if draw_enabled:
                        x1, y1, x2, y2 = xyxy
                        cv2.rectangle(img_for_draw, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.putText(img_for_draw, f"{label} {conf_val:.2f}", (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)
    # 按conf递减排序
    dets = sorted(dets, key=lambda x: -x['conf'])
    obj_labels = [d['label'] for d in dets]
    obj_locs = [d['loc'] + [d['angle']] for d in dets]
    obj_confs = [d['conf'] for d in dets]
    # 保存检测结果图片
    if save_path is not None and draw_enabled:
        if not os.path.exists(save_path):
            os.makedirs(save_path)
        # 用原图名保存
        base_name = os.path.basename(img_path)
        save_img_path = os.path.join(save_path, base_name)
        cv2.imwrite(save_img_path, img_for_draw)
    return obj_labels, obj_locs, obj_confs

# 进行推理
if __name__ == "__main__":
    # 测试图片路径
    img_path = "/home/jaka/AI_CODES/lumi_demo/images/project1/1.jpg"
    # 检测类别
    tags = ["doll"]
    conf = 0.42
    iou = 0.8
    # 调用封装函数
    obj_labels, obj_locs, obj_confs = det_yolo(img_path, conf, tags, iou)
    print('obj_labels: ', obj_labels)
    print('obj_locs: ', obj_locs)
    print('obj_confs: ', obj_confs)
    print("检测结果:")
    for i, res in enumerate(obj_locs):
        print(f"目标 {i+1}: 类别={obj_labels[i]}, 置信度={obj_confs[i]:.2f}, 旋转角度={res[-1]:.2f}度, 中心点=({res[0]}, {res[1]})")

    # 原有可视化代码（如需可视化）
    # 处理结果并计算旋转角度
    # for result in results:
    #     obb_boxes = result.obb  # 使用obb属性而不是boxes
    #     if obb_boxes is not None and len(obb_boxes) > 0:
    #         xyxyxyxys = obb_boxes.xyxyxyxy  # 或 boxes.xyxyxyxy.cpu().numpy()
    #         img_height, img_width = result.orig_shape
    #         img = cv2.imread(str(result.path))
    #         for i, xyxyxyxy in enumerate(xyxyxyxys):
    #             points = xyxyxyxy.cpu().numpy().reshape(4, 2)
    #             rect = cv2.minAreaRect(points.astype(np.float32))
    #             angle = rect[2]
    #             if angle < -45:
    #                 angle = 90 + angle
    #             center_x = int(rect[0][0])
    #             center_y = int(rect[0][1])
    #             cls = int(obb_boxes.cls[i].item())
    #             conf = obb_boxes.conf[i].item()
    #             print(f"目标 {i+1}: 类别={cls}, 置信度={conf:.2f}, 旋转角度={angle:.2f}度, 中心点=({center_x}, {center_y})")
    #             box = cv2.boxPoints(rect).astype(np.int0)
    #             cv2.drawContours(img, [box], 0, (0, 255, 0), 2)
    #             cv2.putText(img, f"angle: {angle:.1f}", (box[0][0], box[0][1]-10), 
    #                         cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
    #             cv2.circle(img, (center_x, center_y), 3, (255, 0, 0), -1)
    #             coord_text = f"center: ({center_x}, {center_y})"
    #             conf_text = f"conf: {conf:.2f}"
    #             cv2.putText(img, coord_text, (center_x + 5, center_y + 15), 
    #                         cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 0, 0), 1)
    #             cv2.putText(img, conf_text, (center_x + 5, center_y + 30), 
    #                         cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 0, 0), 1)
    #         output_path = "all_angles_result.jpg"
    #         cv2.imwrite(output_path, img)