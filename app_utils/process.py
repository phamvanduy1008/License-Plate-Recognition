import cv2
import torch
import numpy as np
import time
from PIL import Image
from function.utils_rotate import deskew
from function.helper import read_plate
import os

# Ensure history and video directories exist
HISTORY_DIR = "D:/Python/License-Plate-Recognition/history_image"
VIDEO_DIR = "D:/Python/License-Plate-Recognition/history_video"
for directory in [HISTORY_DIR, VIDEO_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

# Load models
yolo_LP_detect = torch.hub.load('yolov5', 'custom', path='D:/Python/License-Plate-Recognition/model/LP_detection_nano.pt', force_reload=True, source='local')
yolo_license_plate = torch.hub.load('yolov5', 'custom', path='D:/Python/License-Plate-Recognition/model/LP_ocr_nano.pt', force_reload=True, source='local')
yolo_license_plate.conf = 0.60

def process_frame(frame):
    """Xử lý một frame (ảnh hoặc frame video) để nhận diện biển số."""
    list_read_plates = set()
    plates = yolo_LP_detect(frame, size=640)
    list_plates = plates.pandas().xyxy[0].values.tolist()
    captured_frame = None

    if len(list_plates) == 0:
        lp = read_plate(yolo_license_plate, frame)
        if lp != "unknown":
            cv2.putText(frame, lp, (7, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 2)
            list_read_plates.add(lp)
            captured_frame = frame.copy()
    else:
        for plate in list_plates:
            flag = 0
            x = int(plate[0])  # xmin
            y = int(plate[1])  # ymin
            w = int(plate[2] - plate[0])  # xmax - xmin
            h = int(plate[3] - plate[1])  # ymax - ymin
            crop_img = frame[y:y+h, x:x+w]
            cv2.rectangle(frame, (int(plate[0]), int(plate[1])), (int(plate[2]), int(plate[3])), color=(0, 0, 225), thickness=2)
            cv2.imwrite("crop.jpg", crop_img)
            lp = ""
            for cc in range(0, 2):
                for ct in range(0, 2):
                    lp = read_plate(yolo_license_plate, deskew(crop_img, cc, ct))
                    if lp != "unknown":
                        list_read_plates.add(lp)
                        cv2.putText(frame, lp, (int(plate[0]), int(plate[1]-10)), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 2)
                        flag = 1
                        captured_frame = frame.copy()
                        break
                if flag == 1:
                    break
    return frame, list_read_plates, captured_frame

def process_image(image_path):
    """Xử lý ảnh tĩnh."""
    img = cv2.imread(image_path)
    if img is None:
        return None, "Không thể đọc ảnh", None
    processed_frame, plates, captured_frame = process_frame(img)
    return processed_frame, plates, captured_frame

def process_video(video_path):
    """Xử lý video."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return None, "Không thể mở video", None
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        processed_frame, plates, _ = process_frame(frame)
        cv2.imshow('Video', processed_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()
    return None, plates, None

def process_realtime(cam_source="http://192.168.1.18:4747/video"):
    """Xử lý real-time từ webcam hoặc DroidCam."""
    cap = cv2.VideoCapture(cam_source)
    if not cap.isOpened():
        return None, "Không thể mở luồng webcam", None

    # Initialize video writer
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    video_path = os.path.join(VIDEO_DIR, f"realtime_{timestamp}.mp4")
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    fps = 30
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    out = cv2.VideoWriter(video_path, fourcc, fps, (frame_width, frame_height))

    prev_frame_time = 0
    cv2.namedWindow('Real-time', cv2.WINDOW_NORMAL)
    captured_frame = None
    last_plate = None
    current_plate = None
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            processed_frame, plates, new_captured_frame = process_frame(frame)
            out.write(processed_frame)  # Write frame to video

            if new_captured_frame is not None and plates:
                current_plate = next(iter(plates))
                if current_plate != last_plate:
                    captured_frame = new_captured_frame
                    last_plate = current_plate
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    save_path = os.path.join(HISTORY_DIR, f"plate_{timestamp}.jpg")
                    cv2.imwrite(save_path, captured_frame)
                    yield captured_frame, current_plate
            
            new_frame_time = time.time()
            fps = 1 / (new_frame_time - prev_frame_time)
            prev_frame_time = new_frame_time
            cv2.putText(processed_frame, f"FPS: {int(fps)}", (7, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (100, 255, 0), 3)
            
            cv2.imshow('Real-time', processed_frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or cv2.getWindowProperty('Real-time', cv2.WND_PROP_VISIBLE) < 1:
                break
    finally:
        out.release()  # Save the video
        cap.release()
        cv2.destroyAllWindows()
    
    yield captured_frame, current_plate