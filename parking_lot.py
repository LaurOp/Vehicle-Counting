import tkinter as tk
from tkinter import filedialog, simpledialog
import cv2
from PIL import Image, ImageTk
import threading
from ultralytics import YOLO
import numpy as np
import json

# Initial parking lot setup
TOTAL_SLOTS = None
AVAILABLE_SLOTS = None
OCCUPIED_SLOTS = None

DEFAULT_WIDTH = None
DEFAULT_HEIGHT = None
VIDEO_FRAME_PADDING = None

VIDEO_THREADS = {"left": None, "right": None}
PAUSED = {"left": False, "right": False}
PLAYING = {"left": False, "right": False}
START_VIDEO = {"left": None, "right": None}
VIDEO_PATHS = {"left": None, "right": None}
INFINITE_VIDEO_LOOP = {"left": None, "right": None}
MULTIPLE_VIDEOS_PATHS = {"left": [], "right": []}

AVAILABLE_LABEL = None
OCCUPIED_LABEL = None
STATUS_CANVAS = None
CANVAS = {"left": None, "right": None}
CAP = {"left": None, "right": None}
LEFT_SELECT_BUTTON = None
RIGHT_SELECT_BUTTON = None
LEFT_NEXT_BUTTON = None
RIGHT_NEXT_BUTTON = None
VIDEOS_INDEX = {"left": 0, "right": 0}

#region Paper Code

LINE_POSITION = {"left": None, "right": None}
INTERVAL_BETWEEN_VR_IMAGES = {"left": None, "right": None}
SAVE_VEHICLE = False

MODEL_MARK = YOLO('../Vehicle-Counting/YOLO/marks.pt')
MODEL_VEHICLE = YOLO('../Vehicle-Counting/YOLO/vehicle.pt')

def counting(VR, line, cap, ini, double, MODEL_MARK, MODEL_VEHICLE, saveVehicle, side):
    labels = ['Bus', 'Car', 'Motorbike', 'Pickup', 'Truck', 'Van', '???']
    count = np.array([0, 0, 0, 0, 0, 0, 0])
    duo = []
    infos = [['label', 'frame', 'conf', 'x0', 'y0', 'x1', 'y1']]
    delta = 120


    # detect marks
    marks = MODEL_MARK(VR, iou=0.05, conf=0.25, verbose=False)
    marks = marks[0].numpy()
    boxes = marks.boxes.xyxy
    print(f'Detected {len(boxes)} marks')


    # for each mark
    for box in boxes:
        x0, y0, x1, y1 = np.floor(box).astype(int)

        # save coordinates for the next VR
        if y1 >= len(VR) - 1:
            duo.append([x0, x1])
        # check marks in the previous VR
        elif y0 <= 1:
            mid = (x1 + x0) // 2
            if any(x1_ant <= mid <= x2_ant for x1_ant, x2_ant in double):
                continue


        # gets the corresponding frame
        frame = ini + (y0 + y1) // 2
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame)

        ret, img = cap.read()
        if ret == False:
            print('Frame not found  :(') # should never happen
            continue

        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))


        # detect vehicles
        vehicles = MODEL_VEHICLE(img, iou=0.5, conf=0.3, verbose=False)
        vehicles = vehicles[0].numpy()


        # extend the mark's x-coordinates
        a = max(x0 - delta, 0)
        b = min(x1 + delta, width)


        # find the vehicle associated with the mark
        dist_min = height
        crop = img
        classe = conf = -1
        for cls, xyxy, cnf in zip(vehicles.boxes.cls, vehicles.boxes.xyxy, vehicles.boxes.conf):
            x0, y0, x1, y1 = np.floor(xyxy).astype(int)
            mid_x = (x0 + x1) // 2

            if a < mid_x < b and y0 < line < y1:
                mid_y = (y0 + y1) // 2
                dist = abs(mid_y - line)
                if dist < dist_min:
                    dist_min = dist
                    classe = int(cls)
                    conf = cnf
                    if saveVehicle:
                        crop = img[y0:y1 , x0:x1]


        # update infos
        infos.append([labels[classe], frame, conf, x0, y0, x1, y1])

        if classe != -1:
            # update count
            count[classe] += 1

            # Increment UI slots
            update_parking_status(side)
        

        if classe == -1:
            print(f"Couldn't find the vehicle in frame {frame}!!!")
            print('VERIFY IT MANUALLY')

        if saveVehicle:
            name = f'vehicle-crops/{str(labels[classe])}{frame}.jpg'
            print(f'Saving as {name}')
            cv2.imwrite(name, crop)


    print('Count in this VR: ')
    # print_count(count)
    # print()

    return duo, count, infos

