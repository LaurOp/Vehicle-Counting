import tkinter as tk
from tkinter import ttk
from threading import Thread
import cv2
from PIL import Image, ImageTk
import time
import price

class ParkingManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Parking Management Interface")
        self.setup_ui()
        self.running = False

        self.start_vehicle_counting()
        self.update_ui()  # Start periodic updates

    def setup_ui(self):
        # Top Section: Unified Price Frame
        self.top_frame = ttk.Frame(self.root, relief=tk.SOLID, borderwidth=1)
        self.top_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        self.price_frames = {}

        color = "green"
        if price.LIVE_PRICES['Car'] > 2:
            color = "orange"
        if price.LIVE_PRICES['Car'] > 3:
            color = "red"

        for vehicle, data in price.LIVE_PRICES.items():  # Use price module for initial prices
            frame = ttk.Frame(self.top_frame)
            frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2, pady=2)
            ttk.Label(frame, text=f"{vehicle}", font=("Arial", 14, "bold"), foreground="black").pack(pady=2)
            price_label = ttk.Label(frame, text=f"{data} $", font=("Arial", 16, "bold"), foreground=color)
            space_label = ttk.Label(frame, text=f"{prices[vehicle]['space']}", font=("Arial", 13), foreground="black")
            price_label.pack(pady=2)
            space_label.pack(pady=2)
            self.price_frames[vehicle] = price_label  # Store label for later updates

        # Bottom Section
        self.bottom_frame = ttk.Frame(self.root)
        self.bottom_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Bottom Left: Video Feed with fixed dimensions using tk.Label
        self.video_frame = tk.Label(self.bottom_frame, text="Video Feed", width=960, height=640)
        self.video_frame.pack(side=tk.LEFT)

        # Bottom Right: Info with stretching elements
        self.info_frame = ttk.Frame(self.bottom_frame)
        self.info_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Info labels for displaying dynamic data
        self.space_frame = ttk.Frame(self.info_frame)
        self.space_frame.pack(fill=tk.X, expand=True, padx=5, pady=5)  # Expand horizontally

        self.remaining_capacity_label = ttk.Label(self.space_frame, text="Space\nleft:", font=("Arial", 14), foreground="black", justify="center")
        self.remaining_capacity_label.pack(pady=(10, 2))  # Padding to bring text closer
        self.remaining_capacity_value = ttk.Label(self.space_frame, text="", font=("Arial", 16, "bold"), foreground="green", justify="center")
        self.remaining_capacity_value.pack(pady=2)


        self.profit_frame = ttk.Frame(self.info_frame)
        self.profit_frame.pack(fill=tk.X, expand=True, padx=5, pady=5)  # Expand horizontally

        self.profit_label = ttk.Label(self.profit_frame, text="Current\nProfit:", font=("Arial", 14), foreground="black", justify="center")
        self.profit_label.pack(pady=(10, 2))  # Padding to bring text closer
        self.profit_value = ttk.Label(self.profit_frame, text="", font=("Arial", 16, "bold"), foreground="green", justify="center")
        self.profit_value.pack(pady=2)


        self.eod_frame = ttk.Frame(self.info_frame)
        self.eod_frame.pack(fill=tk.X, expand=True, padx=5, pady=5)  # Expand horizontally

        self.estimated_daily_profit_label = ttk.Label(self.eod_frame, text="Estimate\nEOD:", font=("Arial", 14), foreground="black", justify="center")
        self.estimated_daily_profit_label.pack(pady=(10, 2))  # Padding to bring text closer
        self.estimated_daily_profit_value = ttk.Label(self.eod_frame, text="", font=("Arial", 16, "bold"), foreground="green", justify="center")
        self.estimated_daily_profit_value.pack(pady=20)


        self.latest_frame = ttk.Frame(self.info_frame)
        self.latest_frame.pack(fill=tk.X, expand=True, padx=5, pady=5)  # Expand horizontally

        self.latest_label = ttk.Label(self.eod_frame, text="", font=("Arial", 14), foreground="black", justify="center")
        self.latest_label.pack(pady=(45, 2))  # Padding to bring text closer
        self.latest_value = ttk.Label(self.eod_frame, text="", font=("Arial", 16, "bold"), foreground="green", justify="center")
        self.latest_value.pack(pady=5)

    def update_ui(self):
        """Update UI with current values from the backend."""

        # Calculate remaining capacity
        total_occupied = sum(
            price.parking_lot_state[vehicle] * price.VEHICLE_SIZES[vehicle] for vehicle in price.parking_lot_state)

        remaining_capacity = price.CURRENT_SPACE
        self.remaining_capacity_value.config(
            text=f"{remaining_capacity}m²")

        # Update ticket prices from backend
        current_prices = price.calculate_ticket_prices()  # Get updated prices from backend

        for vehicle in current_prices:
            self.price_frames[vehicle].config(text=f"{current_prices[vehicle]:.2f} $")  # Update ticket prices

        # Update profit value
        current_profit = price.total_session_profit  # Get current profit from backend
        self.profit_value.config(text=f"{current_profit:.2f}$")

        estimated_daily_profit = price.daily_profit_estimate  # Get estimated daily profit from backend
        self.estimated_daily_profit_value.config(text=f"{estimated_daily_profit:.2f}$")

        # Update the latest vehicle passed
        latest_vehicle = price.latest_vehicle
        if len(latest_vehicle) > 0:
            self.latest_label.config(text=f"Identified a {latest_vehicle}")

        latest_price = price.latest_ticket_paid
        if latest_price:
            self.latest_value.config(text=f"+ {latest_price:.2f}$")

        color = "green"
        if price.LIVE_PRICES['Car'] > 2:
            color = "orange"
        if price.LIVE_PRICES['Car'] > 3:
            color = "red"

        for vehicle in ['Car', 'Truck', 'Van', 'Bus']:
            self.price_frames[vehicle].config(foreground=color)

        # Schedule the next update after 500 milliseconds (0.5 seconds)
        self.root.after(500, self.update_ui)

    def count_vehicles(self):
        # Call the vehicle counting function from price.py
        video_path = "C:\\Users\\Laur\\Desktop\\Topici\\traffic.mp4"  # Example path
        line_position = 465  # Example line position
        interval = 90  # Example interval for VR images

        # Start a thread for counting vehicles to avoid blocking the UI
        Thread(target=self.run_counting, args=(video_path, line_position, interval), daemon=True).start()


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

    def start_vehicle_counting(self):
        video_path = "C:\\Users\\Laur\\Desktop\\Topici\\traffic.mp4"  # Example path
        line_position = 465  # Example line position
        interval = 90  # Example interval for VR images

        # Start a thread for counting vehicles to avoid blocking the UI
        Thread(target=self.run_counting, args=(video_path, line_position, interval), daemon=True).start()

    def run_counting(self, video_path, line_position, interval):
        print('Counting vehicles in the video and updating parking lot state...\n')

        # Call your main counting function from price.py here
        price.main(video_path=video_path,
                   line=line_position,
                   sec=interval,
                   saveVR=False,
                   saveVehicle=False,
                   loop=True)

if __name__ == "__main__":
    # Placeholder data
    prices = {
        "Car": {"price": price.LIVE_PRICES['Car'], "space": "~ 3m²"},
        "Truck": {"price": price.LIVE_PRICES['Truck'], "space": "> 30m²"},
        "Van": {"price": price.LIVE_PRICES['Van'], "space": "3-10m²"},
        "Bus": {"price": price.LIVE_PRICES['Bus'], "space": "10-30m²"}
    }

    space_left = price.PARKING_LOT_CAPACITY
    estimated_eod_profit = price.daily_profit_estimate
    current_profit = price.total_session_profit
    video_path = "C:\\Users\\Laur\\Desktop\\Topici\\traffic.mp4"

    root = tk.Tk()
    root.geometry("1300x680")
    app = ParkingManagerApp(root)
    app.start_video(video_path)
    root.mainloop()
