"""
Creative Commons Attribution-NonCommercial 4.0 International License

You are free to share and adapt the material under the following terms:
- Attribution: Give appropriate credit.
- NonCommercial: Not for commercial use without permission.

For inquiries: levi.pereira@gmail.com
Repository: DeepStream / YOLO (https://github.com/levipereira/deepstream-yolo-e2e)
License: https://creativecommons.org/licenses/by-nc/4.0/legalcode
"""

import os
import subprocess
import argparse
import re
MODEL_ENGINE_DIR = '/apps/deepstream-yolo-e2e/models/engine/'

# Function to count non-empty lines in the label file
def count_labels(label_file):
    if not os.path.isfile(label_file):
        print(f"Error: Label file '{label_file}' does not exist.")
        return 0
    
    with open(label_file, 'r') as f:
        # Count lines that are not empty or whitespace
        labels = [line.strip() for line in f if line.strip()]
        return len(labels)

# Function to process the ONNX file and generate TensorRT engine
def process_onnx(file, label_file, batch_size=1, network_size=640, precision="fp16", pgie_config_file=None, force=False):
    # Check if the file exists
    if not os.path.isfile(file):
        print(f"Error: The file '{file}' does not exist.")
        return

    # Set precision flags
    precision_flags = []
    if precision == "fp32":
        # No flags for fp32
        pass
    elif precision == "fp16":
        precision_flags.append("--fp16")
    elif precision == "qat":
        precision_flags.extend(["--fp16", "--int8"])  # Add both flags for QAT
    else:
        print(f"Error: Invalid precision. Use fp32, fp16, or qat.")
        return

    # Ensure the MODEL_ENGINE_DIR exists
    if not os.path.exists(MODEL_ENGINE_DIR):
        os.makedirs(MODEL_ENGINE_DIR)

    # Extract filename without extension
    filename = os.path.basename(file).replace(".onnx", "")
    engine_filename = f"{filename}-{precision}-netsize-{network_size}-batch-{batch_size}.engine"
    engine_timing_filename = f"{filename}-{precision}-netsize-{network_size}.engine.timing.cache"

    # Generate full paths for the engine and timing cache files in the MODEL_ENGINE_DIR
    engine_filepath = os.path.join(MODEL_ENGINE_DIR, engine_filename)
    engine_timing_filepath = os.path.join(MODEL_ENGINE_DIR, engine_timing_filename)
    existing_engines = [
        f for f in os.listdir(MODEL_ENGINE_DIR)
        if re.match(rf"{filename}-{precision}-netsize-{network_size}-batch-(\d+)\.engine", f)
    ]
    
    for engine in existing_engines:
        existing_batch_size = int(re.search(r"-batch-(\d+)\.engine", engine).group(1))

        if existing_batch_size >= batch_size:
            engine_filepath = os.path.join(MODEL_ENGINE_DIR, engine)
            break
    if os.path.isfile(engine_filepath) and not force:
        print(f"Warning: The engine file '{engine_filepath}' already exists and will be reused. Use --force to rebuild.")
    else:
        # Run trtexec with the provided options
        command = [
                    "trtexec",
                    f"--onnx={file}",
                    ] + precision_flags + [  # Include precision flags as separate elements
                    f"--saveEngine={engine_filepath}",
                    f"--timingCacheFile={engine_timing_filepath}",
                    "--warmUp=500",
                    "--duration=10",
                    "--useCudaGraph",
                    f"--minShapes=images:1x3x{network_size}x{network_size}",
                    f"--optShapes=images:{batch_size}x3x{network_size}x{network_size}",
                    f"--maxShapes=images:{batch_size}x3x{network_size}x{network_size}"
                ]

        # Run the command
        try:
            subprocess.run(command, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error running trtexec: {e}")
            return

    # Count the number of labels (non-empty lines) in the label file
    num_detected_classes = count_labels(label_file)

    # Update configuration file if provided
    if pgie_config_file:
        file_abs_path = os.path.abspath(file)
        engine_abs_path = os.path.abspath(engine_filepath)
        label_file_abs_path = os.path.abspath(label_file)
        update_config_file(pgie_config_file, file_abs_path, engine_abs_path, label_file_abs_path, num_detected_classes, batch_size, network_size)

# Function to update the configuration file
def update_config_file(pgie_config_file, onnx_file, engine_file, label_file, num_detected_classes, batch_size, network_size):
    if os.path.isfile(pgie_config_file):
        with open(pgie_config_file, 'r') as file:
            lines = file.readlines()

        onnx_file_line = f"onnx-file={onnx_file}\n"
        engine_file_line = f"model-engine-file={engine_file}\n"
        label_file_line = f"labelfile-path={label_file}\n"
        batch_size_line = f"batch-size={batch_size}\n"
        infer_dims_line = f"infer-dims=3;{network_size};{network_size}\n"
        num_detected_classes_line = f"num-detected-classes={num_detected_classes}\n"

        updated_lines = []
        for line in lines:
            if line.startswith("onnx-file="):
                updated_lines.append(onnx_file_line)
            elif line.startswith("model-engine-file="):
                updated_lines.append(engine_file_line)
            elif line.startswith("labelfile-path="):
                updated_lines.append(label_file_line)
            elif line.startswith("batch-size="):
                updated_lines.append(batch_size_line)
            elif line.startswith("infer-dims="):
                updated_lines.append(infer_dims_line)
            elif line.startswith("num-detected-classes="):
                updated_lines.append(num_detected_classes_line)
            else:
                updated_lines.append(line)

        with open(pgie_config_file, 'w') as file:
            file.writelines(updated_lines)

        print(f"PGIE Configuration file '{pgie_config_file}' updated.")
    else:
        print(f"Error: PGIE Configuration file '{pgie_config_file}' does not exist.")

# Main function to handle command-line arguments
def main():
    parser = argparse.ArgumentParser(description="Process ONNX file and generate TensorRT engine.")
    parser.add_argument("-f", "--file", required=True, help="Name of the .onnx file to be processed")
    parser.add_argument("-l", "--label_file", required=True, help="Path to the label file")
    parser.add_argument("-b", "--batch_size", default=1, type=int, help="Batch size (default: 1)")
    parser.add_argument("-n", "--network_size", default=640, type=int, help="Network size (default: 640)")
    parser.add_argument("-p", "--precision", default="fp16", choices=["fp32", "fp16", "qat"], help="Precision (default: fp16)")
    parser.add_argument("-c", "--config_file", help="Configuration PGIE file to update")
    parser.add_argument("--force", action="store_true", help="Force re-generation of the engine file if it already exists")
    args = parser.parse_args()

    # Call the main processing function
    process_onnx(
        file=args.file,
        label_file=args.label_file,
        batch_size=args.batch_size,
        network_size=args.network_size,
        precision=args.precision,
        config_file=args.config_file,
        force=args.force
    )

if __name__ == "__main__":
    main()