#endregion

#region Methods

def update_parking_status(side = None):
    global AVAILABLE_SLOTS, OCCUPIED_SLOTS, AVAILABLE_LABEL, OCCUPIED_LABEL, STATUS_CANVAS

    if side == "left" and AVAILABLE_SLOTS > 0:
        AVAILABLE_SLOTS -= 1
        OCCUPIED_SLOTS += 1

    if side == "right" and OCCUPIED_SLOTS > 0:
        AVAILABLE_SLOTS += 1
        OCCUPIED_SLOTS -= 1

    AVAILABLE_LABEL.config(text=f"{AVAILABLE_SLOTS}", fg="green")
    OCCUPIED_LABEL.config(text=f"{OCCUPIED_SLOTS}", fg="red")
    if AVAILABLE_SLOTS > 0:
        STATUS_CANVAS.config(bg="green")
    else:
        STATUS_CANVAS.config(bg="red")

def select_video(side, canvas):
    global VIDEO_PATHS, START_VIDEO, CAP, PLAYING, PAUSED, VIDEO_THREADS

    file_path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4;*.avi;*.mkv")])
    
    if file_path:
        VIDEO_PATHS[side] = file_path

        manage_video(side, canvas)

def next_video(side, canvas):
    global MULTIPLE_VIDEOS_PATHS, VIDEOS_INDEX, VIDEO_PATHS

    # Keep the index in the array boundaries
    VIDEOS_INDEX[side] = VIDEOS_INDEX[side] % len(MULTIPLE_VIDEOS_PATHS[side]) 
    print(VIDEOS_INDEX[side])
    VIDEO_PATHS[side] = MULTIPLE_VIDEOS_PATHS[side][VIDEOS_INDEX[side]]
    manage_video(side, canvas)

    VIDEOS_INDEX[side] += 1

def manage_video(side, canvas):
    global VIDEO_PATHS, START_VIDEO, CAP, PLAYING, PAUSED, VIDEO_THREADS
    
    try:
        if VIDEO_PATHS[side]:
            if VIDEO_THREADS[side] is not None:
                print("Entered critical zone")
                VIDEO_THREADS[side].stop_event.set()
                VIDEO_THREADS[side].join()

            if CAP[side] is not None:
                CAP[side].release()
                CAP[side] = None

            CAP[side] = cv2.VideoCapture(VIDEO_PATHS[side])

            show_first_frame(side, canvas)

            if (START_VIDEO[side]):
                play_pause_video(side, canvas)
    except FileNotFoundError as s:
        print(f"File not found exception: {s}")

def show_first_frame(side, canvas):
    global VIDEO_PATHS
    if VIDEO_PATHS[side]:
        cap = cv2.VideoCapture(VIDEO_PATHS[side])
        ret, frame = cap.read()
        if ret:
            resize_frame(canvas, frame)

        cap.release()

