"""
@inproceedings{sibgrapi_estendido,
 author = {Victor Ribeiro and Nina Hirata},
 title = {Combining YOLO and Visual Rhythm for Vehicle Counting},
 booktitle = {Anais Estendidos do XXXVI Conference on Graphics, Patterns and Images},
 location = {Rio Grande/RS},
 year = {2023},
 keywords = {},
 issn = {0000-0000},
 pages = {164--167},
 publisher = {SBC},
 address = {Porto Alegre, RS, Brasil},
 url = {https://sol.sbc.org.br/index.php/sibgrapi_estendido/article/view/27473}
}
"""

'''
Combining YOLO with Visual Rhythm for Vehicle Counting

Usage:
    python count.py [options]
    --line: line position                           [defalt:  600]
    --interval: interval between VR images (frames) [default: 900]
    --save-VR: enable saving VR images              [default: False]
    --save-vehicle: enable saving vehicle images    [default: False]

    The video path is asked in the execution.

    The results are printed in the terminal
    and saved detaily in 'infos.txt' and.
'''

import argparse
import time

import cv2
import numpy as np
from ultralytics import YOLO

PARKING_LOT_CAPACITY = 1000  # square meters
CURRENT_SPACE = 1000  # square meters

VEHICLE_SIZES = {
    'Car': 3,
    'Truck': 30,
    'Van': 6,
    'Bus': 18
}

# price ranges
TICKET_PRICES = {
    'Car': (1, 5),
    'Truck': (5, 25),
    'Van': (2, 10),
    'Bus': (3.5, 17.5)
}

# current
parking_lot_state = {
    'Car': 0,
    'Truck': 0,
    'Van': 0,
    'Bus': 0
}

# after some cars leave
vehicle_totals = {
    'Car': 0,
    'Truck': 0,
    'Van': 0,
    'Bus': 0
}

LIVE_PRICES = {
    'Car': 1.0,
    'Truck': 5.0,
    'Van': 2.0,
    'Bus': 3.0
}

total_session_profit = 0
total_profit_last_30s = 0
daily_profit_estimate = 0
last_decay_time = time.time()
latest_vehicle = ""
latest_ticket_paid = 0


def print_count(count):
    labels = ['Bus', 'Car', 'Motorbike', 'Pickup', 'Truck', 'Van', '???']
    max_length = max(len(label) for label in labels)

    for label, cnt in zip(labels, count):
        print(f'{label.ljust(max_length)} : {cnt}')


def calculate_ticket_prices():
    total_occupied = sum(parking_lot_state[vehicle] * VEHICLE_SIZES[vehicle] for vehicle in parking_lot_state)
    usage_ratio = total_occupied / PARKING_LOT_CAPACITY

    prices = {}
    for vehicle, (min_price, max_price) in TICKET_PRICES.items():
        prices[vehicle] = min_price + (max_price - min_price) * usage_ratio

    for vehicle, (min_price, max_price) in TICKET_PRICES.items():
        LIVE_PRICES[vehicle] = min_price + (max_price - min_price) * usage_ratio

    return prices


def decay_parking_lot():
    global last_decay_time
    current_time = time.time()
    elapsed_time = current_time - last_decay_time

    if elapsed_time >= 5:  # Decay every 5 seconds
        sqm_to_free = int(elapsed_time // 5)
        global CURRENT_SPACE

        if (CURRENT_SPACE + sqm_to_free) <= PARKING_LOT_CAPACITY:
            CURRENT_SPACE = CURRENT_SPACE + sqm_to_free

        last_decay_time = current_time

        print(f"Parking lot decay occurred. Remaining capacity: {CURRENT_SPACE}/{PARKING_LOT_CAPACITY}m².")


def update_parking_lot(count):
    global total_profit_last_30s, total_session_profit, CURRENT_SPACE
    prices = calculate_ticket_prices()

    print("Updated ticket prices:")
    for vehicle, price in prices.items():
        print(f"{vehicle}: {price:.2f}")
    print()

    newVehicles = []
    for vehicle, cnt in count.items():
        if vehicle in parking_lot_state:
            parking_lot_state[vehicle] += cnt
            vehicle_totals[vehicle] += cnt
            if cnt > 0:
                ticket_price = prices[vehicle]
                profit = cnt * ticket_price
                total_profit_last_30s += profit
                total_session_profit += profit
                print(f"Found a {vehicle.upper()}. +{ticket_price:.2f} per ticket")
                newVehicles.append((vehicle, ticket_price))
                global latest_vehicle, latest_ticket_paid
                latest_vehicle = vehicle
                latest_ticket_paid = ticket_price
                CURRENT_SPACE = CURRENT_SPACE - VEHICLE_SIZES[vehicle] * cnt

    total_occupied = sum(parking_lot_state[vehicle] * VEHICLE_SIZES[vehicle] for vehicle in parking_lot_state)

    print(f"Remaining parking lot capacity: {CURRENT_SPACE}/{PARKING_LOT_CAPACITY} square meters")
    return prices, total_occupied, newVehicles


def counting(VR, line, cap, ini, double, model_mark, model_vehicle, saveVehicle):
    labels = ['Bus', 'Car', 'Motorbike', 'Pickup', 'Truck', 'Van', '???']
    count = {label: 0 for label in labels}
    duo = []
    delta = 120

    # detect marks
    marks = model_mark(VR, iou=0.05, conf=0.25, verbose=False)
    marks = marks[0].numpy()
    boxes = marks.boxes.xyxy
    # print(f'Detected {len(boxes)} marks')

    for box in boxes:
        x0, y0, x1, y1 = np.floor(box).astype(int)

        if y1 >= len(VR) - 1:
            duo.append([x0, x1])
        elif y0 <= 1:
            mid = (x1 + x0) // 2
            if any(x1_ant <= mid <= x2_ant for x1_ant, x2_ant in double):
                continue

        frame = ini + (y0 + y1) // 2
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame)

        ret, img = cap.read()
        if not ret:
            print('Frame not found  :(')
            continue

        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))

        vehicles = model_vehicle(img, iou=0.5, conf=0.3, verbose=False)
        vehicles = vehicles[0].numpy()

        a = max(x0 - delta, 0)
        b = min(x1 + delta, width)

        dist_min = height
        for cls, xyxy, cnf in zip(vehicles.boxes.cls, vehicles.boxes.xyxy, vehicles.boxes.conf):
            x0, y0, x1, y1 = np.floor(xyxy).astype(int)
            mid_x = (x0 + x1) // 2

            if a < mid_x < b and y0 < line < y1:
                mid_y = (y0 + y1) // 2
                dist = abs(mid_y - line)
                if dist < dist_min:
                    dist_min = dist
                    classe = int(cls)
                    count[labels[classe]] += 1

    return duo, count


