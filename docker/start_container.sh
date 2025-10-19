#!/bin/bash

# Automated script to start DeepStream container
# Automatically detects platform and allows version selection

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored messages
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to detect platform
detect_platform() {
    print_info "Detecting platform..."
    
    # Check if running on WSL (multiple methods for better detection)
    if grep -q Microsoft /proc/version 2>/dev/null || \
       grep -q microsoft /proc/version 2>/dev/null || \
       [ -n "$WSL_DISTRO_NAME" ] || \
       [ -n "$WSLENV" ]; then
        PLATFORM="wsl"
        print_success "Platform detected: Windows WSL"
    # Check if it's Jetson (ARM64 + NVIDIA)
    elif uname -m | grep -q aarch64 && nvidia-smi &>/dev/null; then
        PLATFORM="jetson"
        print_success "Platform detected: NVIDIA Jetson"
    # Default Linux
    else
        PLATFORM="linux"
        print_success "Platform detected: Linux"
    fi
}

# Function to select DeepStream version
select_deepstream_version() {
    print_info "Selecting DeepStream version..."
    
    # Check if passed as parameter
    if [ "$1" = "7.1" ] || [ "$1" = "8.0" ]; then
        DEEPSTREAM_VERSION="$1"
        print_success "Version selected via parameter: DeepStream $DEEPSTREAM_VERSION"
        return
    fi
    
    # Ask user if not specified
    echo ""
    echo "Choose DeepStream version:"
    echo "1) DeepStream 8.0 (default)"
    echo "2) DeepStream 7.1"
    echo ""
    read -p "Enter your choice [1]: " choice
    
    case $choice in
        2)
            DEEPSTREAM_VERSION="7.1"
            ;;
        *)
            DEEPSTREAM_VERSION="8.0"
            ;;
    esac
    
    print_success "Version selected: DeepStream $DEEPSTREAM_VERSION"
}

# Function to configure platform-specific parameters
configure_platform_params() {
    case $PLATFORM in
        "wsl")
            GPU_PARAMS="--gpus all"
            EXTRA_ENV="-e CUDA_CACHE_DISABLE=0"
            EXTRA_DEVICES="--device /dev/snd"
            print_info "WSL configuration: GPU support, CUDA cache enabled, audio device"
            ;;
        "jetson")
            GPU_PARAMS="--runtime nvidia"
            EXTRA_ENV=""
            EXTRA_DEVICES=""
            print_info "Jetson configuration: NVIDIA runtime"
            ;;
        "linux")
            GPU_PARAMS="--gpus all"
            EXTRA_ENV=""
            EXTRA_DEVICES=""
            print_info "Linux configuration: Default GPU support"
            ;;
    esac
}

# Function to check if container exists
check_container_exists() {
    if docker ps -a --format "table {{.Names}}" | grep -q "^deepstream-yolo-e2e$"; then
        return 0  # Container exists
    else
        return 1  # Container doesn't exist
    fi
}

# Function to check if container is running
is_container_running() {
    if docker ps --format "table {{.Names}}" | grep -q "^deepstream-yolo-e2e$"; then
        return 0  # Container is running
    else
        return 1  # Container is not running
    fi
}

# Function to handle existing container
handle_existing_container() {
    if is_container_running; then
        print_warning "Container 'deepstream-yolo-e2e' is already running!"
        echo ""
        echo "What would you like to do?"
        echo "1) Connect to the running container"
        echo "2) Stop and remove the container, then start a new one"
        echo "3) Exit"
        echo ""
        read -p "Enter your choice [1]: " choice
        
        case $choice in
            2)
                print_info "Stopping and removing existing container..."
                docker stop deepstream-yolo-e2e
                docker rm deepstream-yolo-e2e
                return 1  # Continue with new container creation
                ;;
            3)
                print_info "Exiting..."
                exit 0
                ;;
            *)
                print_info "Connecting to existing container..."
                docker exec -it deepstream-yolo-e2e /bin/bash
                exit 0
                ;;
        esac
    else
        print_warning "Container 'deepstream-yolo-e2e' exists but is not running!"
        echo ""
        echo "What would you like to do?"
        echo "1) Start the existing container"
        echo "2) Remove the container and create a new one"
        echo "3) Exit"
        echo ""
        read -p "Enter your choice [1]: " choice
        
        case $choice in
            2)
                print_info "Removing existing container..."
                docker rm deepstream-yolo-e2e
                return 1  # Continue with new container creation
                ;;
            3)
                print_info "Exiting..."
                exit 0
                ;;
            *)
                print_info "Starting existing container..."
                docker start deepstream-yolo-e2e
                docker exec -it deepstream-yolo-e2e /bin/bash
                exit 0
                ;;
        esac
    fi
}

# Function to run the container
run_container() {
    # Check if container already exists
    if check_container_exists; then
        handle_existing_container
        if [ $? -eq 0 ]; then
            return  # User chose to connect to existing container
        fi
    fi
    
    print_info "Starting DeepStream $DEEPSTREAM_VERSION container..."
    
    # Enable X11 access
    xhost + 2>/dev/null || print_warning "Could not execute xhost +"
    
    # Build docker command
    DOCKER_CMD="docker run \
        -it \
        --privileged \
        --name deepstream-yolo-e2e \
        --net=host \
        --ipc=host \
        $GPU_PARAMS \
        -e DISPLAY=\$DISPLAY \
        $EXTRA_ENV \
        $EXTRA_DEVICES \
        -v /tmp/.X11-unix/:/tmp/.X11-unix \
        -v \`pwd\`:/apps/deepstream-yolo-e2e \
        -v /run/user/0:/run/user/0 \
        -v /mnt/wslg/runtime-dir:/mnt/wslg/runtime-dir \
        -w /apps/deepstream-yolo-e2e \
        deepstream-yolo-e2e_8.0"
        
        #nvcr.io/nvidia/deepstream:$DEEPSTREAM_VERSION-triton-multiarch"
    
    print_info "Executing command:"
    echo "$DOCKER_CMD"
    echo ""
    
    # Execute the command
    eval $DOCKER_CMD
}

# Function to show help
show_help() {
    echo "Usage: $0 [version]"
    echo ""
    echo "Available versions:"
    echo "  7.1    - DeepStream 7.1"
    echo "  8.0    - DeepStream 8.0 (default)"
    echo ""
    echo "Examples:"
    echo "  $0        # Uses DeepStream 8.0 (default)"
    echo "  $0 7.1    # Uses DeepStream 7.1"
    echo "  $0 8.0    # Uses DeepStream 8.0"
    echo ""
    echo "The script automatically detects the platform:"
    echo "  - Windows WSL"
    echo "  - Linux"
    echo "  - NVIDIA Jetson"
}

# Main function
main() {
    # Check if help was requested
    if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
        show_help
        exit 0
    fi
    
    print_info "=== DeepStream Container Launcher ==="
    echo ""
    
    # Detect platform
    detect_platform
    
    # Select version
    select_deepstream_version "$1"
    
    # Configure platform parameters
    configure_platform_params
    
    echo ""
    print_info "Final configuration:"
    echo "  Platform: $PLATFORM"
    echo "  DeepStream: $DEEPSTREAM_VERSION"
    echo ""
    
    # Run the container
    run_container
}

# Execute main function with all arguments
main "$@"
