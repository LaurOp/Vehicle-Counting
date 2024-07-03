### YOLOv8 model for mark and vehicle detection

[Trainig Details](https://drive.google.com/drive/folders/1QLfDRS6OSrBGO76CgvGoCCof6xgxZJub?usp=sharing)

**Vehicle detection**
```
model=yolov8s.pt
task=detect 
mode=train 
epochs=100
batch=64

* the other hyperparameters are the YOLO default settings
```
```
mAP0.5 == 0.84274
mAP0.5:0.95 == 0.69166 
```

**Mark detection**
```
model=yolov8s.pt 
task=detect 
mode=train 
epochs=75 
batch=8 

* the other hyperparameters are the YOLO default settings
```
```
final mAP0.5 == 0.99136
final mAP0.5:0.95 == 0.60865 
```
