#!/bin/bash
arch=$(uname -m)

if [ "$arch" == "x86_64" ]; then
    TRT_INSTALL_LIBPATH=/usr/lib/$arch-linux-gnu
else
    echo "$arch not supported yet."
    exit
fi

# Check if libnvinfer_plugin.so.8.6.1 exists in the current directory
if [ ! -f "./libnvinfer_plugin.so.8.6.1" ]; then
    echo -e "\n\nDownloading: libnvinfer_plugin.so.8.6.1"
    curl -L --retry 3 --retry-delay 5 -A "Mozilla/5.0" -o "./libnvinfer_plugin.so.8.6.1" "https://github.com/levipereira/deepstream-yolov9/releases/download/v1.0/libnvinfer_plugin.so.8.6.1.$arch" || exit 1
fi

# Backup original libnvinfer_plugin.so.x.y
if [ -f "$TRT_INSTALL_LIBPATH/libnvinfer_plugin.so.8.6.1" ]; then
    mv $TRT_INSTALL_LIBPATH/libnvinfer_plugin.so.8.6.1 "./libnvinfer_plugin.so.8.6.1.ori.bak"
fi

cp $(pwd)/libnvinfer_plugin.so.8.6.1 $TRT_INSTALL_LIBPATH/libnvinfer_plugin.so.8.6.1

# Update library cache
ldconfig
echo "libnvinfer_plugin.so.8.6.1 has been installed successfully."