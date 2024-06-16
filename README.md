
# DeepStream / YOLO - Detection and Segmentation with End2End

## ⚠️ Important Notice: This project is currently under construction and is not yet ready for use. ⚠️


Implementation of End-to-End YOLO Models for DeepStream

This repository provides an implementation of End-to-End YOLO models for DeepStream, optimizing the inference process by offloading Non-Maximum Suppression  computations onto the YOLO model itself. This design allows users to leverage dynamic batch sizes and input sizes seamlessly.

We support DeepStream versions 6.2, 6.3, 6.4, and 7.0 for dGPU/X86 and Jetson platforms. Currently, Jetson does not yet support Instance Segmentation models due to the deployment of the EfficientNMSX plugin, but we plan to release support for this soon.

This repository supports segmentation and detection models from the YOLO series - YOLOv10, YOLOv9, YOLOv8, and YOLOv7. 

All YOLO series models are implemented with End2End Deep Learning, incorporating three key features:

1. **Dynamic Shapes** - TensorRT enables the creation of network resolutions different from the original exported ONNX.
2. **Dynamic Batch Size** - Dynamically adjusts the batch size to maximize model performance according to the GPU's capabilities.
3. **NMS-Free** - Achieved in two different ways:
   1. **Native NMS-Free** - Models natively support NMS-Free, available for some YOLOv9 models and all YOLOv10 detection models.
   2. **TensorRT Plugins** - Utilizes TensorRT EfficientNMS plugin for detection models, and EfficientNMSX and ROIAlign for segmentation models.


All detection models across the YOLO series adhere to standardized output layers:

- `num_det`: Represents the number of detections.
- `det_boxes`: Provides the bounding boxes coordinates for each detected object.
- `det_scores`: Indicates the confidence score associated with each detected object.
- `det_classes`: Specifies the class label or category assigned to each detected object.

Similarly, instance segmentation models from the YOLO series also maintain standardized output layers:

- `num_det`: Represents the count of detected instances.
- `det_boxes`: Provides bounding box coordinates for each detected instance.
- `det_scores`: Indicates the confidence score associated with each detected instance.
- `det_classes`: Specifies the class label assigned to each detected instance.
- `det_masks`: Provides the segmentation masks corresponding to each detected instance.

With all models standardized with output layers ensure consistency across all YOLO models, we have streamlined processes in DeepStream using the `nvdsinfer_yolo` library for post-processing, supporting the entire YOLO series without the need for additional modifications.