def play_pause_video(side, canvas):
    global PAUSED, PLAYING, VIDEO_THREADS, LEFT_SELECT_BUTTON, RIGHT_SELECT_BUTTON
    global LEFT_NEXT_BUTTON, RIGHT_NEXT_BUTTON

    if PLAYING[side]:
        PAUSED[side] = not PAUSED[side]
    else:
        PLAYING[side] = True
        stop_event = threading.Event()
        VIDEO_THREADS[side] = VideoThread(stop_event, side, canvas)
        VIDEO_THREADS[side].start()
    
    # Disable select button if the video is not paused - the threads are tweakin'
    if side == "left" and LEFT_SELECT_BUTTON:
        LEFT_SELECT_BUTTON.config(state="disabled" if not PAUSED[side] else "normal")
    elif side == "right" and RIGHT_SELECT_BUTTON:
        RIGHT_SELECT_BUTTON.config(state="disabled" if not PAUSED[side] else "normal")

    if side == "left" and LEFT_NEXT_BUTTON:
        LEFT_NEXT_BUTTON.config(state="disabled" if not PAUSED[side] else "normal")
    elif side == "right" and RIGHT_NEXT_BUTTON:
        RIGHT_NEXT_BUTTON.config(state="disabled" if not PAUSED[side] else "normal")

class VideoThread(threading.Thread):
    def __init__(self, stop_event, side, canvas):
        super().__init__()
        self.stop_event = stop_event
        self.side = side
        self.canvas = canvas

    def run(self):
        play_video(self.side, self.canvas, self.stop_event)

def play_video(side, canvas, stop_event):
    global PAUSED, PLAYING, VIDEO_PATHS, LINE_POSITION, INTERVAL_BETWEEN_VR_IMAGES, INFINITE_VIDEO_LOOP, CAP

    try:
        if CAP[side] is None:
            CAP[side] = cv2.VideoCapture(VIDEO_PATHS[side])
        
        print(VIDEO_THREADS[side].ident)

        #region Paper Code
        ini = 0     # current VR initial frame
        double = [] # marks on the border of the previous VR
        infos = []  # details of each vehicle
        VR = []     # VR image
        count = np.array([0, 0, 0, 0, 0, 0, 0]) # count of each class
        #endregion

        while CAP[side].isOpened() and PLAYING[side]:
            if stop_event.is_set():  # Check if stop event is set
                print(f"Thread {threading.current_thread().ident} has been stopped.")
                break

            if not PAUSED[side]:
                ret, frame = CAP[side].read()
                if not ret:
                    if not INFINITE_VIDEO_LOOP[side]:
                        break

                    # If the video has ended, reset to the beginning
                    CAP[side].set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ini = 0
                    double = []
                    infos = []
                    continue

                #region Paper Code
                
                VR.append(frame[LINE_POSITION[side]])

                if (len(VR)) == INTERVAL_BETWEEN_VR_IMAGES[side]:
                    double, cnt, inf = counting(np.array(VR),
                                                LINE_POSITION[side],
                                                CAP[side],
                                                ini,
                                                double,
                                                MODEL_MARK,
                                                MODEL_VEHICLE,
                                                SAVE_VEHICLE,
                                                side)

                    infos += inf

                    VR = []
                    ini += INTERVAL_BETWEEN_VR_IMAGES[side]
                    CAP[side].set(cv2.CAP_PROP_POS_FRAMES, ini)

                #endregion

                resize_frame(canvas, frame)

            # Small delay to mimic video frame rate
            cv2.waitKey(10)

        #region Paper Code

        if not stop_event.is_set() and len(VR) > 0:
            _, cnt, inf = counting(np.array(VR),
                                LINE_POSITION[side],
                                CAP[side],
                                ini,
                                double,
                                MODEL_MARK,
                                MODEL_VEHICLE,
                                SAVE_VEHICLE,
                                side)

        #endregion
        
    except Exception as e:
        print(f"Exception in thread {VIDEO_THREADS[side].ident}: {e}")
        PLAYING[side] = False
        PAUSED[side] = False

    finally:
        if CAP[side]:
            CAP[side].release()
        PLAYING[side] = False
        PAUSED[side] = False
        print(f"Thread {VIDEO_THREADS[side].ident} has finished.")