def print_session_profit():
    print(f"\nTotal profit this session: ${total_session_profit:.2f}")


def estimate_dynamic_daily_profit(total_profit_last_30s, vr_interval, video_fps):
    global daily_profit_estimate

    video_time_per_vr = vr_interval / video_fps
    vr_count_in_30s = 30 / video_time_per_vr
    video_time_in_30s = vr_count_in_30s * video_time_per_vr

    profit_per_second_video = total_profit_last_30s / video_time_in_30s

    total_occupied = sum(parking_lot_state[vehicle] * VEHICLE_SIZES[vehicle] for vehicle in parking_lot_state)

    # if we got profit_per_second using total_occupied space,
    # we can calculate the daily profit estimate based on the total parking lot capacity
    # also multiply by de median price of the tickets
    # and add a buffer to the estimate
    future_price_factor = 1 + (PARKING_LOT_CAPACITY - total_occupied) / PARKING_LOT_CAPACITY

    if total_occupied == 0:
        daily_profit_estimate = 0
    else:
        profit_per_space = total_session_profit / total_occupied
        daily_profit_estimate = total_session_profit + (
                profit_per_space * (PARKING_LOT_CAPACITY - total_occupied) * 1.25 * future_price_factor)

    print(f"Profit per second: ${profit_per_second_video:.2f}")
    print(f"Estimated daily profit: ${daily_profit_estimate:.2f}")
    return daily_profit_estimate


def main(video_path, line, sec, saveVR, saveVehicle, loop=False):
    ini = 0
    double = []
    VR = []

    model_mark = YOLO('../YOLO/marks.pt')
    model_vehicle = YOLO('../YOLO/vehicle.pt')

    cap = cv2.VideoCapture(video_path)
    assert cap.isOpened(), 'Cannot open the video'

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_delay = 1 / fps  # in seconds

    while True:
        if loop and ini >= cap.get(cv2.CAP_PROP_FRAME_COUNT):
            ini = 0
            double = []
            VR = []
            cap.release()  # reinitialize
            cap = cv2.VideoCapture(video_path)
            assert cap.isOpened(), "Cannot reopen the video file."

        if CURRENT_SPACE <= 0:
            print("Parking lot is full.")
            break

        ret, frame = cap.read()
        if not ret:
            if loop:
                # reset video
                print("End of video reached. Restarting...")
                ini = 0
                double = []
                VR = []
                cap.release()
                cap = cv2.VideoCapture(video_path)
                assert cap.isOpened(), "Cannot reopen the video file."
                cap.set(cv2.CAP_PROP_POS_FRAMES, ini) # reset to start
                continue
            else:
                break

        VR.append(frame[line])

        if len(VR) == sec:
            double, count = counting(np.array(VR), line, cap, ini, double, model_mark, model_vehicle, saveVehicle)
            update_parking_lot(count)
            decay_parking_lot()
            estimate_dynamic_daily_profit(total_profit_last_30s, 90, cap.get(cv2.CAP_PROP_FPS))

            VR = []
            ini += sec
            cap.set(cv2.CAP_PROP_POS_FRAMES, ini)

        time.sleep(frame_delay)

    cap.release()
    cv2.destroyAllWindows()

    print("\nTotal vehicles counted:")
    for vehicle, total in vehicle_totals.items():
        print(f"{vehicle}: {total}")

    print_session_profit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Count the number of vehicles in a video')
    parser.add_argument('--line', type=int, default=465, help='Line position')
    parser.add_argument('--interval', type=int, default=90, help='Interval between VR images (frames)')
    parser.add_argument('--save-VR', type=bool, default=False, help='Enable saving VR images')
    parser.add_argument('--save-vehicle', type=bool, default=False, help='Enable saving vehicle images')
    args = parser.parse_args()

    # video_path = input('Enter the video path: ')
    video_path = "C:\\Users\\Laur\\Desktop\\Topici\\traffic.mp4"

    starting_time = time.time()

    print('Counting vehicles in the video and updating parking lot state...\n')
    main(video_path, args.line, args.interval, args.save_VR, args.save_vehicle, loop=True)

    print(f"\nTotal execution time: {time.time() - starting_time:.2f} seconds")
