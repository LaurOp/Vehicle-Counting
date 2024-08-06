# Combining YOLO and Visual Rhythm for Vehicle Counting

This repository is the official implementation of [Combining YOLO and Visual Rhythm for Vehicle Counting] paper

**Authors**: Victor Nascimento Ribeiro and Nina S. T. Hirata

Link to the paper: [https://doi.org/10.5753/sibgrapi.est.2023.27473](https://doi.org/10.5753/sibgrapi.est.2023.27473)

![Alt Text](https://i.imgur.com/1S6EajH.png)



<br>


## Description

**This work presents an alternative and more efficient method for counting vehicles in videos using Deep Learning and Computer Vision techniques.**

> Conducted at the [University of São Paulo - USP](https://www5.usp.br/) under the guidance of [Prof. Nina S. T. Hirata](https://www.ime.usp.br/nina/).

We developed a system that combines YOLO, for vehicle detection, with Visual Rhythm (VR), a way to create time-spatial images. This integration enhances the system's efficiency by approximately 3 times when compared with conventional methods while maintaining similar accuracy.


<br>


<div align="center">
  <img src="https://i.imgur.com/XLU6bmq.png" width="550">
  <p>
    Data flow in the VR–based video counting vehicles
  </p>
</div>



<br>



## Events

**The work participated in:** 
- **[SIBGRAPI](https://sibgrapi.sbc.org.br/sibgrapi2023/)** – Conference on Graphics Patterns and Images, within the Workshop of Undergraduate Works (WUW). It is an annual academic conference held in Brazil that focuses on computer graphics, image processing, computer vision, and related fields. This work recieved [Honorable Mention](https://sibgrapi.sbc.org.br/sibgrapi2023/awards.html) in the WUW (Workshop of Undergraduate Works) Track
- **[SIICUSP](https://prpi.usp.br/siicusp/)** – _Simpósio Internacional de Iniciação Científica e Tecnológica da USP_ (International Symposium on Scientific and Technological Initiation at USP). The event provides a platform for undergraduate students to present their scientific and technological research projects.



<br>



## Usage

This codebase is written for ```python3```

```bash
# Clone this repository
git clone https://github.com/victor-nasc/Vehicle-Counting.git

# Install dependencies
pip install -r requirements.txt

# Run the program
python3 count.py --OPTIONS

# --OPTIONS
#    --line: Line position                           [default: 600]
#    --interval: Interval between VR images (frames) [default: 900]
#    --save-VR: Enable saving VR images              [default: False]
#    --save-vehicle: Enable saving vehicle images    [default: False]
#    
#    The video path is prompted during execution.
```



<br>



## Citation

If you find the code useful in your research, please consider citing our paper:

```
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

```

