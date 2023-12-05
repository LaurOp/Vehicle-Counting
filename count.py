
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


def counting(VR, line, cap, ini, double, model_mark, model_vehicle, saveVehicle):
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


        # update count
        count[classe] += 1

        if classe == -1:
            print(f"Couldn't find the vehicle in frame {frame}!!!")
            print('VERIFY IT MANUALLY')

        if saveVehicle:
            name = f'vehicle-crops/{str(labels[classe])}{frame}.jpg'
            print(f'Saving as {name}')
            cv2.imwrite(name, crop)
            
            
    print('Count in this VR: ')
    print_count(count)
    print()
    
    return duo, count, infos
        
        
    

def main(video_path, line, sec, saveVR, saveVehicle):
    ini = 0     # current VR initial frame
    double = [] # marks on the border of the previous VR
    infos = []  # details of each vehicle
    VR = []     # VR image
    count = np.array([0, 0, 0, 0, 0, 0, 0]) # count of each class
    
    
    # load models
    model_mark = YOLO('./YOLO/marks/weights/best.pt')
    model_vehicle = YOLO('./YOLO/vehicle/weights/best.pt')


    # opens the video
    cap = cv2.VideoCapture(video_path)
    assert cap.isOpened() == True, 'Can not open the video'


    # creates folders to save images
    if saveVehicle and not os.path.exists('vehicle-crops/'):
        os.makedirs('vehicle-crops/')
    if saveVR and not os.path.exists('VR-images/'):
        os.makedirs('VR-images/')
        
        
    # begins video 
    while True: 
        ret, frame = cap.read() 
        if ret == False:
            break
        
        # stacks line in VR image
        VR.append(frame[line])
        
        
        # if VR image has been fully built
        if len(VR) == sec:        
            print(f'VR image {ini//sec} created')    

            if saveVR:
                name = 'VR-images/VR' + str(ini//sec) + '.jpg'
                print(f'Saving as {name}')
                cv2.imwrite(name, np.array(VR)) 
            
            double, cnt, inf = counting(np.array(VR), line, cap, ini, double, model_mark, model_vehicle, saveVehicle)                
            count += cnt
            infos += inf

            VR = []
            ini += sec
            cap.set(cv2.CAP_PROP_POS_FRAMES, ini)
        
        
    # count the remaining frames
    if len(VR) > 0:
        print(f'VR image {ini//sec + 1} created')
        _, cnt, inf = counting(np.array(VR), line, cap, ini, double, model_mark, model_vehicle, saveVehicle)  
        count += cnt 
        infos += inf
        if saveVR:
            name = 'VR-images/VR' + str(ini//sec + 1) + '.jpg'
            print(f'Saving as {name}')
            cv2.imwrite(name, np.array(VR)) 


    # final results
    print('\n -------------------------- \n')
    print_count(count)
    print(sum(count), 'vehicles counted in total')
    
    # write infos
    with open('infos.txt', 'w') as file:
        for item in infos:
            file.write(str(item) + '\n')


    # closes the video
    cap.release()
    cv2.destroyAllWindows()
    
    
      
      
def print_count(count):
    labels = ['Bus', 'Car', 'Motorbike', 'Pickup', 'Truck', 'Van', '???'] 
    max_length = max(len(label) for label in labels)

    for label, cnt in zip(labels, count):
        print(f'{label.ljust(max_length)} : {cnt}')
      
      
      
      
if __name__ == "__main__":    

    # parse arguments
    parser = argparse.ArgumentParser(description='Count the number of vehicles in a video')
    
    parser.add_argument('--line', type=int, default=600, help='Line position')
    parser.add_argument('--interval', type=int, default=900, help='Interval between VR images (frames)')
    parser.add_argument('--save-VR', type=bool, default=False, help='Enable saving VR images')
    parser.add_argument('--save-vehicle', type=bool, default=False, help='Enable saving vehicle images')
    args = parser.parse_args()


    video_path = input('Enter the video path: ')
    
    
    print('Counting vehicles in the video...\n')
    main(video_path, args.line, args.interval, args.save_VR, args.save_vehicle)
