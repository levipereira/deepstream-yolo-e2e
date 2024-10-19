
# DeepStream / YOLO with End2End Implementation


Implementation of End-to-End YOLO Detection and Segmentation Models for DeepStream

This repository offers an optimized implementation of End-to-End YOLO models for DeepStream, enhancing inference efficiency by integrating Non-Maximum Suppression (NMS) directly into the YOLO models. This approach supports dynamic batch sizes and input sizes, providing seamless adaptability.

### 🌟 New Feature: Python Bindings for Enhanced Application Development

We have introduced **Python bindings** in this version, greatly simplifying the process of developing new applications. 🐍 With these bindings, you can easily customize and extend your application's capabilities, making it ideal for both rapid prototyping.

### 🎥 Special Feature: Direct YouTube Video Integration

Now, you can integrate **videos directly from YouTube** into your pipeline. 📹 This feature enables seamless streaming and processing of YouTube videos, providing an expanded range of input sources for real-time analytics and AI-driven insights. 🌐 It’s perfect for scenarios where accessing online video data is essential, opening up new possibilities for multimedia applications. 


## DeepStream Version Support
| DeepStream Version | dGPU/X86 | Jetson |
|--------------------|----------|--------|
| 6.2                | ✅        | ✅      |
| 6.3                | ✅        | ✅      |
| 6.4                | ✅        | ✅      |
| 7.0                | ✅        | ✅      |
| 7.1                | ✅        | ✅      |


