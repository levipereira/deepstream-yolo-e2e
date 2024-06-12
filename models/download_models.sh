#!/bin/bash

# Array of file URLs to download
urls=(
    "https://github.com/levipereira/deepstream-yolov9/releases/download/v1.0/yolov9-c-converted-trt.onnx"
    "https://github.com/levipereira/deepstream-yolov9/releases/download/v1.0/yolov9-t-converted-trt.onnx"
    "https://github.com/levipereira/deepstream-yolov9/releases/download/v1.0/yolov9-s-converted-trt.onnx"
    "https://github.com/levipereira/deepstream-yolov9/releases/download/v1.0/yolov9-m-converted-trt.onnx"
    "https://github.com/levipereira/deepstream-yolov9/releases/download/v1.0/yolov9-c-seg-converted-trt.onnx"
)

# Destination directory
destination="./"

# Download files
for url in "${urls[@]}"; do
    filename=$(basename "$url")
    echo -e "\n\nDownloading: $filename..."
    curl -L --retry 3 --retry-delay 5 -A "Mozilla/5.0" -o "${destination}${filename}" "$url"
    echo -e "Download Complete: $filename.\n"
done

echo "All downloads complete."