This project was developed using DeepStream SDK 7.0.<br>[DeepStream 7.0 is now supported on Windows WSL2](https://docs.nvidia.com/metropolis/deepstream/dev-guide/text/DS_on_WSL2.html), which greatly aids in application development.



This repo support Object Detection and Instance Segmentation

### Video Processed with DeepStream 7.0 and YOLOv9-Segmentation
[![YOLOv9 Segmentation](https://img.youtube.com/vi/v6OTjOFLNLA/0.jpg)](https://www.youtube.com/watch?v=v6OTjOFLNLA)


# Project Workflow 

This project involves several important steps as outlined below:

### Clone Repo
```bash
git clone https://github.com/levipereira/deepstream-yolo-e2e.git
cd deepstream-yolo-e2e
git submodule update --init --recursive
```


#### 1. Download or Export your own Custom Models

Choose one option:

1. Download Models
    YOLOv9-C Detection/Segmentation models pre-trained on the COCO Dataset are available in this repository, exported in ONNX format.

    ```bash
    cd models
    ./download_models.sh
    cd ..
    ```
    ## Models Download 


2. You can [export your own custom YOLOv9 models](yolov9) to ONNX<br>

#### 2. Required Only for Instance Segmentation Models. 
 Download or Build TensorRT lib `libnvinfer_plugin.so.8.6.1` with  custom TensorRT EfficientNMSX plugin.
The EfficientNMSX plugin is customized, being a modified version of the EfficientNMS plugin, with the addition of a layer called det_indices. The EfficientNMSX plugin needs to be compiled, or you can use a precompiled version provided, which should be installed.

Choose one option:
1. Download  
    ```bash
    cd TensorRTPlugin
    wget https://github.com/levipereira/deepstream-yolo-e2e/releases/download/v1.0/libnvinfer_plugin.so.8.6.1
    cd ..
    ```
2. Build Plugin from source code [TensorRTPlugin](TensorRTPlugin) (This can take a long time)

#### 3. **Run Deepstream Container**
```bash
sudo docker pull nvcr.io/nvidia/deepstream:7.0-triton-multiarch
```
Start the docker container from `deepstream-yolo-e2e` dir:

```bash
sudo  docker run \
        -it \
        --privileged \
        --rm \
        --name=deepstream_yolov9 \
        --net=host \
        --gpus all \
        -e DISPLAY=$DISPLAY \
        -e CUDA_CACHE_DISABLE=0 \
        --device /dev/snd \
        -v /tmp/.X11-unix/:/tmp/.X11-unix \
        -v `pwd`:/apps/deepstream-yolo-e2e \
        -w /apps/deepstream-yolo-e2e \
        nvcr.io/nvidia/deepstream:7.0-triton-multiarch
```

#### 4. Install  `libnvinfer_plugin` with plugin TRT_EfficientNMSX (Required Only for Instance Segmentation Models)
```bash
cd TensorRTPlugin
./patch_libnvinfer.sh
cd ..
```

### 5.  Compile DeepStream Parse Functions
```bash
CUDA_VER=12.2 make -C nvdsinfer_yolo
```

### 6. Run Application
```bash
## Detection
deepstream-app -c deepstream_yolov9_det.txt

## Segmentation
deepstream-app -c deepstream_yolov9_mask.txt
```
>**The first run may take up to 15 minutes due to the building Engine File with FP16 precision.**

During this process, it may seem like it's stuck on the following line.
```
WARNING: [TRT]: onnx2trt_utils.cpp:374: Your ONNX model has been generated with INT64 weights, while TensorRT does not natively support INT64. Attempting to cast down to INT32.
```
Please be patient and wait for it to complete.


# Optional

## Dynamic Shapes Batch Size Support
This implementation supports dynamic shapes and dynamic batch sizes. To modify these settings, change the following configurations:
 
[config_pgie_yolo9_det.txt](https://github.com/levipereira/deepstream-yolo-e2e/blob/master/config_pgie_yolov9_det.txt#L8-L9)  <br>
[config_pgie_yolov9_mask.txt](https://github.com/levipereira/deepstream-yolo-e2e/blob/master/config_pgie_yolov9_mask.txt#L8-L10)
```
batch-size=1
infer-dims=3;640;640
```



## Build TRT Engine Files with trtexec  
**This also can be used to Perfomance Tests**

This will avoid to create TRT Engine File on each execution.

>Important: This step can take long time around ~15min per Model.
>Note: The model was exported with Dynamic Batch and Size, you can change it.

Optional flags: 
* `-b` -- batch_size (default is 1)
* `-n` -- network_size (default is 640)
* `-p` -- precision fp32/fp16/int8 (default fp32)
```bash

cd models
./build_engine.sh 
cd ..
```
Change in config_pgie files accordingly <br>
[config_pgie_yolo9_det.txt](https://github.com/levipereira/deepstream-yolo-e2e/blob/master/config_pgie_yolov9_det.txt#L8-L9)  <br>
[config_pgie_yolov9_mask.txt](https://github.com/levipereira/deepstream-yolo-e2e/blob/master/config_pgie_yolov9_mask.txt#L8-L10)
```plaintext
batch-size=1
infer-dims=3;640;640
# 0: FP32 1: INT8 2: FP16
network-mode=0
```
 



