import tkinter as tk
from tkinter import filedialog, simpledialog
import cv2
from PIL import Image, ImageTk
import threading
from ultralytics import YOLO
import numpy as np
# from count import counting

# Initial parking lot setup
TOTAL_SLOTS = 50
AVAILABLE_SLOTS = TOTAL_SLOTS
OCCUPIED_SLOTS = TOTAL_SLOTS - AVAILABLE_SLOTS

DEFAULT_WIDTH = 1280
DEFAULT_HEIGHT = 720
VIDEO_FRAME_PADDING = 15

video_threads = {"left": None, "right": None}
paused = {"left": False, "right": False}
playing = {"left": False, "right": False}
video_paths = {"left": None, "right": None}

#region Paper Code

LINE_POSITION = 600
INTERVAL_BETWEEN_VR_IMAGES = 900
SAVE_VEHICLE = False

def counting(VR, line, cap, ini, double, model_mark, model_vehicle, saveVehicle, side):
    labels = ['Bus', 'Car', 'Motorbike', 'Pickup', 'Truck', 'Van', '???']
    count = np.array([0, 0, 0, 0, 0, 0, 0])
    duo = []
    infos = [['label', 'frame', 'conf', 'x0', 'y0', 'x1', 'y1']]
    delta = 120


    # detect marks
    marks = model_mark(VR, iou=0.05, conf=0.25, verbose=False)
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
        vehicles = model_vehicle(img, iou=0.5, conf=0.3, verbose=False)
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
    global AVAILABLE_SLOTS, OCCUPIED_SLOTS

    if side == "left" and AVAILABLE_SLOTS > 0:
        AVAILABLE_SLOTS -= 1
        OCCUPIED_SLOTS += 1

    if side == "right" and OCCUPIED_SLOTS > 0:
        AVAILABLE_SLOTS += 1
        OCCUPIED_SLOTS -= 1

    available_label.config(text=f"{AVAILABLE_SLOTS}", fg="green")
    occupied_label.config(text=f"{OCCUPIED_SLOTS}", fg="red")
    if AVAILABLE_SLOTS > 0:
        status_canvas.config(bg="green")
    else:
        status_canvas.config(bg="red")

def select_video(side, canvas):
    global video_paths
    file_path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4;*.avi;*.mkv")])
    if file_path:
        video_paths[side] = file_path
        show_first_frame(side, canvas)

def show_first_frame(side, canvas):
    global video_paths
    if video_paths[side]:
        cap = cv2.VideoCapture(video_paths[side])
        ret, frame = cap.read()
        if ret:
            
            resize_frame(canvas, frame)

        cap.release()

def play_pause_video(side, canvas):
    global paused, playing, video_threads
    if playing[side]:
        paused[side] = not paused[side]
    else:
        playing[side] = True
        video_threads[side] = threading.Thread(target=play_video, args=(side, canvas))
        video_threads[side].start()

def play_video(side, canvas):
    global paused, playing, video_paths
    cap = cv2.VideoCapture(video_paths[side])

    #region Paper Code
    ini = 0     # current VR initial frame
    double = [] # marks on the border of the previous VR
    infos = []  # details of each vehicle
    VR = []     # VR image
    count = np.array([0, 0, 0, 0, 0, 0, 0]) # count of each class
    #endregion

    while cap.isOpened() and playing[side]:
        if not paused[side]:
            ret, frame = cap.read()
            if not ret:
                break

            #region Paper Code
            
            VR.append(frame[LINE_POSITION])

            if (len(VR)) == INTERVAL_BETWEEN_VR_IMAGES:
                print("IM IN")
                double, cnt, inf = counting(np.array(VR),
                                            LINE_POSITION,
                                            cap,
                                            ini,
                                            double,
                                            model_mark,
                                            model_vehicle,
                                            SAVE_VEHICLE,
                                            side)

                infos += inf

                VR = []
                ini += INTERVAL_BETWEEN_VR_IMAGES
                cap.set(cv2.CAP_PROP_POS_FRAMES, ini)

            #endregion

            resize_frame(canvas, frame)

        # Small delay to mimic video frame rate
        cv2.waitKey(10)

    #region Paper Code

    if len(VR) > 0:
        _, cnt, inf = counting(np.array(VR),
                               LINE_POSITION,
                               cap,
                               ini,
                               double,
                               model_mark,
                               model_vehicle,
                               SAVE_VEHICLE,
                               side)

    #endregion

    cap.release()
    playing[side] = False
    paused[side] = False

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

    # Convert the frame to an ImageTk-compatible format
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = ImageTk.PhotoImage(Image.fromarray(frame))

    # Set the anchor points based on the new size
    anchorX = (canvas_width - new_width) / 2 
    anchorY = (canvas_height - new_height) / 2

    # Update the canvas with the new frame
    canvas.create_image(anchorX, anchorY, anchor=tk.NW, image=img)
    canvas.image = img

def set_total_slots():
    global TOTAL_SLOTS, AVAILABLE_SLOTS, OCCUPIED_SLOTS
    new_total_slots = simpledialog.askinteger("Set Parking Lot Slots", "Enter total number of slots:", initialvalue=TOTAL_SLOTS, parent=root, minvalue=1)
    if new_total_slots is not None:
        TOTAL_SLOTS = new_total_slots
        AVAILABLE_SLOTS = TOTAL_SLOTS - OCCUPIED_SLOTS
        update_parking_status()

