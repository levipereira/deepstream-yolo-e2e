#!/bin/bash

# Default values
batch_size=1
network_size=640
precision="fp16"
file=""
update_config=false
model_type=""
force=false

# Function to display usage
usage() {
  echo "Usage: $0 -f file.onnx [-b batch_size] [-n network_size] [-p precision] [--update_config --det|--seg] [--force]"
  echo "  -f: Name of the .onnx file to be processed"
  echo "  -b: Batch size (default: 1)"
  echo "  -n: Network size (default: 640)"
  echo "  -p: Precision (fp32, fp16, qat; default: fp16)"
  echo "  --update_config: Update configuration file"
  echo "  --det: Model is for detection (requires --update_config)"
  echo "  --seg: Model is for segmentation (requires --update_config)"
  echo "  --force: Force re-generation of the engine file if it already exists"
  exit 1
}

# Get the directory where the script is located
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")

# Parse command line options
while getopts ":f:b:n:p:-:" opt; do
  case ${opt} in
    f )
      file=$OPTARG
      ;;
    b )
      batch_size=$OPTARG
      ;;
    n )
      network_size=$OPTARG
      ;;
    p )
      precision=$OPTARG
      ;;
    - )
      case ${OPTARG} in
        update_config)
          update_config=true
          ;;
        det)
          model_type="det"
          ;;
        seg)
          model_type="seg"
          ;;
        force)
          force=true
          ;;
        *)
          usage
          ;;
      esac
      ;;
    \? )
      usage
      ;;
  esac
done
shift $((OPTIND -1))

# Check if the file option is provided
if [ -z "$file" ]; then
  echo "Error: The .onnx file name must be provided."
  usage
fi

# Check if the file exists
if [ ! -f "$file" ]; then
  echo "Error: The file '$file' does not exist."
  exit 1
fi

# Check if update_config flag is provided, model_type must also be specified
if $update_config && [ -z "$model_type" ]; then
  echo "Error: --det or --seg must be specified with --update_config."
  usage
fi

# Set precision flags
precision_flags=""
case $precision in
  fp32)
    precision_flags="--fp32"
    ;;
  fp16)
    precision_flags="--fp16"
    ;;
  qat)
    precision_flags="--fp16 --int8"
    ;;
  *)
    echo "Error: Invalid precision. Use fp32, fp16, or qat."
    usage
    ;;
esac

# Extract filename without extension
filename=$(basename "$file" .onnx)
engine_filename="${filename}-netsize-${network_size}-batch-${batch_size}.engine"

# Check if the engine file already exists
engine_filepath="${SCRIPT_DIR}/${engine_filename}"
if [ -f "$engine_filepath" ] && ! $force; then
  echo "Warning: The engine file '$engine_filepath' already exists and will be reused. Use --force to rebuild."
else
  # Run trtexec with the provided options
  trtexec \
    --onnx=${file} \
    $precision_flags \
    --saveEngine=${engine_filepath} \
    --timingCacheFile=${engine_filepath}.timing.cache \
    --warmUp=500 \
    --duration=10  \
    --useCudaGraph \
    --useSpinWait \
    --noDataTransfers \
    --minShapes=images:1x3x${network_size}x${network_size} \
    --optShapes=images:${batch_size}x3x${network_size}x${network_size} \
    --maxShapes=images:${batch_size}x3x${network_size}x${network_size}
fi

# Update configuration file if requested
if $update_config; then
  onnx_file_line="onnx-file=models/${filename}.onnx"
  engine_file_line="model-engine-file=models/${engine_filename}"

  if [ "$model_type" = "det" ]; then
    config_file="${SCRIPT_DIR}/../config_pgie_yolo_det.txt"
  elif [ "$model_type" = "seg" ]; then
    config_file="${SCRIPT_DIR}/../config_pgie_yolo_seg.txt"
  fi

  if [ -f "$config_file" ]; then
    sed -i "s|^onnx-file=.*|$onnx_file_line|" "$config_file"
    sed -i "s|^model-engine-file=.*|$engine_file_line|" "$config_file"
    echo "Configuration file '$config_file' updated."
  else
    echo "Error: Configuration file '$config_file' does not exist."
    exit 1
  fi
fi
