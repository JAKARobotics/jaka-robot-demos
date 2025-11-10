import cv2

def main():
    camera_id = 4  # 可根据需要修改
    cap = cv2.VideoCapture(camera_id)
    if not cap.isOpened():
        print(f"无法打开摄像头 {camera_id}")
        return
    print(f"摄像头 {camera_id} 打开成功，按 'q' 退出。")
    while True:
        ret, frame = cap.read()
        if not ret:
            print("无法读取摄像头画面")
            break
        cv2.imshow('Camera Test', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
