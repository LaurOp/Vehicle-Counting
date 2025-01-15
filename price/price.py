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

import cv2
import numpy as np
from ultralytics import YOLO
import argparse
import os
import time

# Constants for parking lot management
PARKING_LOT_CAPACITY = 1000  # square meters
VEHICLE_SIZES = {
    'Car': 3,
    'Truck': 30,
    'Van': 6,
    'Bus': 18
}
TICKET_PRICES = {
    'Car': (1, 5),
    'Truck': (5, 25),
    'Van': (2, 10),
    'Bus': (3.5, 17.5)
}

# Initialize parking lot state
parking_lot_state = {
    'Car': 0,
    'Truck': 0,
    'Van': 0,
    'Bus': 0
}

# Track the total count of vehicles
vehicle_totals = {
    'Car': 0,
    'Truck': 0,
    'Van': 0,
    'Bus': 0
}

total_session_profit = 0
total_profit_last_30s = 0  # Tracks profit over the last 30 seconds
daily_profit_estimate = 0
last_decay_time = time.time()


def print_count(count):
    labels = ['Bus', 'Car', 'Motorbike', 'Pickup', 'Truck', 'Van', '???']
    max_length = max(len(label) for label in labels)

    for label, cnt in zip(labels, count):
        print(f'{label.ljust(max_length)} : {cnt}')


def print_ticket_info():
    """
    Prints current ticket prices and parking lot usage.
    """
    prices = calculate_ticket_prices()
    total_occupied = sum(parking_lot_state[vehicle] * VEHICLE_SIZES[vehicle] for vehicle in parking_lot_state)
    print("Current Parking Lot State:")
    print(f"Occupied Area: {total_occupied}/{PARKING_LOT_CAPACITY} sq. meters")
    print("Ticket Prices:")
    for vehicle, price in prices.items():
        print(f"  {vehicle}: ${price:.2f}")


def calculate_ticket_prices():
    """
    Calculate ticket prices based on parking lot usage.
    """
    total_occupied = sum(parking_lot_state[vehicle] * VEHICLE_SIZES[vehicle] for vehicle in parking_lot_state)
    usage_ratio = total_occupied / PARKING_LOT_CAPACITY

    prices = {}
    for vehicle, (min_price, max_price) in TICKET_PRICES.items():
        prices[vehicle] = min_price + (max_price - min_price) * usage_ratio
    return prices


import random


