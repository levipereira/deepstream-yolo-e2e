# Base image from NVIDIA NGC (DeepStream container with Triton support)
FROM nvcr.io/nvidia/deepstream:7.0-triton-multiarch

# Set working directory
WORKDIR /apps/deepstream-yolo-e2e

# Install additional DeepStream plugins
RUN bash /opt/nvidia/deepstream/deepstream/user_additional_install.sh

# Clone the main repository and update submodules
RUN git clone https://github.com/levipereira/deepstream-yolo-e2e.git /apps/deepstream-yolo-e2e && \
    cd /apps/deepstream-yolo-e2e && \
    git submodule update --init --recursive

# Build Parse Function for NVDSINFER_YOLO
RUN cd /apps/deepstream-yolo-e2e && \
    bash scripts/compile_nvdsinfer_yolo.sh

# Patch TensorRT plugins for EfficientNMX
RUN cd /apps/deepstream-yolo-e2e && \
    bash TensorRTPlugin/patch_libnvinfer.sh

# Run ONNX to TensorRT conversion script
RUN cd /apps/deepstream-yolo-e2e && \
    bash scripts/onnx_to_trt.sh -f models/yolov10n-trt.onnx -c config_pgie_yolo_det.txt
