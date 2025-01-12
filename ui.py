import tkinter as tk
from tkinter import filedialog
import cv2
from PIL import Image, ImageTk
import threading

# Initial parking lot setup
TOTAL_SLOTS = 10
available_slots = TOTAL_SLOTS
occupied_slots = 0

video_threads = {"left": None, "right": None}
paused = {"left": False, "right": False}
playing = {"left": False, "right": False}  # Flag to track if a video is playing

# Default video path
default_video_path = r"C:\Users\Laur\Desktop\Topici\video1_short.mp4"


def update_parking_status():
    global available_slots, occupied_slots
    available_label.config(text=f"{available_slots}", fg="green")
    occupied_label.config(text=f"{occupied_slots}", fg="red")
    if available_slots > 0:
        status_canvas.config(bg="green")
    else:
        status_canvas.config(bg="red")


def select_video(video_side):
    file_path = filedialog.askopenfilename(filetypes=[("Video Files", "*.mp4 *.avi")])
    if file_path:
        if video_threads[video_side] and video_threads[video_side].is_alive():
            # Stop any ongoing video playback before starting a new one
            paused[video_side] = True
        video_threads[video_side] = threading.Thread(
            target=play_video, args=(file_path, video_side)
        )
        video_threads[video_side].start()
        playing[video_side] = True  # Mark the video as playing


def toggle_pause(video_side):
    paused[video_side] = not paused[video_side]


def play_video(file_path, video_side):
    cap = cv2.VideoCapture(file_path)
    video_label = video_labels[video_side]

    while cap.isOpened():
        if not paused[video_side]:
            ret, frame = cap.read()
            if ret:
                # Resize frame to fit half the width if both videos are playing, or full width if only one is
                if playing["left"] and playing["right"]:
                    width = 800  # Half the screen width (1600px)
                else:
                    width = 1600  # Full screen width for a single video
                height = int((width / 1280) * 720)  # Maintain aspect ratio (16:9)

                # Resize frame based on the calculated dimensions
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = cv2.resize(frame, (width, height))
                img = ImageTk.PhotoImage(Image.fromarray(frame))
                video_label.config(image=img)
                video_label.image = img
            else:
                # Reset the video capture to loop the video
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        else:
            # Pause functionality: Keep showing the current frame
            cap.set(cv2.CAP_PROP_POS_FRAMES, cap.get(cv2.CAP_PROP_POS_FRAMES) - 1)
    cap.release()


# Initialize the main window
root = tk.Tk()
root.title("Parking Lot Vehicle Counting")
root.geometry("1600x900")
root.configure(bg="light gray")  # Set background color to light gray

# Top: Parking status
status_frame = tk.Frame(root, bg="light gray")
status_frame.pack(side=tk.TOP, pady=10)

available_label = tk.Label(status_frame, text=f"{available_slots}", font=("Arial", 20), fg="green", bg="light gray")
available_label.grid(row=0, column=0, padx=10)

status_canvas = tk.Canvas(status_frame, width=50, height=30, bg="green")
status_canvas.grid(row=0, column=1, padx=10)

occupied_label = tk.Label(status_frame, text=f"{occupied_slots}", font=("Arial", 20), fg="red", bg="light gray")
occupied_label.grid(row=0, column=2, padx=10)

# Horizontal line between top text and video sections
separator = tk.Frame(root, height=2, bg="black")
separator.pack(fill=tk.X, padx=5, pady=10)

# Video frame
video_frame = tk.Frame(root, bg="light gray")
video_frame.pack(fill=tk.BOTH, expand=True)

# Use grid to divide the video area into 2 equal sections (50% each)
left_video_frame = tk.Frame(video_frame, bg="light gray")
left_video_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=5)

right_video_frame = tk.Frame(video_frame, bg="light gray")
right_video_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=5)

# Make sure the columns expand equally
video_frame.grid_columnconfigure(0, weight=1)
video_frame.grid_columnconfigure(1, weight=1)

# Set video labels and buttons for both sides
tk.Label(left_video_frame, text="IN", font=("Arial", 16), bg="light gray").pack(pady=5)

video_labels = {
    "left": tk.Label(left_video_frame, bg="gray"),
    "right": tk.Label()
}
video_labels["left"].pack(fill=tk.BOTH, expand=True)

btn_frame_left = tk.Frame(left_video_frame, bg="light gray")
btn_frame_left.pack(pady=5)
tk.Button(btn_frame_left, text="Play IN Video", command=lambda: select_video("left")).grid(row=0, column=0, padx=5)
tk.Button(btn_frame_left, text="Pause/Play", command=lambda: toggle_pause("left")).grid(row=0, column=1, padx=5)

tk.Label(right_video_frame, text="OUT", font=("Arial", 16), bg="light gray").pack(pady=5)

video_labels["right"] = tk.Label(right_video_frame, bg="gray")
video_labels["right"].pack(fill=tk.BOTH, expand=True)

btn_frame_right = tk.Frame(right_video_frame, bg="light gray")
btn_frame_right.pack(pady=5)
tk.Button(btn_frame_right, text="Play OUT Video", command=lambda: select_video("right")).grid(row=0, column=0, padx=5)
tk.Button(btn_frame_right, text="Pause/Play", command=lambda: toggle_pause("right")).grid(row=0, column=1, padx=5)

# Add bottom margin space
bottom_margin = tk.Frame(root, height=50, bg="light gray")
bottom_margin.pack(fill=tk.X)

# Center the entire UI
root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)

# Set default videos on startup
playing["left"] = True
playing["right"] = True
video_threads["left"] = threading.Thread(target=play_video, args=(default_video_path, "left"))
video_threads["right"] = threading.Thread(target=play_video, args=(default_video_path, "right"))
video_threads["left"].start()
video_threads["right"].start()

# Start the main loop
update_parking_status()
root.mainloop()