def decay_parking_lot():
    """
    Continuously decay the occupied parking space, randomly freeing up one vehicle type.
    """
    global last_decay_time
    current_time = time.time()
    elapsed_time = current_time - last_decay_time

    if elapsed_time >= 3:  # Decay every 3 seconds
        sqm_to_free = int(elapsed_time // 3)

        for _ in range(sqm_to_free):
            # List of vehicle types that have at least one vehicle in the parking lot
            available_vehicles = [vehicle for vehicle in parking_lot_state if parking_lot_state[vehicle] > 0]

            if available_vehicles:
                # Randomly choose a vehicle type
                vehicle_to_free = random.choice(available_vehicles)

                # Remove one of that vehicle type
                parking_lot_state[vehicle_to_free] -= 1
                print(f"Freed one {vehicle_to_free}.")

        # Update last decay time
        last_decay_time = current_time

        # Calculate and print the remaining parking lot capacity
        total_occupied = sum(parking_lot_state[vehicle] * VEHICLE_SIZES[vehicle] for vehicle in parking_lot_state)
        remaining_capacity = PARKING_LOT_CAPACITY - total_occupied
        print(
            f"Parking lot decay occurred. Remaining parking lot capacity: {remaining_capacity}/{PARKING_LOT_CAPACITY} square meters.")


def update_parking_lot(count):
    """
    Update the parking lot state with the counts from the current VR.
    """
    global total_profit_last_30s, total_session_profit
    prices = calculate_ticket_prices()

    print("Updated ticket prices:")
    for vehicle, price in prices.items():
        print(f"{vehicle}: {price:.2f}")
    print()

    # Update parking lot state and calculate total occupied space
    total_occupied = 0
    for vehicle, cnt in count.items():
        if vehicle in parking_lot_state:
            parking_lot_state[vehicle] += cnt
            vehicle_totals[vehicle] += cnt
            if cnt > 0:
                ticket_price = prices[vehicle]
                profit = cnt * ticket_price
                total_profit_last_30s += profit
                total_session_profit += profit  # Update the session's total profit
                print(f"Found a {vehicle.upper()}. +{ticket_price:.2f} per ticket")

    # Calculate total occupied area
    total_occupied = sum(parking_lot_state[vehicle] * VEHICLE_SIZES[vehicle] for vehicle in parking_lot_state)
    remaining_capacity = PARKING_LOT_CAPACITY - total_occupied

    print(f"Remaining parking lot capacity: {remaining_capacity}/{PARKING_LOT_CAPACITY} square meters")


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
    """
    Prints the total profit made during the current session.
    """
    print(f"\nTotal profit for this session: ${total_session_profit:.2f}")


def estimate_dynamic_daily_profit(total_profit_last_30s, vr_interval, video_fps):
    global daily_profit_estimate
    """
    Dynamically estimates daily profit based on the video processing rate.

    Args:
        total_profit_last_30s (float): Profit made in the last 30 real-time seconds.
        vr_interval (int): Number of frames analyzed per VR.
        video_fps (int): Frames per second of the video.

    Returns:
        float: Estimated daily profit.
    """
    # Calculate video time processed in 30 real-time seconds
    video_time_per_vr = vr_interval / video_fps  # Video time represented by one VR
    vr_count_in_30s = 30 / video_time_per_vr  # VRs processed in 30 real-time seconds
    video_time_in_30s = vr_count_in_30s * video_time_per_vr

    # Calculate profit per second of video time
    profit_per_second_video = total_profit_last_30s / video_time_in_30s

    # Calculate how occupied the parking is
    total_occupied = sum(parking_lot_state[vehicle] * VEHICLE_SIZES[vehicle] for vehicle in parking_lot_state)

    # if we got profit_per_second using total_occupied space, we can calculate the daily profit estimate based on the total parking lot capacity
    # also multiply by de median price of the tickets
    median_price = sum(TICKET_PRICES[vehicle][0] for vehicle in TICKET_PRICES) / len(TICKET_PRICES)
    # add a buffer to the estimate
    future_price_factor = 1 + (PARKING_LOT_CAPACITY - total_occupied) / PARKING_LOT_CAPACITY

    if total_occupied == 0:
        daily_profit_estimate = 0
    else:
        profit_per_space = total_session_profit / total_occupied
        daily_profit_estimate = total_session_profit + (
                    profit_per_space * (PARKING_LOT_CAPACITY - total_occupied) * 1.25 * future_price_factor)

    print(f"Profit per second of video: ${profit_per_second_video:.2f}")
    print(f"Estimated daily profit: ${daily_profit_estimate:.2f}")
    return daily_profit_estimate


def main(video_path, line, sec, saveVR, saveVehicle):
    ini = 0
    double = []
    VR = []

    model_mark = YOLO('../YOLO/marks.pt')
    model_vehicle = YOLO('../YOLO/vehicle.pt')

    cap = cv2.VideoCapture(video_path)
    assert cap.isOpened(), 'Cannot open the video'

    if saveVehicle and not os.path.exists('vehicle-crops/'):
        os.makedirs('vehicle-crops/')
    if saveVR and not os.path.exists('VR-images/'):
        os.makedirs('VR-images/')

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        VR.append(frame[line])

        if len(VR) == sec:
            # print(f'VR image {ini // sec} created')

            if saveVR:
                name = f'VR-images/VR{ini // sec}.jpg'
                print(f'Saving as {name}')
                cv2.imwrite(name, np.array(VR))

            double, count = counting(np.array(VR), line, cap, ini, double, model_mark, model_vehicle, saveVehicle)
            update_parking_lot(count)
            decay_parking_lot()  # Apply decay
            prices = calculate_ticket_prices()
            estimate_dynamic_daily_profit(total_profit_last_30s, 90, cap.get(cv2.CAP_PROP_FPS))

            VR = []
            ini += sec
            cap.set(cv2.CAP_PROP_POS_FRAMES, ini)

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

    video_path = input('Enter the video path: ')

    print('Counting vehicles in the video and updating parking lot state...\n')
    main(video_path, args.line, args.interval, args.save_VR, args.save_vehicle)
