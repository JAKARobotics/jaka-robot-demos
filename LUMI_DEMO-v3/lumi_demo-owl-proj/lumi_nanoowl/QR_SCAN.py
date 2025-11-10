# https://www.jyshare.com/front-end/3454/

import cv2
import pyzbar.pyzbar as pyzbar
import numpy as np
# from orbbecCamera import Camera
from multi_camera_manager import Camera
import time
import os


def enhance_image_for_qr(image):
    """
    增强图像以提高二维码识别率
    :param image: 输入图像
    :return: 增强后的图像列表（多种处理方式）
    """
    enhanced_images = []

    # 1. 原始灰度图
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    enhanced_images.append(("original", gray))

    # 2. 高斯模糊去噪 + 锐化
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
    sharpened = cv2.filter2D(blurred, -1, kernel)
    enhanced_images.append(("sharpened", sharpened))

    # 3. 直方图均衡化
    equalized = cv2.equalizeHist(gray)
    enhanced_images.append(("equalized", equalized))

    # 4. 自适应阈值二值化
    adaptive_thresh = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )
    enhanced_images.append(("adaptive_thresh", adaptive_thresh))

    # 5. OTSU阈值二值化
    _, otsu_thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    enhanced_images.append(("otsu_thresh", otsu_thresh))

    # 6. 形态学操作（开运算）
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    morph = cv2.morphologyEx(gray, cv2.MORPH_OPEN, kernel)
    enhanced_images.append(("morphology", morph))

    return enhanced_images


def get_qr_text_enhanced(image_path, save_debug=False):
    """
    增强版二维码检测（兼容单个和多个）
    :param image_path: 图像路径
    :param save_debug: 是否保存调试图像
    :return: 二维码内容列表
    """
    image = cv2.imread(image_path)
    if image is None:
        print(f"无法读取图像: {image_path}")
        return []

    # 获取多种增强图像
    enhanced_images = enhance_image_for_qr(image)

    all_qr_texts = set()  # 使用集合避免重复
    debug_info = []

    for method_name, enhanced_img in enhanced_images:
        try:
            # 使用pyzbar库检测二维码
            barcodes = pyzbar.decode(enhanced_img)

            if barcodes:
                method_qr_texts = []
                for barcode in barcodes:
                    try:
                        barcodeData = barcode.data.decode("utf-8")
                        method_qr_texts.append(barcodeData)
                        all_qr_texts.add(barcodeData)
                    except UnicodeDecodeError:
                        # 尝试其他编码
                        try:
                            barcodeData = barcode.data.decode("gbk")
                            method_qr_texts.append(barcodeData)
                            all_qr_texts.add(barcodeData)
                        except:
                            print(f"无法解码二维码数据: {barcode.data}")

                debug_info.append(f"{method_name}: 检测到 {len(method_qr_texts)} 个二维码")

                # 保存调试图像
                if save_debug and method_qr_texts:
                    debug_dir = os.path.join(os.path.dirname(image_path), "debug")
                    os.makedirs(debug_dir, exist_ok=True)
                    debug_path = os.path.join(debug_dir, f"debug_{method_name}_{os.path.basename(image_path)}")
                    cv2.imwrite(debug_path, enhanced_img)
            else:
                debug_info.append(f"{method_name}: 未检测到二维码")

        except Exception as e:
            debug_info.append(f"{method_name}: 处理出错 - {e}")

    result_list = list(all_qr_texts)

    if result_list:
        print(f"总共检测到 {len(result_list)} 个唯一二维码: {result_list}")
        if save_debug:
            print("调试信息:")
            for info in debug_info:
                print(f"  {info}")

    return result_list


