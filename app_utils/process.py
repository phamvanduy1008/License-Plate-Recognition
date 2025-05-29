import cv2
import torch
import numpy as np
import time
from PIL import Image
from function.utils_rotate import deskew
from function.helper import read_plate
import os
import datetime
import stat

class LicensePlateModel:
    def __init__(self):
        self.HISTORY_DIR = r"D:\hoc_may\License-Plate-Recognition\history_image"
        self.VIDEO_DIR = r"D:\hoc_may\License-Plate-Recognition\history_video"
        for directory in [self.HISTORY_DIR, self.VIDEO_DIR]:
            if not os.path.exists(directory):
                os.makedirs(directory)
        self.yolo_LP_detect = torch.hub.load('yolov5', 'custom', path='./model/LP_detection_nano.pt', force_reload=True, source='local')
        self.yolo_license_plate = torch.hub.load('yolov5', 'custom', path='./model/LP_ocr_nano.pt', force_reload=True, source='local')
        self.yolo_license_plate.conf = 0.60  # Đặt ngưỡng độ tin cậy cho mô hình nhận diện ký tự

    def process_frame(self, frame):
        """Xử lý một frame (ảnh hoặc frame video) để phát hiện và đọc biển số."""
        list_read_plates = set()  # Lưu danh sách biển số
        plates = self.yolo_LP_detect(frame, size=640)  
        list_plates = plates.pandas().xyxy[0].values.tolist()  # Chuyển kết quả thành danh sách
        captured_frame = None  # Lưu frame đã xử lý để hiển thị
        cropped_plate = None  # Lưu ảnh vùng biển số đã cắt

        # Nếu yolov5 không phát hiện được vùng biển số, thử nhận diện trực tiếp
        if len(list_plates) == 0:
            lp = read_plate(self.yolo_license_plate, frame)
            if lp != "unknown":
                cv2.putText(frame, lp, (7, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 2)
                list_read_plates.add(lp)
                captured_frame = frame.copy()
        else:
            # Xử lý từng vùng biển số được phát hiện
            for plate in list_plates:
                flag = 0
                #Khởi tạo tọa độ khung biển sốsố
                x = int(plate[0])  
                y = int(plate[1])  
                w = int(plate[2] - plate[0])  
                h = int(plate[3] - plate[1])  
                crop_img = frame[y:y+h, x:x+w]  
                cv2.rectangle(frame, (int(plate[0]), int(plate[1])), (int(plate[2]), int(plate[3])), color=(0, 0, 225), thickness=2)  # Vẽ khung đỏ quanh vùng biển số
                cv2.imwrite("crop.jpg", crop_img)  # Lưu tạm vùng cắt để xử lý
                lp = ""
                # Thử xoay ảnh để cải thiện kết quả nhận diện
                for cc in range(0, 2):
                    for ct in range(0, 2):
                        lp = read_plate(self.yolo_license_plate, deskew(crop_img, cc, ct))
                        if lp != "unknown":
                            list_read_plates.add(lp)
                            cv2.putText(frame, lp, (int(plate[0]), int(plate[1]-10)), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 2)  # Hiển thị biển số lên frame
                            flag = 1
                            captured_frame = frame.copy()
                            cropped_plate = crop_img  # Lưu vùng biển số đã cắt
                            break
                    if flag == 1:
                        break
        return frame, list_read_plates, captured_frame, cropped_plate

    def process_image(self, image_path):
        """Xử lý một ảnh tĩnh để nhận diện biển số."""
        img = cv2.imread(image_path)
        if img is None:
            return None, "Không thể đọc ảnh", None
        # Gọi hàm xử lý frame để nhận diện
        processed_frame, plates, captured_frame, cropped_plate = self.process_frame(img)
        # Nếu nhận diện thành công, lưu ảnh và thông tin vào lịch sử
        if captured_frame is not None and plates:
            plate = next(iter(plates))
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"{plate}_{timestamp}.jpg"
            output_path = os.path.join(self.HISTORY_DIR, output_filename)
            cv2.imwrite(output_path, captured_frame)
            os.chmod(output_path, stat.S_IWRITE | stat.S_IREAD)  # Đặt quyền ghi/đọc cho file
            current_time = datetime.datetime.now().strftime("%H:%M:%S %d/%m/%Y")
            existing_lines = []
            if os.path.exists("./plate_history.txt"):
                with open("./plate_history.txt", "r", encoding="utf-8") as f:
                    existing_lines = f.readlines()
            with open("./plate_history.txt", "w", encoding="utf-8") as f:
                f.write(f"{output_filename},{plate}; {current_time}\n")
                f.writelines(existing_lines)
        return processed_frame, plates, captured_frame

    def process_video(self, video_path, output_path):
        """Xử lý video, nhận diện biển số và lưu video đã xử lý."""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return None, "Không thể mở video", None
        
        # Lấy thông tin video (chiều rộng, chiều cao, FPS)
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))
        
        plates = set()  # Lưu danh sách biển số
        video_filename = os.path.basename(output_path)
        seen_plates = set()  # Theo dõi các biển số duy nhất trong video
        
        # Xử lý từng frame trong video
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            processed_frame, detected_plates, captured_frame, cropped_plate = self.process_frame(frame)
            plates.update(detected_plates)
            out.write(processed_frame)
            
            # Nếu phát hiện biển số mới, lưu ảnh vùng biển số và ghi lịch sử
            if captured_frame is not None and detected_plates and cropped_plate is not None:
                for plate in detected_plates:
                    if plate not in seen_plates:  # Chỉ xử lý các biển số chưa thấy
                        seen_plates.add(plate)
                        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                        cropped_filename = f"{plate}_video_{timestamp}.jpg"
                        cropped_path = os.path.join(self.HISTORY_DIR, cropped_filename)
                        cv2.imwrite(cropped_path, cropped_plate)
                        os.chmod(cropped_path, stat.S_IWRITE | stat.S_IREAD)
                        
                        current_time = datetime.datetime.now().strftime("%H:%M:%S %d/%m/%Y")
                        existing_lines = []
                        if os.path.exists("./plate_history.txt"):
                            with open("./plate_history.txt", "r", encoding="utf-8") as f:
                                existing_lines = f.readlines()
                        with open("./plate_history.txt", "w", encoding="utf-8") as f:
                            line = f"{cropped_filename},{plate}; {current_time};(from video {video_filename})"
                            f.write(line + "\n")
                            f.writelines(existing_lines)
            
            cv2.imshow('Video', processed_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cap.release()
        out.release()
        os.chmod(output_path, stat.S_IWRITE | stat.S_IREAD)
        cv2.destroyAllWindows()
        return None, plates, None

    def process_realtime(self, cam_source="http://192.168.1.18:4747/video"):
        """Xử lý thời gian thực từ webcam hoặc DroidCam."""
        cap = cv2.VideoCapture(cam_source)
        if not cap.isOpened():
            return None, "Không thể mở luồng webcam", None

        # Tạo video lưu trữ thời gian thực
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        video_path = os.path.join(self.VIDEO_DIR, f"realtime_{timestamp}.mp4")
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
                # Xử lý frame để nhận diện biển số
                processed_frame, plates, new_captured_frame, cropped_plate = self.process_frame(frame)
                out.write(processed_frame)

                # Nếu phát hiện biển số mới, lưu ảnh và thông tin
                if new_captured_frame is not None and plates:
                    current_plate = next(iter(plates))
                    if current_plate != last_plate:
                        captured_frame = new_captured_frame
                        last_plate = current_plate
                        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                        safe_plate = "".join(c if c.isalnum() else "_" for c in current_plate)
                        output_filename = f"{safe_plate}_realtime_{timestamp}.jpg"
                        output_path = os.path.join(self.HISTORY_DIR, output_filename)
                        if cv2.imwrite(output_path, captured_frame):
                            os.chmod(output_path, stat.S_IWRITE | stat.S_IREAD)
                            current_time = datetime.datetime.now().strftime("%H:%M:%S %d/%m/%Y")
                            existing_lines = []
                            if os.path.exists("./plate_history.txt"):
                                with open("./plate_history.txt", "r", encoding="utf-8") as f:
                                    existing_lines = f.readlines()
                            with open("./plate_history.txt", "w", encoding="utf-8") as f:
                                line = f"{output_filename},{current_plate}; {current_time};(from video realtime_{timestamp}.mp4)"
                                f.write(line + "\n")
                                f.writelines(existing_lines)
                        yield captured_frame, current_plate
                
                # Tính FPS để hiển thị
                new_frame_time = time.time()
                fps = 1 / (new_frame_time - prev_frame_time)
                prev_frame_time = new_frame_time
                cv2.putText(processed_frame, f"FPS: {int(fps)}", (7, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (100, 255, 0), 3)
                
                cv2.imshow('Real-time', processed_frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or cv2.getWindowProperty('Real-time', cv2.WND_PROP_VISIBLE) < 1:
                    break
        finally:
            out.release()
            os.chmod(video_path, stat.S_IWRITE | stat.S_IREAD)
            cap.release()
            cv2.destroyAllWindows()
        
        yield captured_frame, current_plate

    def get_file_lists(self, search_text):
        """Lấy danh sách ảnh và video để hiển thị, đảm bảo không trùng lặp biển số."""
        image_items = []
        video_items = []
        self.plate_to_file_map = {}  # Bản đồ ánh xạ biển số với tên file
        
        # Đọc lịch sử biển số và lọc các file không tồn tại
        plate_history = {}
        if os.path.exists("./plate_history.txt"):
            with open("./plate_history.txt", "r", encoding="utf-8") as f:
                lines = f.readlines()
                with open("./plate_history.txt", "w", encoding="utf-8") as f_out:
                    seen_plates = set()
                    for line in lines:
                        filename, plate_with_time = line.strip().split(",", 1)
                        plate = plate_with_time.split(";")[0].strip().replace(" (from video)", "")
                        file_path = os.path.join(self.HISTORY_DIR, filename)
                        if os.path.exists(file_path) and plate not in seen_plates:
                            plate_history[filename] = plate_with_time
                            seen_plates.add(plate)
                            self.plate_to_file_map[plate] = filename
                        if os.path.exists(file_path):
                            f_out.write(f"{filename},{plate_with_time}\n")
        
        # Sắp xếp ảnh theo thời gian (mới nhất trước)
        image_count = 0
        items_with_time = []
        for file in plate_history.keys():
            if search_text in file.lower():
                plate_with_time = plate_history.get(file, "Không xác định; 00:00:00 01/01/1970")
                plate = plate_with_time.split(";")[0].strip().replace(" (from video", "").split(" (")[0]
                time_str = plate_with_time.split(";")[1].strip() if ";" in plate_with_time else "00:00:00 01/01/1970"
                try:
                    time_obj = datetime.datetime.strptime(time_str, "%H:%M:%S %d/%m/%Y")
                except ValueError:
                    time_obj = datetime.datetime(1970, 1, 1, 0, 0, 0)
                items_with_time.append((file, plate, time_obj))
        
        items_with_time.sort(key=lambda x: x[2], reverse=True)
        
        seen_plates = set()
        for file, plate, _ in items_with_time:
            if plate != "Không xác định" and plate not in seen_plates:
                image_items.append((file, plate))
                image_count += 1
                seen_plates.add(plate)
        
        # Lấy danh sách video
        video_count = 0
        for file in sorted(os.listdir(self.VIDEO_DIR), reverse=True):
            if file.endswith('.mp4') and search_text in file.lower():
                date_str = self.get_date_from_filename(file)
                duration = self.get_video_duration(os.path.join(self.VIDEO_DIR, file))
                video_items.append((file, date_str, duration))
                video_count += 1
        
        total_count = image_count + video_count
        return image_items, video_items, total_count

    def get_date_from_filename(self, filename):
        """Lấy ngày từ tên file hoặc ngày sửa đổi file."""
        parts = filename.split('_')
        if len(parts) >= 2:
            try:
                date_part = parts[-2]
                if len(date_part) == 8:  # Định dạng YYYYMMDD
                    return f"{date_part[6:8]}/{date_part[4:6]}/{date_part[0:4]}"
            except:
                pass
        return datetime.datetime.now().strftime("%d/%m/%Y")

    def get_video_duration(self, video_path):
        """Lấy thời lượng video (phút:giây)."""
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return "00:00"
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            duration_sec = frame_count / fps if fps > 0 else 0
            
            minutes = int(duration_sec // 60)
            seconds = int(duration_sec % 60)
            
            cap.release()
            return f"{minutes:02d}:{seconds:02d}"
        except:
            return "00:00"

    def get_image_path(self, filename):
        """Lấy đường dẫn đầy đủ đến file ảnh."""
        return os.path.join(self.HISTORY_DIR, filename)

    def get_video_path(self, filename):
        """Lấy đường dẫn đầy đủ đến file video."""
        return os.path.join(self.VIDEO_DIR, filename)

    def get_filename_from_plate(self, plate):
        """Lấy tên file tương ứng với biển số."""
        return self.plate_to_file_map.get(plate, None)

    def generate_report(self):
        """Tạo báo cáo về các biển số đã nhận diện, nhóm theo ngày."""
        report = []
        report.append("BÁO CÁO NHẬN DIỆN BIỂN SỐ XE\n")
        report.append("=" * 40 + "\n\n")
        report.append(f"Ngày xuất báo cáo: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")
        
        # Đọc lịch sử biển số và nhóm theo ngày
        plate_history = {}
        if os.path.exists("./plate_history.txt"):
            with open("./plate_history.txt", "r", encoding="utf-8") as pf:
                for line in pf:
                    filename, plate_with_time = line.strip().split(",", 1)
                    parts = plate_with_time.split(";")
                    time_str = parts[1].strip() if len(parts) > 1 else "00:00:00 01/01/1970"
                    date_str = time_str.split(" ")[1]
                    if date_str not in plate_history:
                        plate_history[date_str] = []
                    plate_history[date_str].append((filename, plate_with_time))

        # Sắp xếp ngày theo thứ tự giảm dần
        sorted_dates = sorted(plate_history.keys(), key=lambda x: datetime.datetime.strptime(x, "%d/%m/%Y"), reverse=True)

        # Tạo báo cáo nhóm theo ngày
        for date in sorted_dates:
            report.append(f"Ngày: {date}\n")
            report.append("-" * 40 + "\n")
            
            image_entries = []
            video_entries = {}
            for filename, plate_with_time in plate_history[date]:
                if "(from video" in plate_with_time:
                    video_name = plate_with_time.split("(from video ")[1].split(")")[0]
                    if video_name not in video_entries:
                        video_entries[video_name] = []
                    video_entries[video_name].append((filename, plate_with_time))
                else:
                    image_entries.append((filename, plate_with_time))
            
            # Ghi thông tin nhận diện từ ảnh
            if image_entries:
                report.append("Nhận diện từ hình ảnh:\n")
                for filename, plate_with_time in image_entries:
                    plate = plate_with_time.split(";")[0].strip()
                    time_str = plate_with_time.split(";")[1].strip() if ";" in plate_with_time else "00:00:00 01/01/1970"
                    report.append(f"  Tên file: {filename}\n")
                    report.append(f"  Biển số: {plate}\n")
                    report.append(f"  Thời gian: {time_str}\n")
                    report.append("-" * 20 + "\n")
            
            # Ghi thông tin nhận diện từ video
            if video_entries:
                report.append("Nhận diện từ video:\n")
                for video_name, entries in video_entries.items():
                    date_str = self.get_date_from_filename(video_name)
                    duration = self.get_video_duration(os.path.join(self.VIDEO_DIR, video_name))
                    report.append(f"  Video: {video_name}\n")
                    report.append(f"  Ngày: {date_str}\n")
                    report.append(f"  Thời lượng: {duration}\n")
                    report.append("  Biển số nhận diện:\n")
                    seen_plates = set()
                    for filename, plate_with_time in entries:
                        plate = plate_with_time.split(";")[0].strip().split(" (")[0]
                        time_str = plate_with_time.split(";")[1].strip() if ";" in plate_with_time else "00:00:00 01/01/1970"
                        if plate not in seen_plates:
                            report.append(f"    - {plate} (Thời gian: {time_str}, Ảnh: {filename})\n")
                            seen_plates.add(plate)
                    report.append("-" * 20 + "\n")
            
            report.append("\n")
        
        if not plate_history:
            report.append("Không có dữ liệu nhận diện.\n")
        
        return "".join(report)