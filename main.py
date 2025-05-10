import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from PIL import Image, ImageTk
import cv2
import os
from app_utils.process import process_image, process_video, process_realtime

class LicensePlateApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Hệ thống Nhận Diện Biển Số Xe")
        self.root.state('zoomed')
        self.root.configure(bg="#eceff1")

        # Main container with two columns
        self.main_frame = tk.Frame(root, bg="#eceff1")
        self.main_frame.pack(pady=20, padx=20, fill="both", expand=True)

        # Left frame for lists with padding to push content down
        self.list_frame = tk.Frame(self.main_frame, bg="#eceff1", width=300)
        self.list_frame.pack(side="left", fill="y", padx=10)

        # Spacer to push lists down
        self.spacer = tk.Label(self.list_frame, text="", bg="#eceff1", height=10)
        self.spacer.pack()

        # Right frame for existing UI
        self.content_frame = tk.Frame(self.main_frame, bg="#eceff1")
        self.content_frame.pack(side="left", fill="both", expand=True)

        # Image list with scrollbar
        self.image_label = tk.Label(
            self.list_frame,
            text="Hình ảnh đã chụp",
            font=("Helvetica", 12, "bold"),
            bg="#eceff1",
            fg="#263238"
        )
        self.image_label.pack(pady=5)

        # Frame for image listbox and scrollbar
        self.image_list_frame = tk.Frame(self.list_frame, bg="#eceff1")
        self.image_list_frame.pack(pady=5, padx=5, fill="both", expand=True)

        self.image_scrollbar = ttk.Scrollbar(self.image_list_frame, orient=tk.VERTICAL)
        self.image_scrollbar.pack(side="right", fill="y")

        self.image_listbox = tk.Listbox(
            self.image_list_frame,
            width=40,
            height=15,
            font=("Helvetica", 10),
            bg="#ffffff",
            fg="#263238",
            selectbackground="#2ecc71",
            selectforeground="white",
            yscrollcommand=self.image_scrollbar.set,
            borderwidth=1,
            relief="flat",
            highlightthickness=1,
            highlightbackground="#b0bec5"
        )
        self.image_listbox.pack(side="left", fill="both", expand=True)
        self.image_scrollbar.config(command=self.image_listbox.yview)
        self.image_listbox.bind('<<ListboxSelect>>', self.display_selected_file)

        # Video list with scrollbar
        self.video_label = tk.Label(
            self.list_frame,
            text="Video đã quay",
            font=("Helvetica", 12, "bold"),
            bg="#eceff1",
            fg="#263238"
        )
        self.video_label.pack(pady=5)

        # Frame for video listbox and scrollbar
        self.video_list_frame = tk.Frame(self.list_frame, bg="#eceff1")
        self.video_list_frame.pack(pady=5, padx=5, fill="both", expand=True)

        self.video_scrollbar = ttk.Scrollbar(self.video_list_frame, orient=tk.VERTICAL)
        self.video_scrollbar.pack(side="right", fill="y")

        self.video_listbox = tk.Listbox(
            self.video_list_frame,
            width=40,
            height=15,
            font=("Helvetica", 10),
            bg="#ffffff",
            fg="#263238",
            selectbackground="#2ecc71",
            selectforeground="white",
            yscrollcommand=self.video_scrollbar.set,
            borderwidth=1,
            relief="flat",
            highlightthickness=1,
            highlightbackground="#b0bec5"
        )
        self.video_listbox.pack(side="left", fill="both", expand=True)
        self.video_scrollbar.config(command=self.video_listbox.yview)
        self.video_listbox.bind('<<ListboxSelect>>', self.display_selected_file)

        # Title
        self.title_label = tk.Label(
            self.content_frame,
            text="Hệ thống nhận diện biển số xe",
            font=("Helvetica", 26, "bold"),
            bg="#eceff1",
            fg="#263238"
        )
        self.title_label.pack(pady=10)

        # Control panel with shadow effect
        self.shadow_frame = tk.Frame(self.content_frame, bg="#cfd8dc", bd=0)
        self.shadow_frame.pack(pady=10, padx=10, fill="x")
        self.control_frame = tk.Frame(self.shadow_frame, bg="#ffffff", bd=0, relief="flat")
        self.control_frame.pack(pady=2, padx=2, fill="x")

        # Horizontal container for buttons and IP input
        self.control_container = tk.Frame(self.control_frame, bg="#ffffff")
        self.control_container.pack(pady=10)

        # Button frame for buttons
        self.button_frame = tk.Frame(self.control_container, bg="#ffffff")
        self.button_frame.pack(side="left", padx=10)

        # Buttons
        self.btn_realtime = tk.Button(
            self.button_frame,
            text="Chế độ Real-time",
            command=self.run_realtime,
            font=("Helvetica", 11, "bold"),
            bg="#2ecc71",
            fg="white",
            activebackground="#27ae60",
            relief="flat",
            cursor="hand2",
            bd=2,
            highlightbackground="#27ae60",
            highlightthickness=2,
            width=12,
            padx=10,
            pady=6
        )
        self.btn_realtime.pack(side="left", padx=8)
        self.btn_realtime.config(highlightcolor="#ffffff", highlightbackground="#ffffff")
        self.btn_realtime.bind("<Enter>", lambda e: self.btn_realtime.config(bg="#27ae60", highlightbackground="#219653"))
        self.btn_realtime.bind("<Leave>", lambda e: self.btn_realtime.config(bg="#2ecc71", highlightbackground="#27ae60"))

        self.btn_upload = tk.Button(
            self.button_frame,
            text="Tải Ảnh/Video",
            command=self.upload_file,
            font=("Helvetica", 11, "bold"),
            bg="#3498db",
            fg="white",
            activebackground="#2980b9",
            relief="flat",
            cursor="hand2",
            bd=2,
            highlightbackground="#2980b9",
            highlightthickness=2,
            width=12,
            padx=10,
            pady=6
        )
        self.btn_upload.pack(side="left", padx=8)
        self.btn_upload.config(highlightcolor="#ffffff", highlightbackground="#ffffff")
        self.btn_upload.bind("<Enter>", lambda e: self.btn_upload.config(bg="#2980b9", highlightbackground="#2b6a94"))
        self.btn_upload.bind("<Leave>", lambda e: self.btn_upload.config(bg="#3498db", highlightbackground="#2980b9"))

        # DroidCam IP input
        self.ip_frame = tk.Frame(self.control_container, bg="#ffffff")
        self.ip_frame.pack(side="left", padx=10)
        self.label_ip = tk.Label(
            self.ip_frame,
            text="IP DroidCam: ",
            font=("Helvetica", 11),
            bg="#ffffff",
            fg="#263238"
        )
        self.label_ip.pack(side="left")
        self.entry_ip = tk.Entry(
            self.ip_frame,
            width=25,
            font=("Helvetica", 11),
            bd=1,
            relief="solid",
            bg="#f7f9fb",
            fg="#263238",
            highlightthickness=1,
            highlightbackground="#b0bec5"
        )
        self.entry_ip.insert(0, "http://192.168.1.18:4747/video")
        self.entry_ip.pack(side="left", padx=10)

        # Result label
        self.result_label = tk.Label(
            self.content_frame,
            text="Kết quả: Chưa có dữ liệu",
            font=("Helvetica", 12),
            bg="#eceff1",
            fg="#263238",
            wraplength=900,
            anchor="w",
            justify="left"
        )
        self.result_label.pack(pady=10, fill="x", padx=20)

        # Canvas for image/video display with shadow effect
        self.canvas_shadow = tk.Frame(self.content_frame, bg="#cfd8dc", bd=0)
        self.canvas_shadow.pack(pady=10)
        self.canvas = tk.Canvas(
            self.canvas_shadow,
            width=720,
            height=540,
            bg="#ffffff",
            bd=0,
            relief="flat",
            highlightthickness=1,
            highlightbackground="#b0bec5"
        )
        self.canvas.pack(pady=2, padx=2)

        self.is_realtime_running = False
        self.realtime_generator = None
        self.is_video_playing = False
        self.video_cap = None

        # Load initial file lists
        self.update_file_lists()

    def update_file_lists(self):
        """Update the image and video lists from directories."""
        self.image_listbox.delete(0, tk.END)
        self.video_listbox.delete(0, tk.END)

        # Load images
        image_dir = "D:/Python/License-Plate-Recognition/history_image"
        for file in sorted(os.listdir(image_dir)):
            if file.endswith('.jpg'):
                self.image_listbox.insert(tk.END, file)

        # Load videos
        video_dir = "D:/Python/License-Plate-Recognition/history_video"
        for file in sorted(os.listdir(video_dir)):
            if file.endswith('.mp4'):
                self.video_listbox.insert(tk.END, file)

    def display_selected_file(self, event):
        """Display selected image or play selected video on canvas."""
        widget = event.widget
        if not widget.curselection():
            return

        selected_file = widget.get(widget.curselection()[0])
        if widget == self.image_listbox:
            file_path = os.path.join("D:/Python/License-Plate-Recognition/history_image", selected_file)
            self.display_image(file_path)
        elif widget == self.video_listbox:
            file_path = os.path.join("D:/Python/License-Plate-Recognition/history_video", selected_file)
            self.play_video(file_path)

    def display_image(self, file_path):
        """Display an image on the canvas."""
        self.stop_video()  # Stop any playing video
        img = cv2.imread(file_path)
        if img is not None:
            self.update_canvas(img)
            self.result_label.config(text="Kết quả: Đã chọn hình ảnh")
        else:
            messagebox.showerror("Lỗi", "Không thể đọc hình ảnh")

    def play_video(self, file_path):
        """Play a video on the canvas."""
        self.stop_video()  # Stop any playing video
        self.video_cap = cv2.VideoCapture(file_path)
        if not self.video_cap.isOpened():
            messagebox.showerror("Lỗi", "Không thể mở video")
            return

        self.is_video_playing = True
        self.result_label.config(text="Kết quả: Đang phát video")

        def update_video():
            if not self.is_video_playing or not self.video_cap.isOpened():
                self.stop_video()
                return

            ret, frame = self.video_cap.read()
            if ret:
                self.update_canvas(frame)
                self.root.after(33, update_video)  # ~30 FPS
            else:
                self.stop_video()
                self.result_label.config(text="Kết quả: Kết thúc video")

        self.root.after(0, update_video)

    def stop_video(self):
        """Stop any playing video."""
        self.is_video_playing = False
        if self.video_cap is not None:
            self.video_cap.release()
            self.video_cap = None
        self.canvas.delete("all")

    def update_canvas(self, frame):
        """Update canvas with new frame."""
        if frame is not None:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = Image.fromarray(frame)
            frame = frame.resize((720, 540), Image.LANCZOS)
            self.photo = ImageTk.PhotoImage(frame)
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)

    def run_realtime(self):
        if self.is_realtime_running:
            return
        self.stop_video()  # Stop any playing video
        self.is_realtime_running = True
        cam_source = self.entry_ip.get()
        self.result_label.config(text="Đang chạy chế độ real-time...")
        self.canvas.delete("all")

        self.realtime_generator = process_realtime(cam_source)

        def update_realtime():
            if not self.is_realtime_running:
                self.result_label.config(text="Đã đóng chế độ real-time")
                self.update_file_lists()  # Update lists when real-time ends
                return

            try:
                captured_frame, current_plate = next(self.realtime_generator)
                if captured_frame is not None and current_plate is not None:
                    self.update_canvas(captured_frame)
                    self.result_label.config(text=f"Kết quả: {current_plate}")
                    self.update_file_lists()  # Update lists when a new plate is detected
                else:
                    self.result_label.config(text="Kết quả: Chưa có dữ liệu")
            except StopIteration:
                self.is_realtime_running = False
                self.result_label.config(text="Đã đóng chế độ real-time")
                self.update_file_lists()
                return
            except Exception as e:
                messagebox.showerror("Lỗi", f"Đã xảy ra lỗi: {str(e)}")
                self.is_realtime_running = False
                self.result_label.config(text="Đã đóng chế độ real-time")
                self.update_file_lists()
                return

            self.root.after(50, update_realtime)

        self.root.after(0, update_realtime)

    def upload_file(self):
        self.stop_video()  # Stop any playing video
        file_path = filedialog.askopenfilename(filetypes=[("Image/Video files", "*.jpg *.png *.mp4")])
        if file_path:
            self.canvas.delete("all")
            if file_path.endswith(('.jpg', '.png')):
                img, plates, captured_frame = process_image(file_path)
                if img is not None:
                    self.update_canvas(img)
                    plate = next(iter(plates)) if plates else "Chưa có dữ liệu"
                    self.result_label.config(text=f"Kết quả: {plate}")
                else:
                    messagebox.showerror("Lỗi", "Không thể đọc ảnh")
            elif file_path.endswith('.mp4'):
                self.result_label.config(text="Đang xử lý video...")
                _, plates, _ = process_video(file_path)
                plate = next(iter(plates)) if plates else "Chưa có dữ liệu"
                self.result_label.config(text=f"Kết quả: {plate}")

    def destroy(self):
        self.stop_video()
        self.is_realtime_running = False
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = LicensePlateApp(root)
    root.mainloop()