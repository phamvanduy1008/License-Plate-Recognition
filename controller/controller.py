import threading
from tkinter import filedialog, messagebox
import datetime
import cv2
import shutil
import os
import stat

class LicensePlateController:
    def __init__(self, model, view):
        self.model = model
        self.view = view
        
        # Initialize tracking variables
        self.is_realtime_running = False
        self.realtime_generator = None
        self.is_video_playing = False
        self.video_cap = None
        self.detection_history = []
        
        # Bind UI events to controller methods
        self.view.search_var.trace("w", self.filter_lists)
        self.view.tab_images.configure(command=lambda: self.view.switch_tab("images"))
        self.view.tab_videos.configure(command=lambda: self.view.switch_tab("videos"))
        self.view.image_treeview.bind("<ButtonRelease-1>", self.display_selected_file)
        self.view.video_treeview.bind("<ButtonRelease-1>", self.display_selected_file)
        self.view.realtime_btn.configure(command=self.run_realtime)
        self.view.upload_btn.configure(command=self.upload_file)
        self.view.export_btn.configure(command=self.export_report)
        self.view.update_ip_btn.configure(command=self.update_ip)
        
        # Bind the delete history handler
        self.view.set_delete_handler(self.delete_history)
        
        # Load initial file lists
        self.update_file_lists()

    def update_file_lists(self):
        """Update the file lists in the view"""
        search_text = self.view.search_var.get().lower()
        image_items, video_items, total_count = self.model.get_file_lists(search_text)
        self.view.update_file_lists(image_items, video_items, total_count)

    def filter_lists(self, *args):
        """Filter the lists based on search input"""
        self.update_file_lists()

    def display_selected_file(self, event):
        """Display selected image or play selected video on canvas"""
        widget = event.widget
        selection = widget.selection()
        if not selection:
            return

        item_id = selection[0]
        if widget == self.view.image_treeview:
            # Get the values (filename, plate) from the selected row
            values = widget.item(item_id, "values")
            if not values:
                return
            file_name, plate = values  # Extract filename and plate from the row
            file_path = self.model.get_image_path(file_name)
            self.display_image(file_path)
            # Get full plate_with_time from plate_history to extract time
            with open("./plate_history.txt", "r", encoding="utf-8") as f:
                for line in f:
                    if file_name in line:
                        plate_with_time = line.strip().split(",", 1)[1]
                        time_str = plate_with_time.split(";")[1].strip() if ";" in plate_with_time else "00:00:00 01/01/1970"
                        break
                else:
                    time_str = "00:00:00 01/01/1970"
            
            self.view.update_plate_info(
                plate=plate,
                time_str=time_str,
                confidence=95
            )
        elif widget == self.view.video_treeview:
            selected_item = widget.item(item_id, "text")
            file_path = self.model.get_video_path(selected_item)
            self.play_video(file_path)
            # Look up the plate associated with this video from plate_history.txt
            plate = "Không tìm thấy biển số"
            time_str = "00:00:00 01/01/1970"
            with open("./plate_history.txt", "r", encoding="utf-8") as f:
                for line in f:
                    if f"(from video {selected_item})" in line:
                        plate_with_time = line.strip().split(",", 1)[1]
                        plate = plate_with_time.split(";")[0].strip().split(" (")[0]
                        time_str = plate_with_time.split(";")[1].strip() if ";" in plate_with_time else time_str
                        break
            self.view.update_plate_info(
                plate=plate,
                time_str=time_str,
                confidence=95
            )

    def delete_history(self):
        """Delete the selected history item from plate_history.txt and remove the file"""
        # Determine which treeview has the selected item
        image_selection = self.view.image_treeview.selection()
        video_selection = self.view.video_treeview.selection()

        if not image_selection and not video_selection:
            messagebox.showerror("Lỗi", "Vui lòng chọn một mục để xóa!")
            return

        file_to_delete = None
        is_image = False

        if image_selection:
            item_id = image_selection[0]
            # Get the filename from the selected row
            file_to_delete = self.view.image_treeview.item(item_id, "values")[0]
            is_image = True
        elif video_selection:
            item_id = video_selection[0]
            file_to_delete = self.view.video_treeview.item(item_id, "text")
            is_image = False

        if not file_to_delete:
            messagebox.showerror("Lỗi", "Không tìm thấy tệp tương ứng để xóa!")
            return

        # Xóa dòng trong plate_history.txt
        try:
            updated_lines = []
            if os.path.exists("./plate_history.txt"):
                with open("./plate_history.txt", "r", encoding="utf-8") as f:
                    if is_image:
                        updated_lines = [line for line in f if file_to_delete not in line]
                    else:
                        updated_lines = [line for line in f if f"(from video {file_to_delete})" not in line]
                with open("./plate_history.txt", "w", encoding="utf-8") as f:
                    f.writelines(updated_lines)

            # Xóa tệp tương ứng
            if is_image:
                file_path = os.path.join(self.model.HISTORY_DIR, file_to_delete)
            else:
                file_path = os.path.join(self.model.VIDEO_DIR, file_to_delete)

            if os.path.exists(file_path):
                os.chmod(file_path, stat.S_IWRITE | stat.S_IREAD)
                os.remove(file_path)
                self.view.update_status("⬤ Đã xóa lịch sử", "#f44336")
            else:
                messagebox.showwarning("Cảnh báo", f"Tệp {file_to_delete} không tồn tại trong thư mục!")
                self.view.update_status("⬤ Tệp không tồn tại", "#ff9800")

            # Cập nhật lại danh sách
            self.update_file_lists()
            self.view.canvas.delete("all")
            self.view.update_plate_info("Chưa có dữ liệu", "--:--:--", 0)

        except PermissionError:
            messagebox.showerror("Lỗi", f"Không thể xóa tệp {file_to_delete} do file đang chạy!")
            self.view.update_status("⬤ Lỗi", "#f44336")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể xóa tệp: {str(e)}")
            self.view.update_status("⬤ Lỗi xóa lịch sử", "#f44336")

    def display_image(self, file_path):
        """Display an image on the canvas"""
        self.stop_video()
        img = cv2.imread(file_path)
        if img is not None:
            self.view.update_canvas(img)
            self.view.update_status("⬤ Hiển thị ảnh", "#1e88e5")
        else:
            messagebox.showerror("Lỗi", "Không thể đọc hình ảnh")

    def play_video(self, file_path):
        """Play a video on the canvas"""
        self.stop_video()
        self.video_cap = cv2.VideoCapture(file_path)
        if not self.video_cap.isOpened():
            messagebox.showerror("Lỗi", "Không thể mở video")
            return

        self.is_video_playing = True
        self.view.update_status("⬤ Đang phát video", "#f57c00")

        def update_video():
            if not self.is_video_playing or not self.video_cap.isOpened():
                self.stop_video()
                return

            ret, frame = self.video_cap.read()
            if ret:
                self.view.update_canvas(frame)
                self.view.root.after(33, update_video)  # ~30 FPS
            else:
                self.stop_video()
                self.view.update_status("⬤ Kết thúc video", "#757575")

        self.view.root.after(0, update_video)

    def stop_video(self):
        """Stop any playing video"""
        self.is_video_playing = False
        if self.video_cap is not None:
            self.video_cap.release()
            self.video_cap = None
        self.view.canvas.delete("all")
        self.view.update_status("⬤ Sẵn sàng", self.view.accent_color)

    def stop_realtime(self):
        """Stop real-time detection"""
        self.is_realtime_running = False
        if self.realtime_generator is not None:
            try:
                next(self.realtime_generator)  # Force the generator to stop
            except StopIteration:
                pass
            self.realtime_generator = None
        self.view.update_status("⬤ Đã dừng real-time", "#757575")

    def run_realtime(self):
        """Run real-time detection"""
        if self.is_realtime_running:
            return
            
        self.stop_video()
        self.is_realtime_running = True
        cam_source = self.view.ip_entry.get()
        
        self.view.update_status("⬤ Đang chạy real-time", "#f44336")
        self.view.plate_label.configure(text="Đang xử lý...")
        self.view.show_loading("Đang kết nối camera...")
        
        def start_realtime_thread():
            try:
                self.realtime_generator = self.model.process_realtime(cam_source)
                self.view.root.after(100, self.update_realtime)
            except Exception as e:
                self.is_realtime_running = False
                self.view.update_status("⬤ Lỗi kết nối", "#f44336")
                messagebox.showerror("Lỗi", f"Không thể kết nối camera: {str(e)}")
        
        threading.Thread(target=start_realtime_thread).start()

    def update_realtime(self):
        """Update UI with real-time detection results"""
        if not self.is_realtime_running:
            self.view.update_status("⬤ Đã dừng real-time", "#757575")
            self.update_file_lists()
            return
            
        try:
            captured_frame, current_plate = next(self.realtime_generator)
            if captured_frame is not None:
                self.view.update_canvas(captured_frame)
                if current_plate is not None:
                    current_time = datetime.datetime.now().strftime("%H:%M:%S %d/%m/%Y")
                    self.view.update_plate_info(
                        plate=current_plate,
                        time_str=current_time,
                        confidence=97
                    )
                    if current_plate not in self.detection_history:
                        self.detection_history.append(current_plate)
                        self.update_file_lists()
        except StopIteration:
            self.is_realtime_running = False
            self.view.update_status("⬤ Kết thúc real-time", "#757575")
            return
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi xử lý: {str(e)}")
            self.is_realtime_running = False
            self.view.update_status("⬤ Lỗi xử lý", "#f44336")
            return
            
        self.view.root.after(50, self.update_realtime)

    def update_ip(self):
        """Handle IP address update"""
        new_ip = self.view.ip_entry.get()
        if not new_ip.startswith("http://") or "video" not in new_ip:
            messagebox.showerror("Lỗi", "Địa chỉ IP không hợp lệ. Vui lòng nhập dạng http://<ip>:<port>/video")
            return
        if self.is_realtime_running:
            self.stop_realtime()
            self.view.update_status("⬤ IP đã được cập nhật", "#4caf50")
            self.run_realtime()
        else:
            self.view.update_status("⬤ IP đã được cập nhật", "#4caf50")
            messagebox.showinfo("Thông báo", "IP đã được cập nhật. Nhấn 'Chế độ Real-time' để sử dụng IP mới.")

    def upload_file(self):
        """Upload and process image or video file"""
        self.stop_video()
        file_path = filedialog.askopenfilename(
            filetypes=[
                ("Ảnh/Video", "*.jpg *.jpeg *.png *.mp4"),
                ("Ảnh", "*.jpg *.jpeg *.png"),
                ("Video", "*.mp4")
            ],
            title="Chọn file ảnh hoặc video"
        )
        
        if not file_path:
            return
            
        self.view.show_loading("Đang xử lý...")
        self.view.root.update()
        
        if file_path.lower().endswith(('.jpg', '.jpeg', '.png')):
            self.view.update_status("⬤ Đang xử lý ảnh", "#fb8c00")
            
            def process_image_thread():
                try:
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    original_filename = os.path.basename(file_path)
                    unique_filename = f"image_{timestamp}_{original_filename}"
                    image_dest_path = os.path.join(self.model.HISTORY_DIR, unique_filename)
                    shutil.copy2(file_path, image_dest_path)
                    
                    img, plates, captured_frame = self.model.process_image(image_dest_path)
                    
                    def update_ui():
                        if img is not None:
                            self.view.update_canvas(img)
                            plate = next(iter(plates)) if plates else "Không tìm thấy biển số"
                            current_time = datetime.datetime.now().strftime("%H:%M:%S %d/%m/%Y")
                            self.view.update_plate_info(
                                plate=plate,
                                time_str=current_time,
                                confidence=96
                            )
                            self.view.update_status("⬤ Hoàn tất xử lý", "#4caf50")
                            self.update_file_lists()
                        else:
                            messagebox.showerror("Lỗi", "Không thể đọc ảnh")
                            self.view.update_status("⬤ Lỗi xử lý", "#f44336")
                    
                    self.view.root.after(0, update_ui)
                    
                except Exception as e:
                    def show_error(error):
                        messagebox.showerror("Lỗi", f"Lỗi xử lý ảnh: {str(error)}")
                        self.view.update_status("⬤ Lỗi xử lý", "#f44336")
                    
                    self.view.root.after(0, lambda: show_error(e))
            
            threading.Thread(target=process_image_thread).start()
            
        elif file_path.lower().endswith('.mp4'):
            self.view.update_status("⬤ Đang xử lý video", "#fb8c00")
            
            def process_video_thread():
                try:
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    original_filename = os.path.basename(file_path)
                    unique_filename = f"video_{timestamp}_{original_filename}"
                    video_dest_path = os.path.join(self.model.VIDEO_DIR, unique_filename)
                    
                    _, plates, _ = self.model.process_video(file_path, video_dest_path)
                    
                    def update_ui():
                        plate = next(iter(plates)) if plates else "Không tìm thấy biển số"
                        current_time = datetime.datetime.now().strftime("%H:%M:%S %d/%m/%Y")
                        self.view.update_plate_info(
                            plate=plate,
                            time_str=current_time,
                            confidence=0
                        )
                        self.view.update_status("⬤ Hoàn tất xử lý", "#4caf50")
                        self.play_video(video_dest_path)
                        self.update_file_lists()
                    
                    self.view.root.after(0, update_ui)
                    
                except Exception as e:
                    def show_error(error):
                        messagebox.showerror("Lỗi", f"Lỗi xử lý video: {str(error)}")
                        self.view.update_status("⬤ Lỗi xử lý", "#f44336")
                    
                    self.view.root.after(0, lambda: show_error(e))
            
            threading.Thread(target=process_video_thread).start()

    def export_report(self):
        """Export detection results to a report file"""
        today = datetime.datetime.now().strftime("%Y%m%d")
        filename = f"bao_cao_bien_so_{today}.txt"
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=filename,
            title="Lưu báo cáo"
        )
        
        if not file_path:
            return
            
        try:
            report_content = self.model.generate_report()
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            messagebox.showinfo("Thành công", f"Đã xuất báo cáo thành công: {file_path}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể xuất báo cáo: {str(e)}")

    def on_closing(self):
        """Clean up resources before closing"""
        self.stop_video()
        self.stop_realtime()
        self.view.root.destroy()