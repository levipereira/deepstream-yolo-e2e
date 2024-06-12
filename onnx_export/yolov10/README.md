# YOLOv9 Export - Support Detection and Segmentation Models


## Description
This implementation use two TensorRT Plugins YoloNMS and ROIAling.<br>
[YoloNMS](https://github.com/levipereira/TensorRT/tree/release/8.6/plugin/yoloNMSPlugin) is a custom TRT Plugin. For now we must build this Plugin.<br>
ROIAling is available on TensorRT since 8.5

### Export Model - End2End for Detection and Segmentation

### 1. Clone Original YOLOv9, Patch Export Files and Install the requirements

```bash
git clone https://github.com/levipereira/deepstream-yolov9.git
git clone https://github.com/WongKinYiu/yolov9.git

## Patch Export Files
cp deepstream-yolov9/yolov9/export_onnxtrt.py yolov9/
cp deepstream-yolov9/yolov9/models/experimental_trt.py yolov9/models/

## Start docker pytorch container
mkdir yolov9/runs
docker run --gpus all  \
 -it \
 --rm \
 --name yolov9-onnx-trt \
 --net host  \
 --ipc=host \
 -v $(pwd)/yolov9:/yolov9 \
 -v $(pwd)/runs:/yolov9/runs \
 -w /yolov9 \
 nvcr.io/nvidia/pytorch:23.02-py3

## Install Pre-Reqs 
apt-get update 
apt-get install -y zip htop screen libgl1-mesa-glx libfreetype6-dev

pip3 install seaborn \
thop \
markdown-it-py==2.2.0 \
onnx-simplifier==0.4.35 \
onnxsim==0.4.35 \
onnxruntime==1.16.3                
pip install onnx_graphsurgeon --extra-index-url https://pypi.ngc.nvidia.com 
pip install pillow==9.5.0 --no-cache-dir --force-reinstall
```

### 2. Download model
**skip this step if you are using custom models**

```bash
cd /yolov9
mkdir -p /yolov9/runs/models
cd /yolov9/runs/models
wget https://github.com/WongKinYiu/yolov9/releases/download/v0.1/yolov9-c-seg-converted.pt
wget https://github.com/WongKinYiu/yolov9/releases/download/v0.1/yolov9-c-converted.pt

```

### 3. Export Models <br>

The export_onnxtrt.py automatically detect Detection model and Segmentation Model

#### Available Arguments:

- `--weights`: Path to the `model.pt` file.
- `--imgsz`: Image size (height, width). Default `640`
- `--device`: Device for execution (cpu, cuda device). Default `cpu`
- `--class-agnostic`: Enable Agnostic NMS (single class). Default `False`
- `--topk-all`: Topk to keep for all classes. Default `100`
- `--iou-thres`: IoU threshold. Default `0.45`
- `--conf-thres`: Confidence threshold. Default `0.25`
- `--mask-resolution`: Mask pooled output. Default `160`
- `--pooler-scale`: Multiplicative factor used to translate the ROI coordinates. Default `0.25`
- `--sampling-ratio`: Number of sampling points in the interpolation. Default `0`


```bash
python3 export_onnxtrt.py --weights runs/models/yolov9-c-converted.pt
```

```bash
python3 export_onnxtrt.py --weights runs/models/yolov9-c-seg-converted.pt
```

**Note**: Only `yolov9-c-seg-converted.pt` has an issue after reparametrization. It was configured as a DetectionModel instead of a SegmentationModel, `gelan-c-seg.pt` does not have this issue. <br>
To workaround this, you can force the export to recognize it as a segmentation model by using the environment variable `MODEL_DET=0`.

If you don't use the environment variable, you'll encounter the following error:
```bash
ONNX TRT: export failure ❌ 0.9s: 'tuple' object has no attribute 'permute'
```

To workaround this issue, use the following command:
```bash
MODEL_DET=0 python3 export_onnxtrt.py --weights runs/models/yolov9-c-seg-converted.pt
```

#### 4. Copy ONNX Models
exit from docker to host.

Copy the generated ONNX model file to the `deepstream-yolov9/models` dir.
```bash
cp yolov9/run/models/*.onnx deepstream-yolov9/models/
```


## Acknowledgements
https://github.com/hiennguyen9874/yolov7-seg
