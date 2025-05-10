import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import customtkinter as ctk
from PIL import Image, ImageTk
import cv2
import os
from app_utils.process import process_image, process_video, process_realtime
import datetime
import threading

ctk.set_appearance_mode("System")  
ctk.set_default_color_theme("blue")  

class ModernLicensePlateApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Hệ thống Nhận Diện Biển Số Xe")
        self.root.state('zoomed')
        self.root.configure(bg="#f5f5f7")
        
        # Modern font settings
        self.header_font = ("Roboto", 24, "bold")
        self.subheader_font = ("Roboto", 14, "bold")
        self.normal_font = ("Roboto", 12)
        self.small_font = ("Roboto", 10)
        
        # Color scheme
        self.primary_color = "#1e88e5"     
        self.secondary_color = "#1976d2"    
        self.accent_color = "#43a047"       
        self.text_color = "#212121"         
        self.bg_color = "#f5f5f7"         
        self.card_bg = "#ffffff"          
        self.card_border = "#e0e0e0"         
        
        self.create_main_layout()
        
        # Setup UI components
        self.setup_header()
        self.setup_sidebar()
        self.setup_content_area()
        self.setup_control_panel()
        
        # Initialize tracking variables
        self.is_realtime_running = False
        self.realtime_generator = None
        self.is_video_playing = False
        self.video_cap = None
        self.detection_history = []
        
        # Load initial file lists
        self.update_file_lists()

    def create_main_layout(self):
        """Create the main application layout with modern grid system"""
        # Main container
        self.main_container = ctk.CTkFrame(self.root, fg_color=self.bg_color, corner_radius=0)
        self.main_container.pack(fill="both", expand=True, padx=0, pady=0)
        
        for i in range(12):
            self.main_container.columnconfigure(i, weight=1)
        
        self.main_container.rowconfigure(0, weight=0)  
        self.main_container.rowconfigure(1, weight=1)  
        self.main_container.rowconfigure(2, weight=0) 

    def setup_header(self):
        """Create the application header with logo and title"""
        # Header container
        self.header = ctk.CTkFrame(self.main_container, fg_color=self.primary_color, corner_radius=0, height=70)
        self.header.grid(row=0, column=0, columnspan=12, sticky="ew")
        
        self.logo_label = ctk.CTkLabel(
            self.header, 
            text="🚗", 
            font=("Roboto", 30),
            text_color="#ffffff"
        )
        self.logo_label.pack(side="left", padx=(20, 0))
        
        self.title_label = ctk.CTkLabel(
            self.header,
            text="HỆ THỐNG NHẬN DIỆN BIỂN SỐ XE",
            font=("Roboto", 22, "bold"),
            text_color="#ffffff"
        )
        self.title_label.pack(side="left", padx=15)
        

    def setup_sidebar(self):
        """Create the sidebar with file lists and filters"""
        # Sidebar container
        self.sidebar = ctk.CTkFrame(
            self.main_container, 
            fg_color=self.card_bg, 
            corner_radius=15,
            border_width=1,
            border_color=self.card_border
        )
        self.sidebar.grid(row=1, column=0, columnspan=3, sticky="nsew", padx=(20, 10), pady=20)
        
        self.history_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.history_frame.pack(fill="x", padx=15, pady=(15, 5))
        
        self.history_label = ctk.CTkLabel(
            self.history_frame,
            text="Lịch Sử Nhận Diện",
            font=self.subheader_font,
            anchor="w"
        )
        self.history_label.pack(side="left")
        
        self.history_count = ctk.CTkLabel(
            self.history_frame,
            text="0",
            font=self.small_font,
            width=25,
            height=25,
            corner_radius=12,
            fg_color=self.primary_color,
            text_color="#ffffff"
        )
        self.history_count.pack(side="right")
        
        # Search bar
        self.search_var = tk.StringVar()
        self.search_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.search_frame.pack(fill="x", padx=15, pady=10)
        
        self.search_icon_label = ctk.CTkLabel(self.search_frame, text="🔍", font=("Roboto", 14))
        self.search_icon_label.pack(side="left", padx=(0, 5))
        
        self.search_entry = ctk.CTkEntry(
            self.search_frame,
            placeholder_text="Tìm kiếm...",
            font=self.normal_font,
            border_width=0,
            textvariable=self.search_var
        )
        self.search_entry.pack(side="left", fill="x", expand=True)
        self.search_var.trace("w", self.filter_lists)
        
        # Tabs for images and videos
        self.tab_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.tab_frame.pack(fill="x", padx=15, pady=5)
        
        self.tab_images = ctk.CTkButton(
            self.tab_frame,
            text="Hình Ảnh",
            font=self.normal_font,
            fg_color=self.primary_color,
            text_color="#ffffff",
            corner_radius=5,
            command=lambda: self.switch_tab("images")
        )
        self.tab_images.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        self.tab_videos = ctk.CTkButton(
            self.tab_frame,
            text="Video",
            font=self.normal_font,
            fg_color="#e0e0e0",
            text_color=self.text_color,
            corner_radius=5,
            command=lambda: self.switch_tab("videos")
        )
        self.tab_videos.pack(side="left", fill="x", expand=True, padx=(5, 0))
        
        self.active_tab = "images"
        
        # File lists with modern styling
        self.list_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        # Image list
        self.image_list_frame = ctk.CTkFrame(self.list_frame, fg_color="transparent")
        self.image_list_frame.pack(fill="both", expand=True)
        
        # Create a custom theme for the Treeview
        style = ttk.Style()
        style.theme_use('default')
        style.configure(
            "Treeview", 
            background="#ffffff",
            foreground=self.text_color,
            rowheight=40,
            fieldbackground="#ffffff",
            borderwidth=0
        )
        style.map('Treeview', background=[('selected', self.primary_color)], foreground=[('selected', 'white')])
        
        # Configure the Treeview heading style
        style.configure(
            "Treeview.Heading",
            background=self.bg_color,
            foreground=self.text_color,
            relief="flat",
            font=self.normal_font
        )
        
        # Create scrollbar for images treeview
        self.image_scrollbar = ttk.Scrollbar(self.image_list_frame)
        self.image_scrollbar.pack(side="right", fill="y")
        
        # Images treeview - Updated to show Filename and Plate
        self.image_treeview = ttk.Treeview(
            self.image_list_frame,
            columns=("filename", "plate"),
            show="headings",
            yscrollcommand=self.image_scrollbar.set
        )
        
        # Configure columns
        self.image_treeview.heading("filename", text="Tên File")
        self.image_treeview.heading("plate", text="Biển Số")
        self.image_treeview.column("filename", width=150)
        self.image_treeview.column("plate", width=100)
        
        self.image_treeview.pack(fill="both", expand=True)
        self.image_scrollbar.config(command=self.image_treeview.yview)
        self.image_treeview.bind("<ButtonRelease-1>", self.display_selected_file)
        
        # Video list (initially hidden)
        self.video_list_frame = ctk.CTkFrame(self.list_frame, fg_color="transparent")
        
        # Create scrollbar for videos treeview
        self.video_scrollbar = ttk.Scrollbar(self.video_list_frame)
        self.video_scrollbar.pack(side="right", fill="y")
        
        # Videos treeview
        self.video_treeview = ttk.Treeview(
            self.video_list_frame,
            columns=("date", "duration"),
            show="headings",
            yscrollcommand=self.video_scrollbar.set
        )
        
        # Configure columns
        self.video_treeview.heading("date", text="Ngày")
        self.video_treeview.heading("duration", text="Thời lượng")
        self.video_treeview.column("date", width=100)
        self.video_treeview.column("duration", width=150)
        
        self.video_treeview.pack(fill="both", expand=True)
        self.video_scrollbar.config(command=self.video_treeview.yview)
        self.video_treeview.bind("<ButtonRelease-1>", self.display_selected_file)

    def switch_tab(self, tab_name):
        """Switch between image and video tabs"""
        if tab_name == "images" and self.active_tab != "images":
            self.tab_images.configure(fg_color=self.primary_color, text_color="#ffffff")
            self.tab_videos.configure(fg_color="#e0e0e0", text_color=self.text_color)
            self.video_list_frame.pack_forget()
            self.image_list_frame.pack(fill="both", expand=True)
            self.active_tab = "images"
        elif tab_name == "videos" and self.active_tab != "videos":
            self.tab_images.configure(fg_color="#e0e0e0", text_color=self.text_color)
            self.tab_videos.configure(fg_color=self.primary_color, text_color="#ffffff")
            self.image_list_frame.pack_forget()
            self.video_list_frame.pack(fill="both", expand=True)
            self.active_tab = "videos"

    def filter_lists(self, *args):
        """Filter the lists based on search input"""
        search_text = self.search_var.get().lower()
        
        # Clear current lists
        for item in self.image_treeview.get_children():
            self.image_treeview.delete(item)
        for item in self.video_treeview.get_children():
            self.video_treeview.delete(item)
        
        image_dir = "D:/hoc_may/License-Plate-Recognition/history_image"
        video_dir = "D:/hoc_may/License-Plate-Recognition/history_video"
        
        # Read plate history
        plate_history = {}
        if os.path.exists("D:/hoc_may/License-Plate-Recognition/plate_history.txt"):
            with open("D:/hoc_may/License-Plate-Recognition/plate_history.txt", "r", encoding="utf-8") as f:
                for line in f:
                    filename, plate = line.strip().split(",")
                    plate_history[filename] = plate
        
        # Filter and load images
        for file in sorted(os.listdir(image_dir), reverse=True):
            if file.endswith('.jpg') and search_text in file.lower():
                plate = plate_history.get(file, "Không xác định")
                self.image_treeview.insert("", "end", values=(file, plate), text=file)
        
        # Filter and load videos
        for file in sorted(os.listdir(video_dir), reverse=True):
            if file.endswith('.mp4') and search_text in file.lower():
                date_str = self.get_date_from_filename(file)
                duration = self.get_video_duration(os.path.join(video_dir, file))
                self.video_treeview.insert("", "end", values=(date_str, duration), text=file)

    def get_date_from_filename(self, filename):
        """Extract date from filename or return file modification date"""
        parts = filename.split('_')
        if len(parts) >= 2:
            try:
                date_part = parts[-2]  # Adjusted to match new filename format: <plate>_<YYYYMMDD>_<HHMMSS>.jpg
                if len(date_part) == 8:  # YYYYMMDD format
                    return f"{date_part[6:8]}/{date_part[4:6]}/{date_part[0:4]}"
            except:
                pass
        
        # Default to current date if extraction fails
        return datetime.datetime.now().strftime("%d/%m/%Y")

    def get_video_duration(self, video_path):
        """Get duration of video in minutes:seconds format"""
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

    def setup_content_area(self):
        """Create the main content area with preview and details"""
        # Content container
        self.content_area = ctk.CTkFrame(
            self.main_container, 
            fg_color=self.bg_color,
            corner_radius=0
        )
        self.content_area.grid(row=1, column=3, columnspan=9, sticky="nsew", padx=(10, 20), pady=20)
        
        # Preview card
        self.preview_card = ctk.CTkFrame(
            self.content_area, 
            fg_color=self.card_bg,
            corner_radius=15,
            border_width=1,
            border_color=self.card_border
        )
        self.preview_card.pack(fill="both", expand=True, padx=0, pady=0)
        
        # Preview header
        self.preview_header = ctk.CTkFrame(self.preview_card, fg_color="transparent", height=40)
        self.preview_header.pack(fill="x", padx=20, pady=(20, 0))
        
        self.preview_title = ctk.CTkLabel(
            self.preview_header,
            text="Xem Trước",
            font=self.subheader_font,
            anchor="w"
        )
        self.preview_title.pack(side="left")
        
        self.status_indicator = ctk.CTkLabel(
            self.preview_header,
            text="⬤ Sẵn sàng",
            font=self.small_font,
            text_color=self.accent_color
        )
        self.status_indicator.pack(side="right")
        
        # Canvas for image/video display
        self.canvas_frame = ctk.CTkFrame(self.preview_card, fg_color="#f0f0f0", corner_radius=10)
        self.canvas_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.canvas = tk.Canvas(
            self.canvas_frame,
            bg="#f0f0f0",
            bd=0,
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)
        
        # Results frame
        self.results_frame = ctk.CTkFrame(self.preview_card, fg_color="transparent")
        self.results_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        # License plate container
        self.plate_container = ctk.CTkFrame(
            self.results_frame,
            fg_color=self.bg_color,
            corner_radius=8,
            height=60
        )
        self.plate_container.pack(fill="x", pady=10)
        
        # License plate icon
        self.plate_icon = ctk.CTkLabel(
            self.plate_container,
            text="🚘",
            font=("Roboto", 22)
        )
        self.plate_icon.pack(side="left", padx=(15, 0))
        
        # License plate value
        self.plate_label = ctk.CTkLabel(
            self.plate_container,
            text="Chưa có dữ liệu",
            font=("Roboto", 24, "bold")
        )
        self.plate_label.pack(side="left", padx=15)
        
        # Details container
        self.details_container = ctk.CTkFrame(self.results_frame, fg_color="transparent")
        self.details_container.pack(fill="x", pady=10)
        
        # Time stamp
        self.time_frame = ctk.CTkFrame(
            self.details_container,
            fg_color=self.bg_color,
            corner_radius=8,
            height=40,
            width=200
        )
        self.time_frame.pack(side="left", fill="y", expand=True, padx=(0, 5))
        
        self.time_icon = ctk.CTkLabel(
            self.time_frame,
            text="🕒",
            font=("Roboto", 14)
        )
        self.time_icon.pack(side="left", padx=(15, 0))
        
        self.time_label = ctk.CTkLabel(
            self.time_frame,
            text="Thời gian: --:--:--",
            font=self.normal_font
        )
        self.time_label.pack(side="left", padx=10)
        
        # Location
        self.location_frame = ctk.CTkFrame(
            self.details_container,
            fg_color=self.bg_color,
            corner_radius=8,
            height=40,
            width=200
        )
        self.location_frame.pack(side="left", fill="y", expand=True, padx=5)
        
        self.location_icon = ctk.CTkLabel(
            self.location_frame,
            text="📍",
            font=("Roboto", 14)
        )
        self.location_icon.pack(side="left", padx=(15, 0))
        
        self.location_label = ctk.CTkLabel(
            self.location_frame,
            text="Vị trí: Không xác định",
            font=self.normal_font
        )
        self.location_label.pack(side="left", padx=10)
        
        # Confidence
        self.confidence_frame = ctk.CTkFrame(
            self.details_container,
            fg_color=self.bg_color,
            corner_radius=8,
            height=40,
            width=200
        )
        self.confidence_frame.pack(side="left", fill="y", expand=True, padx=(5, 0))
        
        self.confidence_icon = ctk.CTkLabel(
            self.confidence_frame,
            text="📊",
            font=("Roboto", 14)
        )
        self.confidence_icon.pack(side="left", padx=(15, 0))
        
        self.confidence_label = ctk.CTkLabel(
            self.confidence_frame,
            text="Độ chính xác: ---%",
            font=self.normal_font
        )
        self.confidence_label.pack(side="left", padx=10)

    def setup_control_panel(self):
        """Create the control panel with action buttons and settings"""
        # Control panel container
        self.control_panel = ctk.CTkFrame(
            self.main_container,
            fg_color=self.card_bg,
            corner_radius=15,
            border_width=1,
            border_color=self.card_border
        )
        self.control_panel.grid(row=2, column=0, columnspan=12, sticky="ew", padx=20, pady=(0, 20))
        
        # Action buttons
        self.button_frame = ctk.CTkFrame(self.control_panel, fg_color="transparent")
        self.button_frame.pack(side="left", padx=20, pady=15)
        
        self.realtime_btn = ctk.CTkButton(
            self.button_frame,
            text="Chế độ Real-time",
            font=self.normal_font,
            fg_color=self.accent_color,
            hover_color="#388e3c",
            corner_radius=8,
            height=40,
            width=180,
            command=self.run_realtime
        )
        self.realtime_btn.pack(side="left", padx=(0, 10))
        
        self.upload_btn = ctk.CTkButton(
            self.button_frame,
            text="Tải Ảnh/Video",
            font=self.normal_font,
            fg_color=self.primary_color,
            hover_color=self.secondary_color,
            corner_radius=8,
            height=40,
            width=180,
            command=self.upload_file
        )
        self.upload_btn.pack(side="left", padx=10)
        
        self.export_btn = ctk.CTkButton(
            self.button_frame,
            text="Xuất Báo Cáo",
            font=self.normal_font,
            fg_color="#9e9e9e",
            hover_color="#757575",
            corner_radius=8,
            height=40,
            width=180,
            command=self.export_report
        )
        self.export_btn.pack(side="left", padx=10)
        
        # Right side with IP input
        self.settings_frame = ctk.CTkFrame(self.control_panel, fg_color="transparent")
        self.settings_frame.pack(side="right", padx=20, pady=15)
        
        self.ip_label = ctk.CTkLabel(
            self.settings_frame,
            text="IP DroidCam:",
            font=self.normal_font
        )
        self.ip_label.pack(side="left", padx=(0, 10))
        
        self.ip_entry = ctk.CTkEntry(
            self.settings_frame,
            width=250,
            height=40,
            font=self.normal_font,
            corner_radius=8,
            placeholder_text="http://192.168.1.5:4747/video"
        )
        self.ip_entry.insert(0, "http://192.168.1.5:4747/video")
        self.ip_entry.pack(side="left")

    def update_file_lists(self):
        """Update the image and video lists from directories"""
        # Clear current lists
        for item in self.image_treeview.get_children():
            self.image_treeview.delete(item)
        for item in self.video_treeview.get_children():
            self.video_treeview.delete(item)
        
        # Load images
        image_dir = "D:/hoc_may/License-Plate-Recognition/history_image"
        plate_history = {}
        
        # Read plate history from file
        if os.path.exists("D:/hoc_may/License-Plate-Recognition/plate_history.txt"):
            with open("D:/hoc_may/License-Plate-Recognition/plate_history.txt", "r", encoding="utf-8") as f:
                for line in f:
                    filename, plate = line.strip().split(",")
                    plate_history[filename] = plate
        
        image_count = 0
        for file in sorted(os.listdir(image_dir), reverse=True):
            if file.endswith('.jpg'):
                plate = plate_history.get(file, "Không xác định")
                self.image_treeview.insert("", "end", values=(file, plate), text=file)
                image_count += 1
        
        # Load videos
        video_dir = "D:/hoc_may/License-Plate-Recognition/history_video"
        video_count = 0
        
        for file in sorted(os.listdir(video_dir), reverse=True):
            if file.endswith('.mp4'):
                date_str = self.get_date_from_filename(file)
                duration = self.get_video_duration(os.path.join(video_dir, file))
                self.video_treeview.insert("", "end", values=(date_str, duration), text=file)
                video_count += 1
        
        # Update history count
        self.history_count.configure(text=str(image_count + video_count))

    def display_selected_file(self, event):
        """Display selected image or play selected video on canvas"""
        widget = event.widget
        selection = widget.selection()
        if not selection:
            return

        item_id = selection[0]
        file_name = widget.item(item_id, "text")
        
        if widget == self.image_treeview:
            file_path = os.path.join("D:/hoc_may/License-Plate-Recognition/history_image", file_name)
            self.display_image(file_path)
            
            # Update details
            values = widget.item(item_id, "values")
            self.plate_label.configure(text=values[1] if values[1] != "Không xác định" else "Không xác định")
            self.time_label.configure(text=f"Thời gian: {datetime.datetime.now().strftime('%H:%M:%S')}")
            self.confidence_label.configure(text="Độ chính xác: 95%")  # Placeholder
            
        elif widget == self.video_treeview:
            file_path = os.path.join("D:/hoc_may/License-Plate-Recognition/history_video", file_name)
            self.play_video(file_path)
            
            # Update details
            values = widget.item(item_id, "values")
            self.plate_label.configure(text="Xem video")
            self.time_label.configure(text=f"Thời gian: {values[0]}")
            self.confidence_label.configure(text=f"Thời lượng: {values[1]}")

    def display_image(self, file_path):
        """Display an image on the canvas with modern styling"""
        self.stop_video()  # Stop any playing video
        img = cv2.imread(file_path)
        if img is not None:
            self.update_canvas(img)
            self.status_indicator.configure(text="⬤ Hiển thị ảnh", text_color="#1e88e5")
        else:
            messagebox.showerror("Lỗi", "Không thể đọc hình ảnh")

    def play_video(self, file_path):
        """Play a video on the canvas with modern styling"""
        self.stop_video()  # Stop any playing video
        self.video_cap = cv2.VideoCapture(file_path)
        if not self.video_cap.isOpened():
            messagebox.showerror("Lỗi", "Không thể mở video")
            return

        self.is_video_playing = True
        self.status_indicator.configure(text="⬤ Đang phát video", text_color="#f57c00")

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
                self.status_indicator.configure(text="⬤ Kết thúc video", text_color="#757575")

        self.root.after(0, update_video)

    def stop_video(self):
        """Stop any playing video"""
        self.is_video_playing = False
        if self.video_cap is not None:
            self.video_cap.release()
            self.video_cap = None
        self.canvas.delete("all")
        self.status_indicator.configure(text="⬤ Sẵn sàng", text_color=self.accent_color)
        
    def update_canvas(self, frame):
        """Update canvas with new frame using modern styling"""
        if frame is not None:
            # Calculate dimensions to maintain aspect ratio
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            if canvas_width > 0 and canvas_height > 0:
                # Get image dimensions
                img_height, img_width = frame.shape[:2]
                
                # Calculate scaling factor to fit within canvas
                scale_width = canvas_width / img_width
                scale_height = canvas_height / img_height
                scale = min(scale_width, scale_height)
                
                # Calculate new dimensions
                new_width = int(img_width * scale)
                new_height = int(img_height * scale)
                
                # Resize the image
                frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image = Image.fromarray(frame)
                photo = ImageTk.PhotoImage(image=image)
                
                # Calculate position to center the image
                x_position = (canvas_width - new_width) // 2
                y_position = (canvas_height - new_height) // 2
                
                # Update canvas
                self.canvas.delete("all")
                self.canvas.create_image(x_position, y_position, anchor=tk.NW, image=photo)
                self.photo = photo  # Keep a reference to prevent garbage collection
    
    def run_realtime(self):
        """Run real-time detection with modern UI updates"""
        if self.is_realtime_running:
            return
            
        self.stop_video()  # Stop any playing video
        self.is_realtime_running = True
        cam_source = self.ip_entry.get()
        
        # Update UI to show processing state
        self.status_indicator.configure(text="⬤ Đang chạy real-time", text_color="#f44336")
        self.plate_label.configure(text="Đang xử lý...")
        self.canvas.delete("all")
        
        # Create loading indicator
        self.canvas.create_text(
            self.canvas.winfo_width() // 2, 
            self.canvas.winfo_height() // 2,
            text="Đang kết nối camera...",
            font=("Roboto", 16),
            fill="#757575"
        )
        
        # Run in a separate thread to avoid UI freezing
        def start_realtime_thread():
            try:
                self.realtime_generator = process_realtime(cam_source)
                self.root.after(100, self.update_realtime)
            except Exception as e:
                self.is_realtime_running = False
                self.status_indicator.configure(text="⬤ Lỗi kết nối", text_color="#f44336")
                messagebox.showerror("Lỗi", f"Không thể kết nối camera: {str(e)}")
        
        # Start thread
        threading.Thread(target=start_realtime_thread).start()
    
    def update_realtime(self):
        """Update UI with real-time detection results"""
        if not self.is_realtime_running:
            self.status_indicator.configure(text="⬤ Đã dừng real-time", text_color="#757575")
            self.update_file_lists()
            return
            
        try:
            captured_frame, current_plate = next(self.realtime_generator)
            if captured_frame is not None:
                self.update_canvas(captured_frame)
                
                # Update detection details
                if current_plate is not None:
                    self.plate_label.configure(text=current_plate)
                    
                    # Update time
                    current_time = datetime.datetime.now().strftime("%H:%M:%S")
                    self.time_label.configure(text=f"Thời gian: {current_time}")
                    
                    # Save image and plate number
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    output_filename = f"{current_plate}_{timestamp}.jpg"
                    output_path = os.path.join("D:/hoc_may/License-Plate-Recognition/history_image", output_filename)
                    cv2.imwrite(output_path, captured_frame)
                    
                    # Save plate number to history file
                    with open("D:/hoc_may/License-Plate-Recognition/plate_history.txt", "a", encoding="utf-8") as f:
                        f.write(f"{output_filename},{current_plate}\n")
                    
                    # Add to detection history
                    if current_plate not in self.detection_history:
                        self.detection_history.append(current_plate)
                        self.confidence_label.configure(text="Độ chính xác: 97%")  # Placeholder
                        
                        # Update lists after new detection
                        self.update_file_lists()
            
        except StopIteration:
            self.is_realtime_running = False
            self.status_indicator.configure(text="⬤ Kết thúc real-time", text_color="#757575")
            return
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi xử lý: {str(e)}")
            self.is_realtime_running = False
            self.status_indicator.configure(text="⬤ Lỗi xử lý", text_color="#f44336")
            return
            
        # Continue updating
        self.root.after(50, self.update_realtime)
    
    def upload_file(self):
        """Upload and process image or video file with modern UI updates"""
        self.stop_video()  # Stop any playing video
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
            
        self.canvas.delete("all")
        self.canvas.create_text(
            self.canvas.winfo_width() // 2, 
            self.canvas.winfo_height() // 2,
            text="Đang xử lý...",
            font=("Roboto", 16),
            fill="#757575"
        )
        self.root.update()
        
        if file_path.lower().endswith(('.jpg', '.jpeg', '.png')):
            # Process image
            self.status_indicator.configure(text="⬤ Đang xử lý ảnh", text_color="#fb8c00")
            
            # Use threading to avoid UI freeze
            def process_image_thread():
                try:
                    img, plates, captured_frame = process_image(file_path)
                    
                    # Update UI on main thread
                    def update_ui():
                        if img is not None:
                            self.update_canvas(img)
                            plate = next(iter(plates)) if plates else "Không tìm thấy biển số"
                            
                            # Save image and plate number
                            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                            output_filename = f"{plate}_{timestamp}.jpg"
                            output_path = os.path.join("D:/hoc_may/License-Plate-Recognition/history_image", output_filename)
                            cv2.imwrite(output_path, captured_frame)
                            
                            # Save plate number to history file
                            with open("D:/hoc_may/License-Plate-Recognition/plate_history.txt", "a", encoding="utf-8") as f:
                                f.write(f"{output_filename},{plate}\n")
                            
                            self.plate_label.configure(text=plate)
                            self.status_indicator.configure(text="⬤ Hoàn tất xử lý", text_color="#4caf50")
                            
                            # Update time with current time
                            self.time_label.configure(text=f"Thời gian: {datetime.datetime.now().strftime('%H:%M:%S')}")
                            
                            # Update confidence (placeholder)
                            self.confidence_label.configure(text="Độ chính xác: 96%")
                            
                            # Update lists
                            self.update_file_lists()
                        else:
                            messagebox.showerror("Lỗi", "Không thể đọc ảnh")
                            self.status_indicator.configure(text="⬤ Lỗi xử lý", text_color="#f44336")
                    
                    # Schedule UI update on main thread
                    self.root.after(0, update_ui)
                    
                except Exception as e:
                    def show_error():
                        messagebox.showerror("Lỗi", f"Lỗi xử lý ảnh: {str(e)}")
                        self.status_indicator.configure(text="⬤ Lỗi xử lý", text_color="#f44336")
                    
                    self.root.after(0, show_error)
            
            # Start processing thread
            threading.Thread(target=process_image_thread).start()
            
        elif file_path.lower().endswith('.mp4'):
            # Process video
            self.status_indicator.configure(text="⬤ Đang xử lý video", text_color="#fb8c00")
            
            # Use threading to avoid UI freeze
            def process_video_thread():
                try:
                    _, plates, _ = process_video(file_path)
                    
                    # Update UI on main thread
                    def update_ui():
                        plate = next(iter(plates)) if plates else "Không tìm thấy biển số"
                        self.plate_label.configure(text=plate)
                        self.status_indicator.configure(text="⬤ Hoàn tất xử lý", text_color="#4caf50")
                        
                        # Play the processed video
                        self.play_video(file_path)
                        
                        # Update time with current time
                        self.time_label.configure(text=f"Thời gian: {datetime.datetime.now().strftime('%H:%M:%S')}")
                        
                        # Update lists
                        self.update_file_lists()
                    
                    # Schedule UI update on main thread
                    self.root.after(0, update_ui)
                    
                except Exception as e:
                    def show_error():
                        messagebox.showerror("Lỗi", f"Lỗi xử lý video: {str(e)}")
                        self.status_indicator.configure(text="⬤ Lỗi xử lý", text_color="#f44336")
                    
                    self.root.after(0, show_error)
            
            # Start processing thread
            threading.Thread(target=process_video_thread).start()
    
    def export_report(self):
        """Export detection results to a report file"""
        # Get current date for filename
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
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("BÁO CÁO NHẬN DIỆN BIỂN SỐ XE\n")
                f.write("=" * 40 + "\n\n")
                f.write(f"Ngày xuất báo cáo: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")
                
                # Write image detections
                f.write("DANH SÁCH BIỂN SỐ NHẬN DIỆN TỪ HÌNH ẢNH:\n")
                f.write("-" * 40 + "\n")
                
                image_dir = "D:/hoc_may/License-Plate-Recognition/history_image"
                plate_history = {}
                if os.path.exists("D:/hoc_may/License-Plate-Recognition/plate_history.txt"):
                    with open("D:/hoc_may/License-Plate-Recognition/plate_history.txt", "r", encoding="utf-8") as pf:
                        for line in pf:
                            filename, plate = line.strip().split(",")
                            plate_history[filename] = plate
                
                for file in sorted(os.listdir(image_dir), reverse=True):
                    if file.endswith('.jpg'):
                        plate = plate_history.get(file, "Không xác định")
                        date_str = self.get_date_from_filename(file)
                        f.write(f"Tên file: {file}\n")
                        f.write(f"Biển số: {plate}\n")
                        f.write(f"Thời gian: {date_str}\n")
                        f.write("-" * 40 + "\n")
                
                # Write video detections
                f.write("\nDANH SÁCH BIỂN SỐ NHẬN DIỆN TỪ VIDEO:\n")
                f.write("-" * 40 + "\n")
                
                video_dir = "D:/hoc_may/License-Plate-Recognition/history_video"
                for file in sorted(os.listdir(video_dir), reverse=True):
                    if file.endswith('.mp4'):
                        date_str = self.get_date_from_filename(file)
                        duration = self.get_video_duration(os.path.join(video_dir, file))
                        f.write(f"Video: {file}\n")
                        f.write(f"Ngày: {date_str}\n")
                        f.write(f"Thời lượng: {duration}\n")
                        f.write("-" * 40 + "\n")
            
            messagebox.showinfo("Thành công", f"Đã xuất báo cáo thành công: {file_path}")
            
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể xuất báo cáo: {str(e)}")
    
    def destroy(self):
        """Clean up resources before closing"""
        self.stop_video()
        self.is_realtime_running = False
        self.root.destroy()

if __name__ == "__main__":
    # Initialize customtkinter
    ctk.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
    ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"
    
    root = ctk.CTk()
    app = ModernLicensePlateApp(root)
    root.protocol("WM_DELETE_WINDOW", app.destroy)  # Handle window close event
    root.mainloop()
