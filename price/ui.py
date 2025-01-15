import tkinter as tk
from tkinter import ttk
from threading import Thread
import cv2
from PIL import Image, ImageTk
import time

class ParkingManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Parking Management Interface")
        self.setup_ui()
        self.running = False

    def setup_ui(self):
        # Top Section: Unified Price Frame
        self.top_frame = ttk.Frame(self.root, relief=tk.SOLID, borderwidth=1)
        self.top_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        self.price_frames = {}
        for vehicle, data in prices.items():
            frame = ttk.Frame(self.top_frame)
            frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2, pady=2)
            ttk.Label(frame, text=f"{vehicle}", font=("Arial", 14, "bold"), foreground="black").pack(pady=2)
            ttk.Label(frame, text=f"{data['price']} $", font=("Arial", 16, "bold"), foreground="green").pack(pady=2)
            ttk.Label(frame, text=f"{data['space']}", font=("Arial", 13)).pack(pady=2)
            self.price_frames[vehicle] = frame

        # Bottom Section
        self.bottom_frame = ttk.Frame(self.root)
        self.bottom_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Bottom Left: Video Feed with fixed dimensions using tk.Label
        self.video_frame = tk.Label(self.bottom_frame, text="Video Feed", width=960, height=640)
        self.video_frame.pack(side=tk.LEFT)

        # Bottom Right: Info with stretching elements
        self.info_frame = ttk.Frame(self.bottom_frame)
        self.info_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)  # Fill both vertically and horizontally

        # Frames and Labels for Bottom Right
        self.create_info_box("Space\nleft:", f"{space_left} m²", "green")
        self.create_info_box("Estimate\nEOD:", f"{estimated_eod_profit} $", "green")
        self.create_info_box("Current\nprofit:", f"{current_profit} $", "green")
        self.create_info_box("FUTURE\nFEATURE", "", "black")

    def create_info_box(self, label_text, value_text, color):
        frame = ttk.Frame(self.info_frame)
        frame.pack(fill=tk.X, expand=True, padx=5, pady=5)  # Expand horizontally

        label = ttk.Label(frame, text=label_text, font=("Arial", 14), foreground="black", justify="center")
        label.pack(pady=(10, 2))  # Padding to bring text closer
        value = ttk.Label(frame, text=value_text, font=("Arial", 16, "bold"), foreground=color, justify="center")
        value.pack(pady=2)

    def start_video(self, path):
        self.running = True
        Thread(target=self.play_video, args=(path,), daemon=True).start()

    def play_video(self, path):
        cap = cv2.VideoCapture(path)

        while self.running:
            ret, frame = cap.read()
            if ret:
                frame = cv2.resize(frame, (960, 640))  # Adjusted to fixed height of 640
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = ImageTk.PhotoImage(Image.fromarray(frame))
                self.video_frame.config(image=img)
                self.video_frame.image = img
                time.sleep(0.03)  # Simulate ~30 FPS
            else:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Reset to the first frame if end is reached

        cap.release()

    def stop_video(self):
        self.running = False

if __name__ == "__main__":
    # Placeholder data
    prices = {
        "Car": {"price": 1.05, "space": "~ 3m²"},
        "Truck": {"price": 5.87, "space": "> 30m²"},
        "Van": {"price": 2.21, "space": "3-10m²"},
        "Bus": {"price": 3.50, "space": "10-30m²"}
    }

    space_left = 1000
    estimated_eod_profit = 12.547
    current_profit = 350.01
    video_path = "C:\\Users\\Laur\\Desktop\\Topici\\traffic.mp4"

    root = tk.Tk()
    root.geometry("1300x680")
    app = ParkingManagerApp(root)
    app.start_video(video_path)
    root.mainloop()
