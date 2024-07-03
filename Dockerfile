# Base image from NVIDIA NGC (DeepStream container with Triton support)
FROM nvcr.io/nvidia/deepstream:7.0-triton-multiarch

# Install additional DeepStream plugins
RUN bash /opt/nvidia/deepstream/deepstream/user_additional_install.sh

# Copy local repository
COPY . /apps/deepstream-yolo-e2e/

# Build Parse Function for NVDSINFER_YOLO
RUN cd /apps/deepstream-yolo-e2e/; bash scripts/compile_nvdsinfer_yolo.sh;

# Patch TensorRT plugins for EfficientNMX
RUN cd /apps/deepstream-yolo-e2e/; bash TensorRTPlugin/patch_libnvinfer.sh;

# Run ONNX to TensorRT conversion script
RUN cd /apps/deepstream-yolo-e2e/; bash scripts/onnx_to_trt.sh -f models/yolov9-c-trt.onnx -c config_pgie_yolo_det.txt