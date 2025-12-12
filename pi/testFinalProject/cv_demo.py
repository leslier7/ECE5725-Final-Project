import cv2
import numpy as np

def main():
    # 1. 设置摄像头
    # 如果你的 Mac 仍然调用 iPhone，请尝试把 0 改成 1
    cap = cv2.VideoCapture(1) 

    if not cap.isOpened():
        print("无法打开摄像头，请尝试修改 VideoCapture 的数字 (0 或 1)")
        return

    print("绿色追踪已启动！请在摄像头前挥动绿色物体 (如绿色瓶盖、荧光笔)...")
    print("按 'q' 键退出。")

    # 2. 定义【绿色】的 HSV 范围
    # H (Hue): 色相，绿色通常在 40 到 80 之间 (OpenCV标准)
    # S (Saturation): 饱和度，设为 40 过滤掉发白的颜色
    # V (Value): 亮度，设为 40 过滤掉太黑的颜色
    lower_green = np.array([40, 40, 40])
    upper_green = np.array([80, 255, 255])

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # 镜像翻转 (像照镜子一样)
        frame = cv2.flip(frame, 1)

        # 3. 预处理
        # 高斯模糊 (平滑图像，减少噪点)
        blurred = cv2.GaussianBlur(frame, (11, 11), 0)
        # 转为 HSV 格式
        hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

        # 4. 创建遮罩 (Mask)
        # 只有在 lower_green 和 upper_green 之间的像素会变成白色
        mask = cv2.inRange(hsv, lower_green, upper_green)

        # 5. 去除噪点 (腐蚀与膨胀)
        # 这一步可以去掉背景中细小的绿色噪点
        mask = cv2.erode(mask, None, iterations=2)
        mask = cv2.dilate(mask, None, iterations=2)

        # 6. 寻找轮廓
        contours, _ = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        center = None

        # 7. 如果找到了绿色物体
        if len(contours) > 0:
            # 找到面积最大的那个轮廓 (假设最大的就是你的手/物体)
            c = max(contours, key=cv2.contourArea)
            
            # 计算最小外接圆
            ((x, y), radius) = cv2.minEnclosingCircle(c)
            
            # 计算力矩以找到中心点
            M = cv2.moments(c)
            if M["m00"] > 0:
                center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))

            # 只有当物体足够大 (半径 > 10) 时才显示，避免误判
            if radius > 10:
                # 画出黄色的圆圈
                cv2.circle(frame, (int(x), int(y)), int(radius), (0, 255, 255), 2)
                # 画出红色的中心点
                cv2.circle(frame, center, 5, (0, 0, 255), -1)
                
                # 打印坐标 (归一化坐标，方便以后给 IMU 用)
                height, width, _ = frame.shape
                norm_x = x / width
                norm_y = y / height
                cv2.putText(frame, f"Pos: {norm_x:.2f}, {norm_y:.2f}", (10, 50), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # 显示画面
        cv2.imshow("Green Tracker", frame)
        # 如果你想看程序到底“看”到了什么，取消下面这行的注释：
        cv2.imshow("Mask (Debug)", mask)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()