

'''

TA UM POUCO BAGUNÇADO :D (por enquanto)
MUITOS PRINTS PARA DEBUG

DA PRA DEIXAR MAIS EFICIENTE


'''

import cv2
import numpy as np
from ultralytics import YOLO

labels = ['Bus', 'Car', 'Motorbike', 'Pickup', 'Truck', 'Van', '?'] # Classes
count = [0, 0, 0, 0, 0, 0, 0] # Contagem
pulo = []  # frames em que o veiculo aparece em 2 VRs diferentes
infos = [] # [frame, classe] de cada veiculo


def contagem(VR, video_path, duplo, ini):
    # abre o video
    cap = cv2.VideoCapture(video_path)
    assert cap.isOpened() == True, '[2] Nao conseguiu abrir o video [2]'
    
    # load nos pesos
    model = YOLO('mancha.pt')
    model1 = YOLO('veiculos.pt')

    # detecta as manchas da VR
    results = model(VR, iou=0.2, conf=0.2) 
    results = results[0].numpy()
    boxes = results.boxes.xyxy  
    print(boxes)
    
    dup = []
    delta = 120          # pixels para cada lado horiontalmente
    # altura = y - 350   # 150 pixels acima da linh
    
    # para cada mancha
    for i, box in enumerate(boxes):
        # coordenadas da mancha
        x0, y0, x1, y1 = np.floor(box).astype(int)
        
        pulou = 0
        # mancha em 2 VR diferentes
        if(y1 >= 899): # VR.shape -1
            dup.append([x0, x1])
        
        if y0 <= 1:
            x = (x1 + x0) // 2
            for x1_ant, x2_ant in duplo:
                if x >= x1_ant and x <= x2_ant:
                    pulo.append(ini)
                    pulou = 1
                    break
        
        if pulou == 1:
            continue
        
        frame = ini + y1

        # pega o frame correspondente
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame)
        ret, img = cap.read()   
        if ret == False:
            print('Frame nao encontrado') # nunca entraria aqui
            continue
        
        # predict nos veiculos do frame
        results1 = model1(img, iou=0.5, conf=0.3)
        results1 = results1[0].numpy()
        
        # local aproximado do veiculo no eixo X
        a = max(0, x0 - delta)
        b = min(1280, x1 + delta)
        
        # encontra o veiculo correspondente a mancha
        dist_min = 720
        classe = -1
        for cls, xyxy in zip(results1.boxes.cls, results1.boxes.xyxy):
            x0, y0, x1, y1 = np.floor(xyxy).astype(int)
            x = (x0 + x1) // 2
            
            if x > a and x < b:
                dist = abs(y1 - 600)
                if dist < dist_min:
                    dist_min = dist
                    classe = int(cls)
                    crop = img[y0:y1 , x0:x1]
        
        infos.append([frame, labels[classe]])
        name = 'runs/v3/' + str(labels[classe]) + str(ini) + str(i) + '.jpg'
        print(name)

        # atualiza informacoes
        count[classe] += 1
        if classe != -1:
            cv2.imwrite(name, crop)
            pass
        else: 
            cv2.imwrite('runs/v3/AAA' + str(frame) + '.jpg', img)
            model1(img, iou=0.8, conf=0.3)
            print("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAa")
            
    return dup
        
        
    

def main():
    video_path = 'videoplayback1.mp4'
    y = 600     # altura da linha 
    ini = 0     # frame da primeira linha do VR
    sec = 900   # altura do VR (frames)
    aux = 0
    
    VR = []     # imagem VR
    duplo = []
    
    # abre o video
    cap = cv2.VideoCapture(video_path)
    assert cap.isOpened() == True, '[1] Nao conseguiu abrir o video [1]'

    while True: 
        # Le o proximo frame
        ret, frame = cap.read()
        if ret == False:
            break
        
        # Corta a linha e empilha na VR
        linha = frame[y]    
        VR.append(linha)
        
        # Contagem a cada 'sec' segundos 
        if np.shape(VR)[0] >= sec:             
            name = 'runs/v3/outros/' + str(ini) + '.jpg'
            print(name)
            # cv2.imwrite(name, np.array(VR))

            duplo = contagem(np.array(VR), video_path, duplo, ini)                
                
            VR = []
            ini += sec
            
            print('pulo: ', pulo)
            print('duplo: ', np.size(duplo), duplo)
            with open('res.txt', 'w') as file:
                for item in infos:
                    file.write(str(item) + '\n')
        
    # contagem para os frames restantes
    contagem(np.array(VR), video_path, duplo, ini)
    name = 'runs/v3/outros/' + str(ini) + '.jpg'
    print(name)
    # cv2.imwrite(name, np.array(VR))
    
    # salva tudo
    print("Acabou o video")
    print(count)
    print('Total: ', sum(count))

    # fecha o video
    cap.release()
    cv2.destroyAllWindows()
    
      
      
if __name__ == "__main__":
    main()
    

    