def set_line_position():
    global LINE_POSITION
    new_line_position = simpledialog.askinteger("Set Line Position", "Enter line position", initialvalue=LINE_POSITION, parent=root, minvalue=0)
    if new_line_position is not None:
        LINE_POSITION = new_line_position

def set_vr_interval():
    global INTERVAL_BETWEEN_VR_IMAGES
    new_VR_interval = simpledialog.askinteger("Set VR Interval", "Enter interval between VR images", initialvalue=INTERVAL_BETWEEN_VR_IMAGES, parent=root, minvalue=0)
    if new_VR_interval is not None:
        INTERVAL_BETWEEN_VR_IMAGES = new_VR_interval

def reset():
    # Reset parking variables
    global TOTAL_SLOTS, AVAILABLE_SLOTS, OCCUPIED_SLOTS

    TOTAL_SLOTS = 50
    AVAILABLE_SLOTS = TOTAL_SLOTS
    OCCUPIED_SLOTS = TOTAL_SLOTS - AVAILABLE_SLOTS

    update_parking_status()

    # Reset states
    global video_threads, paused, playing, video_paths

    video_threads = {"left": None, "right": None}
    paused = {"left": False, "right": False}
    playing = {"left": False, "right": False}
    
    # Instead of resetting the video paths, we reload the videos again 
    if (video_paths["left"]):
        show_first_frame("left", left_canvas)

    if (video_paths["right"]):
        show_first_frame("right", right_canvas)

    # Reset Paper Variables
    global LINE_POSITION, INTERVAL_BETWEEN_VR_IMAGES, SAVE_VEHICLE

    LINE_POSITION = 600
    INTERVAL_BETWEEN_VR_IMAGES = 900
    SAVE_VEHICLE = False

#endregion

#region Paper Code

model_mark = YOLO('../Vehicle-Counting/YOLO/marks.pt')
model_vehicle = YOLO('../Vehicle-Counting/YOLO/vehicle.pt')

#endregion

# Initialize the main window
root = tk.Tk()
root.title("Parking Lot Vehicle Counting")
root.geometry(f"{DEFAULT_WIDTH}x{DEFAULT_HEIGHT}")
root.configure(bg="light gray")

#region Menu
menu_bar = tk.Menu(root)

# Create Preferences menu
variables_menu = tk.Menu(menu_bar, tearoff=0)
variables_menu.add_command(label="Set Total Slots", command=set_total_slots)
variables_menu.add_command(label="Set Line Position", command=set_line_position)
variables_menu.add_command(label="Set Interval Between VR Images", command=set_vr_interval)

reset_menu = tk.Menu(menu_bar, tearoff=0)
reset_menu.add_command(label="Reset State", command=reset)

# Add menus to the menu bar
menu_bar.add_cascade(label="Variables", menu=variables_menu)
menu_bar.add_cascade(label="Reset", menu=reset_menu)

# Set the menu bar to the window
root.config(menu=menu_bar)

#endregion

# Top: Parking status
status_frame = tk.Frame(root, bg="light gray")
status_frame.pack(side=tk.TOP, pady=10)

available_label = tk.Label(status_frame, text=f"{AVAILABLE_SLOTS}", font=("Arial", 20), fg="green", bg="light gray")
available_label.grid(row=0, column=0, padx=10)

status_canvas = tk.Canvas(status_frame, width=50, height=30, bg="green")
status_canvas.grid(row=0, column=1, padx=10)

occupied_label = tk.Label(status_frame, text=f"{OCCUPIED_SLOTS}", font=("Arial", 20), fg="red", bg="light gray")
occupied_label.grid(row=0, column=2, padx=10)

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
left_canvas = tk.Canvas(left_video_frame, bg="dark gray", width=DEFAULT_WIDTH//2, height=DEFAULT_HEIGHT//2)
left_canvas.pack(fill=tk.BOTH, expand=True)

left_buttons_frame = tk.Frame(left_video_frame, bg="light gray")
left_buttons_frame.pack(fill=tk.X, pady=5)

left_select_button = tk.Button(left_buttons_frame, text="Select Camera", command=lambda: select_video("left", left_canvas))
left_select_button.pack(side=tk.LEFT, padx=10)

left_play_button = tk.Button(left_buttons_frame, text="Play/Pause", command=lambda: play_pause_video("left", left_canvas))
left_play_button.pack(side=tk.RIGHT, padx=10)

# Right video section
right_canvas = tk.Canvas(right_video_frame, bg="dark gray", width=DEFAULT_WIDTH//2, height=DEFAULT_HEIGHT//2)
right_canvas.pack(fill=tk.BOTH, expand=True)

right_buttons_frame = tk.Frame(right_video_frame, bg="light gray")
right_buttons_frame.pack(fill=tk.X, pady=5)

right_select_button = tk.Button(right_buttons_frame, text="Select Camera", command=lambda: select_video("right", right_canvas))
right_select_button.pack(side=tk.LEFT, padx=10)

right_play_button = tk.Button(right_buttons_frame, text="Play/Pause", command=lambda: play_pause_video("right", right_canvas))
right_play_button.pack(side=tk.RIGHT, padx=10)

# Start the main loop
update_parking_status()
root.mainloop()