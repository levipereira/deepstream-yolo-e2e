# Base image from NVIDIA NGC (DeepStream container with Triton support)
FROM nvcr.io/nvidia/deepstream:7.0-triton-multiarch

# Add /sbin/ to path so lsmod and modprobe can be found
ENV PATH="/usr/sbin:/sbin:$PATH"

# Install additional DeepStream plugins
RUN bash /opt/nvidia/deepstream/deepstream/user_additional_install.sh

# Copy local repository, 1 by 1 for efficient caching
COPY ./models /apps/deepstream-yolo-e2e/models
COPY ./nvdsinfer_yolo /apps/deepstream-yolo-e2e/nvdsinfer_yolo
COPY ./scripts /apps/deepstream-yolo-e2e/scripts
COPY ./TensorRTPlugin /apps/deepstream-yolo-e2e/TensorRTPlugin
COPY ./tracker /apps/deepstream-yolo-e2e/tracker
COPY ./yolo_e2e /apps/deepstream-yolo-e2e/yolo_e2e

# Copy config file for ONNX to TensorRT conversion
COPY ./config_pgie_yolo_det.txt /apps/deepstream-yolo-e2e/config_pgie_yolo_det.txt

# Build Parse Function for NVDSINFER_YOLO
RUN cd /apps/deepstream-yolo-e2e/; bash scripts/compile_nvdsinfer_yolo.sh;

# Patch TensorRT plugins for EfficientNMX
RUN cd /apps/deepstream-yolo-e2e/; bash TensorRTPlugin/patch_libnvinfer.sh;

# Run ONNX to TensorRT conversion script
RUN cd /apps/deepstream-yolo-e2e/; bash scripts/onnx_to_trt.sh -f models/yolov9-c-trt.onnx -c config_pgie_yolo_det.txt

# Copy config files for running YOLOv9 on deepstream
COPY ./labels.txt /apps/deepstream-yolo-e2e/labels.txt
COPY ./deepstream_yolo_det.ini /apps/deepstream-yolo-e2e/deepstream_yolo_det.ini