def resize_frame(canvas, frame):
    height, width, _ = frame.shape

    canvas_width = canvas.winfo_width()
    canvas_height = canvas.winfo_height()

    aspect_ratio = width / height

    if width > height:
        new_width = canvas_width - VIDEO_FRAME_PADDING # Keep a padding
        new_height = int(new_width / aspect_ratio)
    else:
        new_height = canvas_height - VIDEO_FRAME_PADDING 
        new_width = int(new_height * aspect_ratio)

    frame = cv2.resize(frame, (new_width, new_height))

    # Convert the frame to ImageTk
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = ImageTk.PhotoImage(Image.fromarray(frame))

    # Set the anchor points based on the new size
    anchorX = (canvas_width - new_width) / 2 
    anchorY = (canvas_height - new_height) / 2

    # Update the canvas with the new frame
    canvas.create_image(anchorX, anchorY, anchor=tk.NW, image=img)
    canvas.image = img

def set_total_slots(root):
    global TOTAL_SLOTS, AVAILABLE_SLOTS, OCCUPIED_SLOTS
    new_total_slots = simpledialog.askinteger("Set Parking Lot Slots", "Enter total number of slots:", initialvalue=TOTAL_SLOTS, parent=root, minvalue=1)
    if new_total_slots is not None:
        TOTAL_SLOTS = new_total_slots
        AVAILABLE_SLOTS = TOTAL_SLOTS - OCCUPIED_SLOTS
        update_parking_status()

def set_line_position(root, side):
    global LINE_POSITION
    new_line_position = simpledialog.askinteger("Set Line Position", "Enter line position", 
                                                initialvalue=LINE_POSITION[side], 
                                                parent=root, 
                                                minvalue=0)
    if new_line_position is not None:
        LINE_POSITION[side] = new_line_position

def set_vr_interval(root, side):
    global INTERVAL_BETWEEN_VR_IMAGES
    new_VR_interval = simpledialog.askinteger("Set VR Interval", "Enter interval between VR images", 
                                              initialvalue=INTERVAL_BETWEEN_VR_IMAGES[side], 
                                              parent=root, 
                                              minvalue=0)
    if new_VR_interval is not None:
        INTERVAL_BETWEEN_VR_IMAGES[side] = new_VR_interval

def set_start_video(root, side):
    global START_VIDEO
    user_input = simpledialog.askstring(
        "Set Start Video", 
        f"Start {side} video as soon as the app starts (True or False)", 
        initialvalue=START_VIDEO[side], 
        parent=root)
    
    if user_input is not None: 
        if user_input.lower() in ["true", "false"]:
            START_VIDEO[side] = user_input.lower() == "true"
        else:
            print("Invalid input. Please enter 'True' or 'False'.")

def set_infinite_loop(root, side):
    user_input = simpledialog.askstring(
        "Set Infinite Loop",
        f"Set {side} video to play in a loop (True or False)",
        initialvalue=str(INFINITE_VIDEO_LOOP[side]),
        parent=root
    )
    
    if user_input is not None: 
        if user_input.lower() in ["true", "false"]:
            INFINITE_VIDEO_LOOP[side] = user_input.lower() == "true"
        else:
            print("Invalid input. Please enter 'True' or 'False'.")

def append_video(side):
    global MULTIPLE_VIDEOS_PATHS

    file_path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4;*.avi;*.mkv")])
    if file_path:
        MULTIPLE_VIDEOS_PATHS[side].append(file_path)

def set_default_video(side):
    global VIDEO_PATHS

    file_path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4;*.avi;*.mkv")])
    if file_path:
        VIDEO_PATHS[side] = file_path
        show_first_frame(side, CANVAS[side])

