
<div align="center">
  <p>
    <a href="https://github.com/levipereira/deepstream-yolo-e2e" target="_blank">
      <img width="100%" src="https://github.com/levipereira/deepstream-yolo-e2e/releases/download/v1.0/banner_yolo_e2e.jpg" alt="DeepStream YOLO  banner"></a>
  </p>
</div>  

<div align="center">

# DeepStream / YOLO E2E

Implementation of End-to-End YOLO Detection and Segmentation Models for DeepStream

This repository offers an optimized implementation of End-to-End YOLO models for DeepStream, enhancing inference efficiency by integrating Non-Maximum Suppression (NMS) directly into the YOLO models. This approach supports dynamic batch sizes and input sizes, providing seamless adaptability.
 

### 🎥 Special Feature: Direct YouTube Video Integration 
</div>
<div align="justify"> 
Now, you can integrate **videos directly from YouTube** into your pipeline. 📹 This feature enables seamless streaming and processing of YouTube videos, providing an expanded range of input sources for real-time analytics and AI-driven insights. 🌐 It’s perfect for scenarios where accessing online video data is essential, opening up new possibilities for multimedia applications. 

> **Note:** This feature is available only in the Python application.
</div>
<div align="center"> 

### DeepStream Version Supported
| DeepStream Version | dGPU/X86 | Jetson |
|--------------------|----------|--------|
| 7.1                | ✅        | ⚠️     |
| 7.0                | ✅        | ✅      |
| 6.4                | ✅        | ✅      |
| 6.3                | ✅        | ✅      |
| 6.2                | ✅        | ✅      |
| 6.1                | ❌        | ❌      |

<div align="justify"> 

> ⚠️ **Note:** On Jetson devices, DeepStream 7.1 is only partially supported. Segmentation models are not yet compatible with this version.