>Note: [DeepStream 7.0 is now supported on Windows WSL2](https://docs.nvidia.com/metropolis/deepstream/dev-guide/text/DS_on_WSL2.html), which greatly aids in application development.

## Supported End2End Models

### Detection Models

| Model    | Feature   | Dynamic Shape | Dynamic Batch Size | NMS-Free | Efficient NMS |
|----------|-----------|:-------------:|:-----------------:|:--------:|:-------------:|
| YOLOv10  | Detection |       ✅       |         ✅         |     ✅    |   <span style="color:red">❌</span>   |
| YOLOv9   | Detection |       ✅       |         ✅         |     ✅    |       ✅       |
| YOLOv8   | Detection |       ✅       |         ✅         | <span style="color:red">❌</span> |       ✅       |
| YOLOv7   | Detection |       ✅       |         ✅         | <span style="color:red">❌</span> |       ✅       |

### Instance Segmentation Models

| Model    | Feature      | Dynamic Shape | Dynamic Batch Size | NMS-Free | Efficient NMSX / RoiAlign |
|----------|--------------|:-------------:|:-----------------:|:--------:|:-------------------------:|
| YOLOv9   | Segmentation |       ✅       |         ✅         | <span style="color:red">❌</span> |            ✅              |
| YOLOv8   | Segmentation |       ✅       |         ✅         | <span style="color:red">❌</span> |            ✅              |
| YOLOv7   | Segmentation |       ✅       |         ✅         | <span style="color:red">❌</span> |            ✅              |

**Dynamic Shapes** - TensorRT enables the creation of network resolutions different from the original exported ONNX.

**Dynamic Batch Size** - Dynamically adjusts the batch size to maximize model performance according to the GPU's.

**NMS-Free** - Models natively implement NMS-Free, available for some YOLOv9 models and all YOLOv10 detection models.

**TensorRT Plugins** - TensorRT `EfficientNMS` plugin for detection models, and `EfficientNMSX / ROIAlign` plugins for segmentation models.


### Detection Model Output Layers
- `num_det`
- `det_boxes`
- `det_scores`
- `det_classes`


### Instance Segmentation Model Output Layers
- `num_det`
- `det_boxes`
- `det_scores`
- `det_classes`
- `det_masks` 


With all models standardized with output layers ensure consistency across all YOLO models, we have streamlined processes in DeepStream using the [nvdsinfer_yolo](https://github.com/levipereira/nvdsinfer_yolo/tree/master) library for post-processing, supporting the entire YOLO series without the need for additional modifications.

## Future Implementations 🚀

### Support for QAT Models

- **Yolov10-QAT** - 🔧 **In Development**
- **Yolov9-QAT** - ✅ **Ready**   
- **Yolov8-QAT** - 🔧 **In Development**
- **Yolov7-QAT** - ✅ **Ready**

**Ready**: Quantization Aware Training is implemented and ready for use, but integration into the current repository is still in progress. Stay tuned for updates!  
**In Development**: Development is ongoing to add support for models with Quantization Aware Training. Stay tuned for updates!

These future implementations aim to expand the range of models supported by this repository, offering enhanced capabilities for your projects.


# Project Workflow 

This project involves important steps as outlined below:

### 1. Clone Repo and Submodules
```bash
git clone https://github.com/levipereira/deepstream-yolo-e2e.git
cd deepstream-yolo-e2e
git submodule update --init --recursive
```

### 2. **Run Deepstream Container**

```bash
sudo docker pull nvcr.io/nvidia/deepstream:7.0-triton-multiarch
```
Start the docker container from `deepstream-yolo-e2e` dir:

#### 2.1 Windows WSL
```bash
sudo  docker run \
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
        nvcr.io/nvidia/deepstream:7.0-triton-multiarch
```

#### 2.2 Linux
```bash
sudo  docker run \
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
        nvcr.io/nvidia/deepstream:7.0-triton-multiarch
```

#### 2.3 Jetson
```bash
sudo  docker run \
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
        nvcr.io/nvidia/deepstream:7.0-triton-multiarch
```


### 3. **Install Deepstream Aditional Plugins**
```bash
bash /opt/nvidia/deepstream/deepstream/user_additional_install.sh
```

### 4. **Install Deepstream Python Binds**
To install the DeepStream Python bindings, run the following command in your terminal, depending on the version of DeepStream you are using. 

**This step is required only if you plan to use the code in Python.**

#### DeepStream 7.1
```bash
/opt/nvidia/deepstream/deepstream/user_deepstream_python_apps_install.sh --version 1.2.0
```
#### DeepStream 7.0
```bash
/opt/nvidia/deepstream/deepstream/user_deepstream_python_apps_install.sh --version 1.1.11
```

#### DeepStream 6.4
```bash
/opt/nvidia/deepstream/deepstream/user_deepstream_python_apps_install.sh --version 1.1.10
```
#### DeepStream 6.3
```bash
/opt/nvidia/deepstream/deepstream/user_deepstream_python_apps_install.sh --version 1.1.8
```

### 5. **Build Parse Function nvdsinfer_yolo used by PGIE**
```bash
cd /apps/deepstream-yolo-e2e
bash scripts/compile_nvdsinfer_yolo.sh
```

### 5. **Optional: Patch libnvinfer_plugin to Add EfficientNMX plugin**
>  Important: This step is **mandatory** if you plan to use segmentation models.
```bash
cd /apps/deepstream-yolo-e2e/TensorRTPlugin
bash ./patch_libnvinfer.sh
```

### 7. **Install `yt-dlp` and `ffmpeg` for YouTube Stream Support**
To enable YouTube streaming support in your Python applications, you need to install `yt-dlp` and `ffmpeg`

```bash
apt-get install ffmpeg  -y
pip3 install yt-dlp
```

### 8. **Download YOLO models**
```
cd /apps/deepstream-yolo-e2e/models
./download_models.py
```

### 9. **Convert Models ONNX to TensorRT**
This script converts an ONNX file to a TensorRT engine. 
>**Note** This process may take up to 15 minutes due to the building Engine File with FP16 precision.

```bash
cd /apps/deepstream-yolo-e2e/
scripts/onnx_to_trt.sh -f file.onnx [-b batch_size] [-n network_size] [-p precision] [-c config_file] [--force]
```

- **`-f`**: (Required) Name of the `.onnx` file to be processed.
- **`-b`**: Batch size. Default is `1`.
- **`-n`**: Network size. Default is `640`.
- **`-p`**: Precision. Options are `fp32`, `fp16`, and `qat`. Default is `fp16`.
- **`-c`**: Configuration PGIE file to update.
- **`--force`**: Force re-generation of the engine file if it already exists.

> **Note**: The PGIE configuration file (flag `-c`) must be `config_pgie_yolo_det.txt` for detection models and `config_pgie_yolo_seg.txt` for segmentation models.

```
cd /apps/deepstream-yolo-e2e
bash scripts/onnx_to_trt.sh -f models/yolov10n-trt.onnx -c config_pgie_yolo_det.txt
```


### 10. Run DeepStream Application

#### 10.1 DeepStream Reference Application
You can run the DeepStream reference application for both detection and segmentation tasks using the following commands:

#### Detection
```bash
deepstream-app -c config/deepstream_app/deepstream_yolo_det.txt
```

#### Segmentation
```bash
deepstream-app -c config/deepstream_app/deepstream_yolov9_mask.txt
```

#### 10.2 Run DeepStream Python Application
To run the DeepStream Python application for detection and segmentation, navigate to the `python_apps` directory and execute the following commands:

For more detailed information, please refer to the [`python_apps`](python_apps).

#### Configure Media Source
To configure your media settings, please edit the file located at `python_apps/config/media.ini`. In this file, you can select the media source from the following options:

- **File**: Specify a local media file.
- **RTSP**: Stream video from an RTSP source.
- **YouTube**: Integrate directly with YouTube videos.

#### Detection
```bash
cd python_apps
./main.py --output display --model-type det
```
#### Segmentation

```bash
cd python_apps
./main.py --output display --model-type seg
```


### Video Processed with DeepStream 7.0 and YOLOv9-Segmentation
[![YOLOv9 Segmentation](https://img.youtube.com/vi/v6OTjOFLNLA/0.jpg)](https://www.youtube.com/watch?v=v6OTjOFLNLA)


# How to Use Custom YOLO Models in This Project
After training your model, you need to export the model to the ONNX format by implementing the final layers of the model using End2End. <br>
The procedure is detailed in the [YOLO End2End](https://github.com/levipereira/yolo_e2e/)

Additionally, you must update the [`labels.txt`](labels.txt) file and modify the number of classes in the configuration file, either [`config_pgie_yolo_det.txt`](https://github.com/levipereira/deepstream-yolo-e2e/blob/c9f318b0182cc5d4591e15134ef7caf5a8cbddb9/config_pgie_yolo_det.txt#L13).txt or [`config_pgie_yolo_seg.txt`](https://github.com/levipereira/deepstream-yolo-e2e/blob/c9f318b0182cc5d4591e15134ef7caf5a8cbddb9/config_pgie_yolo_seg.txt#L13).


## Using EfficientNMSX Plugin for Segmentation Models

Segmentation models in this project depend on the EfficientNMSX plugin, which is only available in my [TensorRT repository](https://github.com/levipereira/TensorRT). If users prefer not to use the precompiled `libnvinfer_plugin.so` from this repository, they have the option to clone the forked repository and build `libnvinfer_plugin.so` themselves.

To build the plugin:

1. Clone the forked repository containing the EfficientNMSX plugin.
2. Follow the build instructions provided in the repository to compile `libnvinfer_plugin.so`.
3. Ensure that the compiled plugin is correctly integrated into your project environment.

This approach allows users flexibility in choosing whether to use the precompiled plugin or build it from the source, depending on their specific requirements and preferences.