def load_configuration():
    # GLOBAL
    global TOTAL_SLOTS, AVAILABLE_SLOTS, OCCUPIED_SLOTS, PLAYING, MULTIPLE_VIDEOS_PATHS
    global LINE_POSITION, INTERVAL_BETWEEN_VR_IMAGES, INFINITE_VIDEO_LOOP
    global START_VIDEO, VIDEO_PATHS, DEFAULT_WIDTH, DEFAULT_HEIGHT, VIDEO_FRAME_PADDING
    
    def retrieveKeyValue(array, key_name):
        if key_name in array:
            return array[key_name]
            
        return None

    with open("config.json") as r:
        config = json.load(r)
        
        general = config["general"]
        left = config["left"]
        right = config["right"]

        # GENERAL
        TOTAL_SLOTS = retrieveKeyValue(general, "totalSlots")
        AVAILABLE_SLOTS = TOTAL_SLOTS
        OCCUPIED_SLOTS = TOTAL_SLOTS - AVAILABLE_SLOTS
        DEFAULT_WIDTH = retrieveKeyValue(general, "width")
        DEFAULT_HEIGHT = retrieveKeyValue(general, "height")
        VIDEO_FRAME_PADDING = retrieveKeyValue(general, "framePadding")

        # LEFT
        LINE_POSITION["left"] = retrieveKeyValue(left, "linePosition")
        INTERVAL_BETWEEN_VR_IMAGES["left"] = retrieveKeyValue(left, "VRInterval")
        START_VIDEO["left"] = retrieveKeyValue(left, "startVideo")
        VIDEO_PATHS["left"] = retrieveKeyValue(left, "videoPath")
        INFINITE_VIDEO_LOOP["left"] = retrieveKeyValue(left, "infiniteVideoLoop")
        MULTIPLE_VIDEOS_PATHS["left"] = retrieveKeyValue(left, "nextVideos")

        # RIGHT
        LINE_POSITION["right"] = retrieveKeyValue(right, "linePosition")
        INTERVAL_BETWEEN_VR_IMAGES["right"] = retrieveKeyValue(right, "VRInterval")
        START_VIDEO["right"] = retrieveKeyValue(right, "startVideo")
        VIDEO_PATHS["right"] = retrieveKeyValue(right, "videoPath")
        INFINITE_VIDEO_LOOP["right"] = retrieveKeyValue(right, "infiniteVideoLoop")
        MULTIPLE_VIDEOS_PATHS["right"] = retrieveKeyValue(right, "nextVideos")

def save_configuration():
    global TOTAL_SLOTS, DEFAULT_WIDTH, DEFAULT_HEIGHT, VIDEO_FRAME_PADDING
    global VIDEO_PATHS, LINE_POSITION, INTERVAL_BETWEEN_VR_IMAGES, START_VIDEO, INFINITE_VIDEO_LOOP, MULTIPLE_VIDEOS_PATHS

    data = {
        "general":{
            "totalSlots": TOTAL_SLOTS,
            "width": DEFAULT_WIDTH,
            "height": DEFAULT_HEIGHT,
            "framePadding": VIDEO_FRAME_PADDING
        },
        "left": {
            "videoPath": VIDEO_PATHS["left"],
            "linePosition": LINE_POSITION["left"],
            "VRInterval": INTERVAL_BETWEEN_VR_IMAGES["left"],
            "startVideo": START_VIDEO["left"],
            "infiniteVideoLoop": INFINITE_VIDEO_LOOP["left"],
            "nextVideos": MULTIPLE_VIDEOS_PATHS["left"]
        },
        "right": {
            "videoPath": VIDEO_PATHS["right"],
            "linePosition": LINE_POSITION["right"],
            "VRInterval": INTERVAL_BETWEEN_VR_IMAGES["right"],
            "startVideo": START_VIDEO["right"],
            "infiniteVideoLoop": INFINITE_VIDEO_LOOP["right"],
            "nextVideos": MULTIPLE_VIDEOS_PATHS["right"]
        }
    }
    
    with open("config.json", "w") as write:
        json.dump(data, write)

def play_default_videos(side, canvas):
    global START_VIDEO

    show_first_frame(side, canvas)
    if (START_VIDEO[side]):
        play_pause_video(side, canvas)

#endregion