def get_qr_text(image_path):
    """
    检测图像中的二维码（兼容单个和多个）- 保持向后兼容
    :param image_path: 图像路径
    :return: 二维码内容列表
    """
    # 首先尝试增强版检测
    enhanced_result = get_qr_text_enhanced(image_path)
    if enhanced_result:
        return enhanced_result

    # 如果增强版没有结果，回退到原始方法
    image = cv2.imread(image_path)
    if image is None:
        return []

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # 使用pyzbar库检测二维码
    barcodes = pyzbar.decode(gray)
    qr_texts = []
    for barcode in barcodes:
        try:
            barcodeData = barcode.data.decode("utf-8")
            qr_texts.append(barcodeData)
        except UnicodeDecodeError:
            try:
                barcodeData = barcode.data.decode("gbk")
                qr_texts.append(barcodeData)
            except:
                print(f"无法解码二维码数据: {barcode.data}")
    return qr_texts



def get_qr_text_from_camera_enhanced(camera_serial_number=None, save_dir="./qr_snapshots", timeout=30.0,
                                   max_attempts_per_detection=3, save_debug=False):
    """
    增强版相机二维码检测，提高多二维码和低分辨率场景的识别率
    :param camera_serial_number: 可选，指定相机序列号
    :param save_dir: 图片保存目录
    :param timeout: 超时时间（秒）
    :param max_attempts_per_detection: 每次检测的最大尝试次数
    :param save_debug: 是否保存调试图像
    :return: 识别到的二维码内容列表
    """
    os.makedirs(save_dir, exist_ok=True)
    # 只要求color，不要求depth
    cam = Camera(serial_number=camera_serial_number, require_depth=False) if camera_serial_number else Camera(require_depth=False)
    print(f"开始增强版二维码检测...")

    start_time = time.time()
    attempt = 0
    all_detected_qrs = set()  # 累积所有检测到的二维码

    while time.time() - start_time < timeout:
        # 连续采集多帧进行检测
        frame_results = set()

        for frame_idx in range(max_attempts_per_detection):
            try:
                color_img = cam.getColorImageData()
                if color_img is None:
                    print(f"获取图像失败，跳过帧 {frame_idx}")
                    continue

                timestamp = time.strftime("%Y%m%d_%H%M%S")
                img_path = os.path.join(save_dir, f"qr_{timestamp}_{attempt}_{frame_idx}.jpg")
                cv2.imwrite(img_path, color_img)

                # 使用增强检测方法
                enhanced_images = enhance_image_for_qr(color_img)

                for method_name, enhanced_img in enhanced_images:
                    try:
                        barcodes = pyzbar.decode(enhanced_img)

                        if barcodes:
                            for barcode in barcodes:
                                try:
                                    barcodeData = barcode.data.decode("utf-8")
                                    frame_results.add(barcodeData)
                                    all_detected_qrs.add(barcodeData)
                                except UnicodeDecodeError:
                                    try:
                                        barcodeData = barcode.data.decode("gbk")
                                        frame_results.add(barcodeData)
                                        all_detected_qrs.add(barcodeData)
                                    except:
                                        print(f"无法解码二维码数据: {barcode.data}")

                            # 保存成功检测的调试图像
                            if save_debug and frame_results:
                                debug_dir = os.path.join(save_dir, "debug")
                                os.makedirs(debug_dir, exist_ok=True)
                                debug_path = os.path.join(debug_dir, f"success_{method_name}_{timestamp}_{attempt}_{frame_idx}.jpg")
                                cv2.imwrite(debug_path, enhanced_img)

                    except Exception as e:
                        print(f"处理方法 {method_name} 时出错: {e}")

                # 如果这一帧检测到了二维码，记录信息
                if frame_results:
                    print(f"帧 {frame_idx} 检测到二维码: {list(frame_results)}")

                time.sleep(0.1)  # 短暂延迟，让相机稳定

            except Exception as e:
                print(f"处理帧 {frame_idx} 时出错: {e}")
                continue

        # 检查是否有新的检测结果
        if all_detected_qrs:
            result_list = list(all_detected_qrs)
            print(f"当前累积检测到 {len(result_list)} 个唯一二维码: {result_list}")

            # 如果检测到多个二维码，给更多时间确保完整性
            if len(result_list) > 1:
                print("检测到多个二维码，继续检测以确保完整性...")
                # 继续检测一段时间，看是否还有更多二维码
                if attempt < 3:  # 至少尝试3轮
                    attempt += 1
                    time.sleep(1.0)
                    continue

            # 单个二维码或已经检测足够轮次，返回结果
            cam.close()
            print(f"最终检测到 {len(result_list)} 个二维码: {result_list}")
            return result_list

        print(f"第 {attempt + 1} 轮未识别到二维码，继续检测...")
        attempt += 1
        time.sleep(0.5)

    cam.close()
    if all_detected_qrs:
        result_list = list(all_detected_qrs)
        print(f"超时，但检测到 {len(result_list)} 个二维码: {result_list}")
        return result_list
    else:
        print(f"超时未检测到二维码")
        return []