>Note: [DeepStream 7.0 and later is supported on Windows WSL2](https://docs.nvidia.com/metropolis/deepstream/dev-guide/text/DS_on_WSL2.html), which greatly aids in application development.

</div> 

<div align="justify"> 

# Prerequisites

## 1. NVIDIA GPU CARD
Make sure you have an Nvidia GPU installed on your system and that the latest drivers are properly configured. 
Download and install the GPU drivers from the official Nvidia website:
[Nvidia Drivers Download](https://www.nvidia.com/en-us/drivers/)

## 2. Docker
Docker is required for creating and managing containers, simplifying development and deployment. 
To install Docker on Ubuntu, use the convenience script:<br>
[Docker Installation Guide for Ubuntu](https://docs.docker.com/engine/install/ubuntu/#install-using-the-convenience-script)

After the installation, add your user to the docker group to run Docker commands without sudo:
```bash
sudo usermod -aG docker $USER
```
 ## 3. NVIDIA Container Toolkit
The NVIDIA Container Toolkit allows Docker containers to utilize the Nvidia GPU to accelerate your applications. 
To install the toolkit, follow the official guide:

[NVIDIA Container Toolkit Installation Guide](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)

After installation, verify that the setup is correct by running a GPU-enabled container:
```bash
docker run --gpus all nvidia/cuda:12.0-base nvidia-smi
```

</div>



<div align="center"> 
 
#### Models Available

| Dataset | Model    | Feature      | Dynamic Shape | Dynamic Batch Size | NMS-Free | Efficient NMS / RoiAlign |
|---------|----------|--------------|:-------------:|:-----------------:|:--------:|:-------------------------:|
| COCO    | YOLO11   | Detection    |       ✅       |         ✅         |     <span style="color:red">🚫</span>    |     ✅                   |
| COCO    | YOLOv10  | Detection    |       ✅       |         ✅         |     ✅    |   <span style="color:red">🚫</span>   |
| COCO    | YOLOv9   | Detection    |       ✅       |         ✅         |     ✅    |       ✅                 |
| COCO    | YOLOv8   | Detection    |       ✅       |         ✅         | <span style="color:red">🚫</span> |       ✅                 |
| COCO    | YOLOv7   | Detection    |       ✅       |         ✅         | <span style="color:red">🚫</span> |       ✅                 |
| COCO    | YOLO11   | Segmentation |       ✅       |         ✅         |     <span style="color:red">🚫</span>    |     ✅                   |
| COCO    | YOLOv9   | Segmentation |       ✅       |         ✅         | <span style="color:red">🚫</span> |            ✅            |
| COCO    | YOLOv8   | Segmentation |       ✅       |         ✅         | <span style="color:red">🚫</span> |            ✅            |
| COCO    | YOLOv7   | Segmentation |       ✅       |         ✅         | <span style="color:red">🚫</span> |            ✅            |
| WIDER FACE    | YOLO11   | Detection    |       ✅       |         ✅         |     <span style="color:red">🚫</span>    |     ✅                   |
| WIDER FACE    | YOLOv10  | Detection    |       ✅       |         ✅         |     ✅    |   <span style="color:red">🚫</span>   |
| WIDER FACE    | YOLOv8   | Detection    |       ✅       |         ✅         |     ✅    |       ✅                 |

</div>



<table align="center" border="1" cellpadding="10">
    <tr>
        <th colspan="2">Features</th>
    </tr>
    <tr>
        <td><strong>Dynamic Shapes</strong></td>
        <td>TensorRT enables the creation of network resolutions different from the original exported ONNX.</td>
    </tr>
    <tr>
        <td><strong>Dynamic Batch Size</strong></td>
        <td>Dynamically adjusts the batch size to maximize model performance according to the number of deepstream sources.</td>
    </tr>
    <tr>
        <td><strong>NMS-Free</strong></td>
        <td>Models natively implement NMS-Free, available for some YOLOv9 models and all YOLOv10 detection models.</td>
    </tr>
    <tr>
        <td><strong>TensorRT Plugins</strong></td>
        <td>TensorRT <code>EfficientNMS</code> plugin for detection models, and <code>EfficientNMSX / ROIAlign</code> plugins for segmentation models.</td>
    </tr>
</table>

<br>
 
<div align="justify"> 

# Project Workflow 

This project involves important steps as outlined below:

### 1. Clone Repo and Submodules
```bash
git clone https://github.com/levipereira/deepstream-yolo-e2e.git
cd deepstream-yolo-e2e
git submodule update --init --recursive
```

### 2. **Run Deepstream Container**
In this example, we will use **DeepStream 7.1**.

Start the docker container from `deepstream-yolo-e2e` dir:
#### 2.1 Windows WSL
```bash
docker run \
        -it \
        --privileged \
        --rm \
        --net=host \
        --ipc=host \
        --gpus all \
        -e DISPLAY=$DISPLAY \
        -e CUDA_CACHE_DISABLE=0 \
        --device /dev/snd \
        -v /tmp/.X11-unix/:/tmp/.X11-unix \
        -v `pwd`:/apps/deepstream-yolo-e2e \
        -w /apps/deepstream-yolo-e2e \
        nvcr.io/nvidia/deepstream:7.1-triton-multiarch
```

#### 2.2 Linux
```bash
docker run \
        -it \
        --privileged \
        --rm \
        --net=host \
        --ipc=host \
        --gpus all \
        -e DISPLAY=$DISPLAY \
        -v /tmp/.X11-unix/:/tmp/.X11-unix \
        -v `pwd`:/apps/deepstream-yolo-e2e \
        -w /apps/deepstream-yolo-e2e \
        nvcr.io/nvidia/deepstream:7.1-triton-multiarch
```

#### 2.3 Jetson
```bash
docker run \
        -it \
        --privileged \
        --rm \
        --net=host \
        --ipc=host \
        --runtime nvidia \
        -e DISPLAY=$DISPLAY \
        -v /tmp/.X11-unix/:/tmp/.X11-unix \
        -v `pwd`:/apps/deepstream-yolo-e2e \
        -w /apps/deepstream-yolo-e2e \
        nvcr.io/nvidia/deepstream:7.1-triton-multiarch
```


### 3. **Install packages**
```bash
cd /apps/deepstream-yolo-e2e
bash /apps/deepstream-yolo-e2e/one_hit_install.sh
```
 
### 4. Run DeepStream Application
```bash
cd /apps/deepstream-yolo-e2e
./deepstream.py
```

### ⚠️ Important Tip

The model with the highest performance and accuracy is **YOLOv9-QAT (ReLU)**. This quantized model delivers exceptional results and supports multiple sources, depending on your GPU capabilities.

You can find it in the model selection menu:
- **Coco > Detection > Balanced > YOLOv9 QAT (ReLU)**

 
<h3>References</h3>
<ul>
    <li>
        <a href="https://github.com/ultralytics/ultralytics" target="_blank">YOLO11</a>: Official repository for the YOLOv11 model, featuring advanced object detection capabilities and enhancements over its predecessors.
    </li>
    <li>
        <a href="https://github.com/THU-MIG/yolov10" target="_blank">YOLOv10</a>: The official repository for YOLOv10, which includes improvements in detection accuracy and speed.
    </li>
    <li>
        <a href="https://github.com/WongKinYiu/yolov9" target="_blank">YOLOv9</a>: Access the official YOLOv9 repository, showcasing cutting-edge developments in the YOLO series.
    </li>
    <li>
        <a href="https://github.com/ultralytics/ultralytics" target="_blank">YOLOv8</a>: Official repository for the YOLOv8 model, known for its robust performance in real-time object detection.
    </li>
    <li>
        <a href="https://github.com/WongKinYiu/yolov7" target="_blank">YOLOv7</a>: Explore the YOLOv7 repository, which continues to push the boundaries of object detection technologies.
    </li>
    <li>
        <a href="https://github.com/akanametov/yolo-face" target="_blank">YOLO-FACE</a>: Dedicated repository for the YOLO-FACE model, designed for accurate face detection and recognition tasks.
    </li>
    <li>
        <a href="https://github.com/levipereira/ultralytics" target="_blank">Export YOLO 11/v10/v8</a>: This repository provides tools for exporting YOLOv11, YOLOv10, and YOLOv8 models for various applications, including End2End setups.
    </li>
    <li>
        <a href="https://github.com/levipereira/yolov9-qat" target="_blank">YOLOv9 QAT</a>: Official repository for quantization-aware training (QAT) of the YOLOv9 model, focusing on performance optimization.
    </li>
    <li>
        <a href="https://github.com/levipereira/nvdsinfer_yolo" target="_blank">NvDsInferYolo</a>: Explore the official repository for the NvDsInferYolo parsing function, facilitating integration with NVIDIA DeepStream applications.
    </li>
    <li>
        <a href="https://github.com/levipereira/yolo_e2e" target="_blank">YOLO E2E</a>: This repository focuses on exporting YOLO models with End2End capabilities, streamlining deployment processes.
    </li>
    <li>
        <a href="https://github.com/levipereira/TensorRT" target="_blank">TensorRT Plugin EfficientNMSX</a>: Official repository for the EfficientNMSX plugin implemented in TensorRT, enhancing non-maximum suppression performance in object detection pipelines.
    </li>
</ul>
