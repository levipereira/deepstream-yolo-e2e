#!/bin/bash

# Detect architecture
arch=$(uname -m)

if [ "$arch" != "x86_64" ]; then
    echo "$arch not supported yet."
    exit 1
fi

TRT_INSTALL_LIBPATH="/usr/lib/$arch-linux-gnu"

# URLs for the different versions of the library
URL_852="https://github.com/levipereira/deepstream-yolo-e2e/releases/download/v1.0/libnvinfer_plugin.so.8.5.2.x86_64"
URL_853="https://github.com/levipereira/deepstream-yolo-e2e/releases/download/v1.0/libnvinfer_plugin.so.8.5.3.x86_64"
URL_861="https://github.com/levipereira/deepstream-yolo-e2e/releases/download/v1.0/libnvinfer_plugin.so.8.6.1.x86_64"

# Function to download and apply the patch
download_and_patch() {
    local lib_name=$1
    local url=$2

    if [ ! -f "./$lib_name" ]; then
        echo -e "\n\nDownloading: $lib_name"
        curl -L --retry 3 --retry-delay 5 -A "Mozilla/5.0" -o "./$lib_name" "$url" || exit 1
    fi

    # Backup original library if it exists
    if [ -f "$TRT_INSTALL_LIBPATH/$lib_name" ]; then
        mv "$TRT_INSTALL_LIBPATH/$lib_name" "./${lib_name}.ori.bak"
        echo "Backup of the original $lib_name created."
    fi

    # Copy the downloaded library to the installation path
    cp "$(pwd)/$lib_name" "$TRT_INSTALL_LIBPATH/$lib_name"

    # Update library cache
    ldconfig
    echo "$lib_name has been installed successfully."
}

# Check which version of the library is installed and apply the appropriate patch
if [ -f "$TRT_INSTALL_LIBPATH/libnvinfer_plugin.so.8.5.2" ]; then
    download_and_patch "libnvinfer_plugin.so.8.5.2" "$URL_852"
elif [ -f "$TRT_INSTALL_LIBPATH/libnvinfer_plugin.so.8.5.3" ]; then
    download_and_patch "libnvinfer_plugin.so.8.5.3" "$URL_853"
elif [ -f "$TRT_INSTALL_LIBPATH/libnvinfer_plugin.so.8.6.1" ]; then
    download_and_patch "libnvinfer_plugin.so.8.6.1" "$URL_861"
else
    echo "No compatible version of libnvinfer_plugin.so found in $TRT_INSTALL_LIBPATH."
    exit 1
fi
