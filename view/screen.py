import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from PIL import Image, ImageTk
import cv2
import os
import datetime

class LicensePlateView:
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
        
        # Setup UI components
        self.create_main_layout()
        self.setup_header()
        self.setup_sidebar()
        self.setup_content_area()
        self.setup_control_panel()
        
        # Variables for UI state
        self.active_tab = "images"
        self.photo = None  # To prevent garbage collection of canvas images

    def create_main_layout(self):
        """Create the main application layout with modern grid system"""
        self.main_container = ctk.CTkFrame(self.root, fg_color=self.bg_color, corner_radius=0)
        self.main_container.pack(fill="both", expand=True, padx=0, pady=0)
        
        for i in range(12):
            self.main_container.columnconfigure(i, weight=1)
        
        self.main_container.rowconfigure(0, weight=0)  
        self.main_container.rowconfigure(1, weight=1)  
        self.main_container.rowconfigure(2, weight=0) 

    def setup_header(self):
        """Create the application header with logo and title"""
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
        )
        self.tab_images.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        self.tab_videos = ctk.CTkButton(
            self.tab_frame,
            text="Video",
            font=self.normal_font,
            fg_color="#e0e0e0",
            text_color=self.text_color,
            corner_radius=5,
        )
        self.tab_videos.pack(side="left", fill="x", expand=True, padx=(5, 0))
        
        # File lists with modern styling
        self.list_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        # Image list
        self.image_list_frame = ctk.CTkFrame(self.list_frame, fg_color="transparent")
        self.image_list_frame.pack(fill="both", expand=True)
        
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
        
        style.configure(
            "Treeview.Heading",
            background=self.bg_color,
            foreground=self.text_color,
            relief="flat",
            font=self.normal_font
        )
        
        self.image_scrollbar = ttk.Scrollbar(self.image_list_frame)
        self.image_scrollbar.pack(side="right", fill="y")
        
        self.image_treeview = ttk.Treeview(
            self.image_list_frame,
            columns=("filename", "plate"),
            show="headings",
            yscrollcommand=self.image_scrollbar.set
        )
        
        self.image_treeview.heading("filename", text="Tên File")
        self.image_treeview.heading("plate", text="Biển Số")
        self.image_treeview.column("filename", width=150)
        self.image_treeview.column("plate", width=100)
        
        self.image_treeview.pack(fill="both", expand=True)
        self.image_scrollbar.config(command=self.image_treeview.yview)
        
        # Video list (initially hidden)
        self.video_list_frame = ctk.CTkFrame(self.list_frame, fg_color="transparent")
        
        self.video_scrollbar = ttk.Scrollbar(self.video_list_frame)
        self.video_scrollbar.pack(side="right", fill="y")
        
        self.video_treeview = ttk.Treeview(
            self.video_list_frame,
            columns=("date", "duration"),
            show="headings",
            yscrollcommand=self.video_scrollbar.set
        )
        
        self.video_treeview.heading("date", text="Ngày")
        self.video_treeview.heading("duration", text="Thời lượng")
        self.video_treeview.column("date", width=100)
        self.video_treeview.column("duration", width=150)
        
        self.video_treeview.pack(fill="both", expand=True)
        self.video_scrollbar.config(command=self.video_treeview.yview)

    def setup_content_area(self):
        """Create the main content area with preview and details"""
        self.content_area = ctk.CTkFrame(
            self.main_container, 
            fg_color=self.bg_color,
            corner_radius=0
        )
        self.content_area.grid(row=1, column=3, columnspan=9, sticky="nsew", padx=(10, 20), pady=20)
        
        self.preview_card = ctk.CTkFrame(
            self.content_area, 
            fg_color=self.card_bg,
            corner_radius=15,
            border_width=1,
            border_color=self.card_border
        )
        self.preview_card.pack(fill="both", expand=True, padx=0, pady=0)
        
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
        
        self.canvas_frame = ctk.CTkFrame(self.preview_card, fg_color="#f0f0f0", corner_radius=10)
        self.canvas_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.canvas = tk.Canvas(
            self.canvas_frame,
            bg="#f0f0f0",
            bd=0,
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)
        
        self.results_frame = ctk.CTkFrame(self.preview_card, fg_color="transparent")
        self.results_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        self.plate_container = ctk.CTkFrame(
            self.results_frame,
            fg_color=self.bg_color,
            corner_radius=8,
            height=60
        )
        self.plate_container.pack(fill="x", pady=10)
        
        self.plate_icon = ctk.CTkLabel(
            self.plate_container,
            text="🚘",
            font=("Roboto", 22)
        )
        self.plate_icon.pack(side="left", padx=(15, 0))
        
        self.plate_label = ctk.CTkLabel(
            self.plate_container,
            text="Chưa có dữ liệu",
            font=("Roboto", 24, "bold")
        )
        self.plate_label.pack(side="left", padx=15)
        
        self.details_container = ctk.CTkFrame(self.results_frame, fg_color="transparent")
        self.details_container.pack(fill="x", pady=10)
        
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
        
        self.delete_frame = ctk.CTkFrame(
            self.details_container,
            fg_color=self.bg_color,
            corner_radius=8,
            height=40,
            width=200
        )
        self.delete_frame.pack(side="left", fill="y", expand=True, padx=(5, 0))
        
        self.delete_button = ctk.CTkButton(
            self.delete_frame,
            text="Xóa Lịch Sử",
            font=self.normal_font,
            fg_color="transparent",  
            text_color="#000000",
            corner_radius=8,
            height=40,
            width=120,
            command=self.on_delete_history  
        )
        self.delete_button.pack(side="left", padx=15)

    def setup_control_panel(self):
        """Create the control panel with action buttons and settings"""
        self.control_panel = ctk.CTkFrame(
            self.main_container,
            fg_color=self.card_bg,
            corner_radius=15,
            border_width=1,
            border_color=self.card_border
        )
        self.control_panel.grid(row=2, column=0, columnspan=12, sticky="ew", padx=20, pady=(0, 20))
        
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
        )
        self.export_btn.pack(side="left", padx=10)
        
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
        self.ip_entry.pack(side="left", padx=(0, 10))
        
        self.update_ip_btn = ctk.CTkButton(
            self.settings_frame,
            text="Cập Nhật IP",
            font=self.normal_font,
            fg_color=self.primary_color,
            hover_color=self.secondary_color,
            corner_radius=8,
            height=40,
            width=120,
        )
        self.update_ip_btn.pack(side="left")

    def update_canvas(self, frame):
        """Update canvas with new frame using modern styling"""
        if frame is not None:
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            if canvas_width > 0 and canvas_height > 0:
                img_height, img_width = frame.shape[:2]
                scale_width = canvas_width / img_width
                scale_height = canvas_height / img_height
                scale = min(scale_width, scale_height)
                new_width = int(img_width * scale)
                new_height = int(img_height * scale)
                frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image = Image.fromarray(frame)
                photo = ImageTk.PhotoImage(image=image)
                x_position = (canvas_width - new_width) // 2
                y_position = (canvas_height - new_height) // 2
                self.canvas.delete("all")
                self.canvas.create_image(x_position, y_position, anchor=tk.NW, image=photo)
                self.photo = photo  # Keep a reference to prevent garbage collection

    def update_file_lists(self, image_items, video_items, total_count):
        """Update the image and video lists in the UI"""
        for item in self.image_treeview.get_children():
            self.image_treeview.delete(item)
        for item in self.video_treeview.get_children():
            self.video_treeview.delete(item)
        
        for filename, plate in image_items:
            self.image_treeview.insert("", "end", values=(filename, plate), text=filename)
        
        for file, date_str, duration in video_items:
            self.video_treeview.insert("", "end", values=(date_str, duration), text=file)
        
        self.history_count.configure(text=str(total_count))

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

    def show_loading(self, message):
        """Show a loading message on the canvas"""
        self.canvas.delete("all")
        self.canvas.create_text(
            self.canvas.winfo_width() // 2, 
            self.canvas.winfo_height() // 2,
            text=message,
            font=("Roboto", 16),
            fill="#757575"
        )

    def update_status(self, message, color):
        """Update the status indicator"""
        self.status_indicator.configure(text=message, text_color=color)

    def update_plate_info(self, plate, time_str, confidence):
        """Update the plate detection info"""
        self.plate_label.configure(text=plate)
        self.time_label.configure(text=f"Thời gian: {time_str}")

    def on_delete_history(self):
        # Hàm này sẽ được gọi từ controller
        if hasattr(self, 'delete_history_handler'):
            self.delete_history_handler()
        else:
            messagebox.showerror("Lỗi", "Chưa chọn mục để xóa!")

    def set_delete_handler(self, handler):
        """Set the handler for delete history action"""
        self.delete_history_handler = handler