def application():
    global AVAILABLE_LABEL, OCCUPIED_LABEL, STATUS_CANVAS, CANVAS, PAUSED, LEFT_SELECT_BUTTON, RIGHT_SELECT_BUTTON, START_VIDEO
    global LEFT_NEXT_BUTTON, RIGHT_NEXT_BUTTON

    # Initialize the main window
    root = tk.Tk()
    root.title("Parking Lot Vehicle Counting")
    root.geometry(f"{DEFAULT_WIDTH}x{DEFAULT_HEIGHT}")
    root.configure(bg="light gray")

    #region Menu
    menu_bar = tk.Menu(root)

    # Configuration
    configuration_menu = tk.Menu(menu_bar, tearoff=0)
    configuration_menu.add_command(label="Load Configuration (from config.json)", command=lambda: load_configuration()) 
    configuration_menu.add_command(label="Save Current Configuration (to config.json)", command=lambda: save_configuration()) 
    
    # General Variables
    variables_menu = tk.Menu(menu_bar, tearoff=0)
    variables_menu.add_command(label="Set Total Slots", command=lambda: set_total_slots(root))
    
    # Left Variables
    left_variables_menu = tk.Menu(menu_bar, tearoff=0)
    left_variables_menu.add_command(label="Set Default Video (left)", command=lambda: set_default_video("left"))
    left_variables_menu.add_command(label="Set Line Position (left)", command=lambda: set_line_position(root, "left"))
    left_variables_menu.add_command(label="Set Interval Between VR Images (left)", command=lambda: set_vr_interval(root, "left"))
    left_variables_menu.add_command(label="Set Start Video (left)", command=lambda: set_start_video(root, "left"))
    left_variables_menu.add_command(label="Set Infinite Loop (left)", command=lambda: set_infinite_loop(root, "left"))
    left_variables_menu.add_command(label="Add New Video (left)", command=lambda: append_video("left"))

    # right Variables
    right_variables_menu = tk.Menu(menu_bar, tearoff=0)
    right_variables_menu.add_command(label="Set Default Video (right)", command=lambda: set_default_video("right"))
    right_variables_menu.add_command(label="Set Line Position (right)", command=lambda: set_line_position(root, "right"))
    right_variables_menu.add_command(label="Set Interval Between VR Images (right)", command=lambda: set_vr_interval(root, "right"))
    right_variables_menu.add_command(label="Set Start Video (right)", command=lambda: set_start_video(root, "right"))
    right_variables_menu.add_command(label="Set Infinite Loop (right)", command=lambda: set_infinite_loop(root, "right"))
    right_variables_menu.add_command(label="Add New Video (right)", command=lambda: append_video("right"))
    
    # Reset
    reset_menu = tk.Menu(menu_bar, tearoff=0)
    reset_menu.add_command(label="Revert Changes", command=load_configuration)

    # Add menus to the menu bar
    menu_bar.add_cascade(label="Configuration", menu=configuration_menu)
    menu_bar.add_cascade(label="General Variables", menu=variables_menu)
    menu_bar.add_cascade(label="Left Video Variables", menu=left_variables_menu)
    menu_bar.add_cascade(label="Right Video Variables", menu=right_variables_menu)
    menu_bar.add_cascade(label="Reset", menu=reset_menu)

    # Set the menu bar to the window
    root.config(menu=menu_bar)

    #endregion

    # Top: Parking status
    status_frame = tk.Frame(root, bg="light gray")
    status_frame.pack(side=tk.TOP, pady=10)

    AVAILABLE_LABEL = tk.Label(status_frame, text=f"{AVAILABLE_SLOTS}", font=("Arial", 20), fg="green", bg="light gray")
    AVAILABLE_LABEL.grid(row=0, column=0, padx=10)

    STATUS_CANVAS = tk.Canvas(status_frame, width=50, height=30, bg="green")
    STATUS_CANVAS.grid(row=0, column=1, padx=10)

    OCCUPIED_LABEL = tk.Label(status_frame, text=f"{OCCUPIED_SLOTS}", font=("Arial", 20), fg="red", bg="light gray")
    OCCUPIED_LABEL.grid(row=0, column=2, padx=10)

    # Horizontal line between top text and video sections
    separator = tk.Frame(root, height=2, bg="black")
    separator.pack(fill=tk.X, padx=10, pady=10)

    # Video frame
    video_frame = tk.Frame(root, bg="light gray")
    video_frame.pack(fill=tk.BOTH, expand=True)

    left_video_frame = tk.Frame(video_frame, bg="light gray")
    left_video_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=5)
    tk.Label(left_video_frame, text="Entering Gate", font=("Arial", 14), bg="light gray").pack(pady=5)

    right_video_frame = tk.Frame(video_frame, bg="light gray")
    right_video_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=5)
    tk.Label(right_video_frame, text="Exit Gate", font=("Arial", 14), bg="light gray").pack(pady=5)

    # Left video section
    CANVAS["left"] = tk.Canvas(left_video_frame, bg="dark gray", width=DEFAULT_WIDTH//2, height=DEFAULT_HEIGHT//2)
    CANVAS["left"].pack(fill=tk.BOTH, expand=True)

    left_buttons_frame = tk.Frame(left_video_frame, bg="light gray")
    left_buttons_frame.pack(fill=tk.X, pady=5)

    LEFT_SELECT_BUTTON = tk.Button(left_buttons_frame, text="Select Camera", command=lambda: select_video("left", CANVAS["left"]))
    LEFT_SELECT_BUTTON.pack(side=tk.LEFT, padx=10)
    LEFT_SELECT_BUTTON.config(state="disabled" if START_VIDEO["left"] else "normal")

    LEFT_NEXT_BUTTON = tk.Button(left_buttons_frame, text="Switch Camera", command=lambda: next_video("left", CANVAS["left"]))
    LEFT_NEXT_BUTTON.pack(side=tk.RIGHT, padx=10)
    LEFT_NEXT_BUTTON.config(state="disabled" if START_VIDEO["left"] else "normal")
    
    left_play_button = tk.Button(left_buttons_frame, text="Play/Pause", command=lambda: play_pause_video("left", CANVAS["left"]))
    left_play_button.pack(side=tk.RIGHT, padx=10)

    # Right video section
    CANVAS["right"] = tk.Canvas(right_video_frame, bg="dark gray", width=DEFAULT_WIDTH//2, height=DEFAULT_HEIGHT//2)
    CANVAS["right"].pack(fill=tk.BOTH, expand=True)

    right_buttons_frame = tk.Frame(right_video_frame, bg="light gray")
    right_buttons_frame.pack(fill=tk.X, pady=5)

    RIGHT_SELECT_BUTTON = tk.Button(right_buttons_frame, text="Select Camera", command=lambda: select_video("right", CANVAS["right"]))
    RIGHT_SELECT_BUTTON.pack(side=tk.LEFT, padx=10)
    RIGHT_SELECT_BUTTON.config(state="disabled" if START_VIDEO["right"] else "normal")

    RIGHT_NEXT_BUTTON = tk.Button(right_buttons_frame, text="Switch Camera", command=lambda: next_video("right", CANVAS["right"]))
    RIGHT_NEXT_BUTTON.pack(side=tk.RIGHT, padx=10)
    RIGHT_NEXT_BUTTON.config(state="disabled" if START_VIDEO["right"] else "normal")
    
    right_play_button = tk.Button(right_buttons_frame, text="Play/Pause", command=lambda: play_pause_video("right", CANVAS["right"]))
    right_play_button.pack(side=tk.RIGHT, padx=10)

    root.after(100, lambda: play_default_videos("left", CANVAS["left"]))
    root.after(100, lambda: play_default_videos("right", CANVAS["right"]))
    root.after(100, lambda: update_parking_status())

    # Start the main loop
    root.mainloop()

if __name__ == "__main__":
    load_configuration()
    application()