def get_qr_text_from_camera(camera_serial_number=None, save_dir="./qr_snapshots", timeout=30.0):
    """
    用Orbbec相机循环采集图片并识别二维码，直到扫码成功。
    每次拍照都保存图片到save_dir，文件名带时间戳。
    兼容单个和多个二维码检测，统一返回列表格式。
    :param camera_serial_number: 可选，指定相机序列号
    :param save_dir: 图片保存目录
    :param timeout: 超时时间（秒）
    :return: 识别到的二维码内容列表
    """
    # 首先尝试增强版检测
    try:
        result = get_qr_text_from_camera_enhanced(
            camera_serial_number=camera_serial_number,
            save_dir=save_dir,
            timeout=timeout,
            max_attempts_per_detection=2,  # 每次检测2帧
            save_debug=False
        )
        if result:
            return result
    except Exception as e:
        print(f"增强版检测失败，回退到原始方法: {e}")

    # 回退到原始方法
    os.makedirs(save_dir, exist_ok=True)
    # 只要求color，不要求depth
    cam = Camera(serial_number=camera_serial_number, require_depth=False) if camera_serial_number else Camera(require_depth=False)
    print(f"开始原始二维码检测...")

    start_time = time.time()
    attempt = 0

    while time.time() - start_time < timeout:
        try:
            color_img = cam.getColorImageData()
            if color_img is None:
                continue

            timestamp = time.strftime("%Y%m%d_%H%M%S")
            img_path = os.path.join(save_dir, f"qr_{timestamp}_{attempt}.jpg")
            cv2.imwrite(img_path, color_img)

            gray = cv2.cvtColor(color_img, cv2.COLOR_BGR2GRAY)
            barcodes = pyzbar.decode(gray)

            if barcodes:
                qr_texts = []
                for barcode in barcodes:
                    try:
                        barcodeData = barcode.data.decode("utf-8")
                        qr_texts.append(barcodeData)
                    except UnicodeDecodeError:
                        try:
                            barcodeData = barcode.data.decode("gbk")
                            qr_texts.append(barcodeData)
                        except:
                            print(f"无法解码二维码数据: {barcode.data}")

                cam.close()
                print(f"检测到 {len(qr_texts)} 个二维码: {qr_texts}")
                print(f"图片路径: {img_path}")
                return qr_texts

            print(f"未识别到二维码，已保存图片: {img_path}，继续检测...")
            time.sleep(0.5)
            attempt += 1

        except Exception as e:
            print(f"检测过程中出错: {e}")
            attempt += 1
            time.sleep(0.5)

    cam.close()
    print(f"超时未检测到二维码")
    return []



if __name__ == "__main__":
    # image_path='/opt/nanoowl/assets/qr-西瓜霜润喉片.png'
    # # image_path='/opt/nanoowl/assets/qr-云南白药创可贴.png'
    # print(get_qr_text(image_path))

    # 测试二维码检测（兼容单个和多个）
    qr_texts = get_qr_text_from_camera(camera_serial_number='AY8V74300CZ') # AY8V74300F4
    print(f"识别到二维码内容: {qr_texts}")

    # qr_text = get_qr_text_from_camera(camera_serial_number='AY8V74300F4') #  # AY8V74300F4  hand #  AY8V74300CZ head
    # qr_text = get_qr_text_from_camera(camera_serial_number='AY8V74300CZ')
    # print(f"识别到二维码内容: {qr_text}")