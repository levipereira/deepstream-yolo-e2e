# Base image from NVIDIA NGC (DeepStream container with Triton support)
FROM nvcr.io/nvidia/deepstream:7.0-triton-multiarch

# Add /sbin/ to path so lsmod and modprobe can be found
ENV PATH="/usr/sbin:/sbin:$PATH"

# Install additional DeepStream plugins
RUN bash /opt/nvidia/deepstream/deepstream/user_additional_install.sh

# Install additional system utilities and Python packages
RUN apt-get update && apt-get install -y \
    python3-pip \
    kmod \
    python3-gi \
    python3-dev \
    python3-gst-1.0 \
    python3-opencv \
    python3-numpy \
    libgstrtspserver-1.0-0 gstreamer1.0-rtsp \
    libgirepository1.0-dev \
    gobject-introspection gir1.2-gst-rtsp-server-1.0 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install DeepStream Python bindings
RUN pip3 install pyds cuda-python

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

# Copy pipeline Python code
COPY ./pipeline.py /apps/deepstream-yolo-e2e/pipeline.py
COPY ./pipeline.py /apps/deepstream-yolo-e2e/pipeline_test.py
