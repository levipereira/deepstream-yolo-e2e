#!/bin/bash
#
# DeepStream YOLO E2E Runner
# Automatically activates the correct Python environment based on DeepStream version
#
# Usage:
#   ./run.sh [options]
#   ./run.sh -o display
#   ./run.sh -o file -e gpu
#   ./run.sh --help
#

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# DeepStream paths
DEEPSTREAM_ROOT_DIR="/opt/nvidia/deepstream"
DEEPSTREAM_SYMLINK="${DEEPSTREAM_ROOT_DIR}/deepstream"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to get DeepStream version
get_deepstream_version() {
    if [ -L "$DEEPSTREAM_SYMLINK" ]; then
        local target=$(readlink -f "$DEEPSTREAM_SYMLINK")
        local version_dir=$(basename "$target")
        if [[ $version_dir =~ deepstream-([0-9]+\.[0-9]+) ]]; then
            echo "${BASH_REMATCH[1]}"
            return 0
        fi
    fi
    
    # Fallback: check directory directly
    local version_dir=$(ls -d ${DEEPSTREAM_ROOT_DIR}/deepstream-* 2>/dev/null | head -1 | xargs basename 2>/dev/null)
    if [[ $version_dir =~ deepstream-([0-9]+\.[0-9]+) ]]; then
        echo "${BASH_REMATCH[1]}"
        return 0
    fi
    
    echo ""
    return 1
}

# Check if DeepStream is installed
if [ ! -d "$DEEPSTREAM_ROOT_DIR" ]; then
    log_error "DeepStream is not installed in $DEEPSTREAM_ROOT_DIR"
    exit 1
fi

# Get DeepStream version
DS_VERSION=$(get_deepstream_version)

if [ -z "$DS_VERSION" ]; then
    log_error "Unable to detect DeepStream version"
    exit 1
fi

log_info "Detected DeepStream version: $DS_VERSION"

# Determine Python executable based on version
case "$DS_VERSION" in
    "8.0")
        VENV_PATH="${DEEPSTREAM_ROOT_DIR}/deepstream-${DS_VERSION}/sources/deepstream_python_apps/pyds"
        PYTHON_EXEC="${VENV_PATH}/bin/python3"
        
        if [ ! -f "$PYTHON_EXEC" ]; then
            log_error "Virtual environment not found at: $VENV_PATH"
            log_error "Please run one_hit_install.sh first"
            exit 1
        fi
        
        log_info "Using Python from virtual environment"
        ;;
    "7.1")
        PYTHON_EXEC="python3"
        log_info "Using system Python"
        ;;
    *)
        log_error "Unsupported DeepStream version: $DS_VERSION"
        log_error "Supported versions: 7.1, 8.0"
        exit 1
        ;;
esac

# Change to script directory
cd "$SCRIPT_DIR"

# Execute the main Python script with all passed arguments
exec "$PYTHON_EXEC" "${SCRIPT_DIR}/deepstream.py" "$@"

