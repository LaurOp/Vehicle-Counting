# Combining YOLO and Visual Rhythm for Vehicle Counting

This repository is the official implementation of [Combining YOLO and Visual Rhythm for Vehicle Counting]

**Authors**: Victor N. Ribeiro and Nina S. T. Hirata

![Alt Text](./imgs/print_sb.png)



<br>



**This work presents an alternative and more efficient method for counting vehicles in videos using Deep Learning and Computer Vision techniques.**

> Conducted at the [University of São Paulo - USP](https://www5.usp.br/) under the guidance of [Prof. Nina S. T. Hirata](https://www.ime.usp.br/nina/).

We developed a system that combines YOLO, for vehicle detection, with Visual Rhythm (VR), a way to create time-spatial images. This integration enhances the system's efficiency by approximately 3 times when compared with conventional methods while maintaining similar accuracy.

dasdasdsa
![Alt Text](./imgs/method-hori.png)

dasdsadas
<div align="center">
  <img src="./imgs/method-vert.png" alt="Alt Text" width="500">
  <p>
    sodasd
  </p>
</div>


<br>


## Events

**The work participated in:** 
- [SIBGRAPI](https://sibgrapi.sbc.org.br/sibgrapi2023/) (**Honorable Mention**) – Conference on Graphics Patterns and Images, within the Workshop of Undergraduate Works (WUW). It is an annual academic conference held in Brazil that focuses on computer graphics, image processing, computer vision, and related fields.
- [SIICUSP](https://prpi.usp.br/siicusp/) – International Seminar on Scientific and Technological Initiation of the University of São Paulo. The event provides a platform for undergraduate students to present their scientific and technological research projects.

[Link to the paper](https://drive.google.com/file/d/1wVH4HC0ClA7rfVMxXEBE4QctVhcGZBMU/view?usp=sharing)



<br>



## Usage
```bash
# install yarn
npm install --global yarn

# install dependencies
yarn

# run the frontend, it should start in http://localhost:5173
yarn dev
```

**Requirements**
```sh
numpy
opencv-python
ultralytics
```
