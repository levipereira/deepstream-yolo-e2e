# Base image from NVIDIA NGC (DeepStream container with Triton support)
FROM nvcr.io/nvidia/deepstream:7.0-triton-multiarch

# Set working directory
WORKDIR /apps/deepstream-yolo-e2e

# Install additional DeepStream plugins
RUN bash /opt/nvidia/deepstream/deepstream/user_additional_install.sh

# Build Parse Function for NVDSINFER_YOLO
RUN bash scripts/compile_nvdsinfer_yolo.sh

# Optional: Patch TensorRT plugins for EfficientNMX (for segmentation models)
RUN bash TensorRTPlugin/patch_libnvinfer.sh

# Download YOLO models
RUN cd models && ./download_models.py

# Run ONNX to TensorRT conversion script
RUN bash scripts/onnx_to_trt.sh -f models/yolov10n-trt.onnx -c config_pgie_yolo_det.txt