# Base image from NVIDIA NGC (DeepStream container with Triton support)
FROM nvcr.io/nvidia/deepstream:7.0-triton-multiarch

# Copy local repository
COPY . /apps/deepstream-yolo-e2e/

# Install additional DeepStream plugins
RUN bash /opt/nvidia/deepstream/deepstream/user_additional_install.sh

# Build Parse Function for NVDSINFER_YOLO
RUN bash /apps/deepstream-yolo-e2e/scripts/compile_nvdsinfer_yolo.sh

# Optional: Patch TensorRT plugins for EfficientNMX (for segmentation models)
RUN bash /apps/deepstream-yolo-e2e/TensorRTPlugin/patch_libnvinfer.sh

# Run ONNX to TensorRT conversion script
RUN bash /apps/deepstream-yolo-e2e/scripts/onnx_to_trt.sh -f /apps/deepstream-yolo-e2e/models/yolov9-c-trt.onnx -c /apps/deepstream-yolo-e2e/config_pgie_yolo_det.txt