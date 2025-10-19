#!/bin/bash

# Define the DeepStream root directory
DEEPSTREAM_ROOT_DIR="/opt/nvidia/deepstream/"

# Check if the DeepStream root directory exists
if [ ! -d "$DEEPSTREAM_ROOT_DIR" ]; then
    echo "DeepStream is not installed in the directory $DEEPSTREAM_ROOT_DIR"
    exit 1
fi

# Execute the additional DeepStream installation script
bash /opt/nvidia/deepstream/deepstream/user_additional_install.sh
if [ $? -ne 0 ]; then
    echo "Failed to execute additional DeepStream installation script."
    exit 1
fi

# Check the DeepStream version based on the directory name
DEEPSTREAM_VERSION_DIR=$(ls -d ${DEEPSTREAM_ROOT_DIR}/deepstream-* | awk -F'/' '{print $NF}')

# Verify if the version was identified correctly
if [[ $DEEPSTREAM_VERSION_DIR =~ deepstream-([0-9]+\.[0-9]+) ]]; then
    VERSION="${BASH_REMATCH[1]}"
    
    case "$VERSION" in
        "8.0")
            bash /opt/nvidia/deepstream/deepstream/user_deepstream_python_apps_install.sh --version 1.2.2
            ;;
        "7.1")
            bash /opt/nvidia/deepstream/deepstream/user_deepstream_python_apps_install.sh --version 1.2.0
            ;;
        *)
            echo "Unsupported DeepStream version: $VERSION"
            echo "Supported versions: 7.1, 8.0"
            exit 1
            ;;
    esac

    # Check if the previous command was successful
    if [ $? -ne 0 ]; then
        echo "Failed to install DeepStream Python apps for version $VERSION."
        exit 1
    fi
else
    echo "Unable to identify the DeepStream version in the directory $DEEPSTREAM_ROOT_DIR"
    exit 1
fi

# Compile the nvdsinfer_yolo function used by PGIE
cd /apps/deepstream-yolo-e2e || exit
scripts/compile_nvdsinfer_yolo.sh
if [ $? -ne 0 ]; then
    echo "Failed to compile nvdsinfer_yolo function."
    exit 1
fi

# Apply the patch to the nvinfer library
cd /apps/deepstream-yolo-e2e/TensorRTPlugin || exit
./patch_libnvinfer.sh
if [ $? -ne 0 ]; then
    echo "Failed to apply patch to the nvinfer library."
    exit 1
fi

# Install ffmpeg and yt-dlp
apt-get install ffmpeg -y
if [ $? -ne 0 ]; then
    echo "Failed to install ffmpeg."
    exit 1
fi

# Install Python packages based on DeepStream version
if [ "$VERSION" = "8.0" ]; then
    echo "Installing Python packages in DeepStream 8.0 virtual environment..."
    # Activate the virtual environment and install packages
    source /opt/nvidia/deepstream/deepstream-8.0/sources/deepstream_python_apps/pyds/bin/activate
    pip install yt-dlp prettytable requests
    if [ $? -ne 0 ]; then
        echo "Failed to install yt-dlp, prettytable and requests in virtual environment."
        exit 1
    fi
    echo "Skipping cuda-python installation for DeepStream $VERSION (not required)."
    deactivate
elif [ "$VERSION" = "7.1" ]; then
    echo "Installing Python packages for DeepStream 7.1..."
    pip3 install yt-dlp prettytable requests
    if [ $? -ne 0 ]; then
        echo "Failed to install yt-dlp, prettytable and requests."
        exit 1
    fi
    
    # Install correct version of cuda-python to avoid import errors (only for DeepStream 7.1)
    echo "Installing cuda-python 12.6.0 for DeepStream 7.1..."
    pip3 install cuda-python==12.6.0
    if [ $? -ne 0 ]; then
        echo "Failed to install cuda-python 12.6.0."
        exit 1
    fi
else
    echo "Unsupported DeepStream version: $VERSION"
    exit 1
fi

# Clear the screen at the end
clear
echo "All components have been installed successfully."
