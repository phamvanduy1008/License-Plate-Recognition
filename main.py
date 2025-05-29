import customtkinter as ctk
from view.screen import LicensePlateView
from controller.controller import LicensePlateController
from app_utils.process import LicensePlateModel

if __name__ == "__main__":
    # Initialize customtkinter
    ctk.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
    ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"
    
    # Create the root window
    root = ctk.CTk()
    
    # Initialize MVC components
    model = LicensePlateModel()
    view = LicensePlateView(root)
    controller = LicensePlateController(model, view)
    
    # Start the main loop
    root.protocol("WM_DELETE_WINDOW", controller.on_closing)  # Handle window close event
    root.mainloop()