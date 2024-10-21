import os
import argparse
import subprocess

def count_labels(label_file):
    """Counts the number of labels in the given file, excluding empty lines."""
    try:
        with open(label_file, 'r') as f:
            labels = [line.strip() for line in f if line.strip()]
        return len(labels)
    except FileNotFoundError:
        print(f"Error: Label file '{label_file}' not found.")
        exit(1)

def update_config_file(config_file, onnx_file, engine_file, batch_size, network_size, num_detected_classes, label_file):
    """Updates the configuration file with the provided parameters."""
    if not os.path.isfile(config_file):
        print(f"Error: Configuration file '{config_file}' does not exist.")
        exit(1)

    with open(config_file, 'r') as f:
        config_lines = f.readlines()

    def replace_or_add_param(lines, param, value):
        for i, line in enumerate(lines):
            if line.startswith(param):
                lines[i] = f"{param}={value}\n"
                return
        lines.append(f"{param}={value}\n")

    onnx_file_line = os.path.abspath(onnx_file)
    engine_file_line = os.path.abspath(engine_file)
    label_file = os.path.abspath(label_file)
    replace_or_add_param(config_lines, "onnx-file", onnx_file_line)
    replace_or_add_param(config_lines, "model-engine-file", engine_file_line)
    replace_or_add_param(config_lines, "batch-size", batch_size)
    replace_or_add_param(config_lines, "infer-dims", f"3;{network_size};{network_size}")
    replace_or_add_param(config_lines, "num-detected-classes", num_detected_classes)
    replace_or_add_param(config_lines, "labelfile-path", label_file)
    

    with open(config_file, 'w') as f:
        f.writelines(config_lines)

    print(f"Configuration file '{config_file}' updated.")

def generate_engine(onnx_file, engine_file, timing_cache_file, precision, batch_size, network_size, force):
    """Generates a TensorRT engine using trtexec."""
    if os.path.isfile(engine_file) and not force:
        print(f"Warning: The engine file '{engine_file}' already exists and will be reused. Use --force to rebuild.")
        return

    precision_flags = ""
    if precision == "fp16":
        precision_flags = "--fp16"
    elif precision == "qat":
        precision_flags = "--fp16 --int8"

    cmd = [
        "trtexec",
        f"--onnx={onnx_file}",
        precision_flags,
        f"--saveEngine={engine_file}",
        f"--timingCacheFile={timing_cache_file}",
        "--warmUp=500",
        "--duration=10",
        "--useCudaGraph",
        f"--minShapes=images:1x3x{network_size}x{network_size}",
        f"--optShapes=images:{batch_size}x3x{network_size}x{network_size}",
        f"--maxShapes=images:{batch_size}x3x{network_size}x{network_size}"
    ]

    subprocess.run(' '.join(cmd), shell=True, check=True)
    print(f"Engine file '{engine_file}' generated successfully.")

def main():
    parser = argparse.ArgumentParser(description="Process an ONNX file and generate a TensorRT engine.")
    parser.add_argument('-f', '--file', required=True, help="Name of the .onnx file to be processed")
    parser.add_argument('-b', '--batch_size', type=int, default=1, help="Batch size (default: 1)")
    parser.add_argument('-n', '--network_size', type=int, default=640, help="Network size (default: 640)")
    parser.add_argument('-p', '--precision', choices=['fp32', 'fp16', 'qat'], default='fp16', help="Precision (fp32, fp16, qat; default: fp16)")
    parser.add_argument('-c', '--config_file', help="Configuration PGIE file to update")
    parser.add_argument('-l', '--label_file', help="Label file to update num-detected-classes")
    parser.add_argument('--force', action='store_true', help="Force re-generation of the engine file if it already exists")
    args = parser.parse_args()

    # Validate ONNX file
    if not os.path.isfile(args.file):
        print(f"Error: The file '{args.file}' does not exist.")
        exit(1)

    # Prepare file paths and engine names
    file_dir = os.path.dirname(args.file)
    filename = os.path.basename(args.file).replace('.onnx', '')
    engine_filename = f"{filename}-{args.precision}-netsize-{args.network_size}-batch-{args.batch_size}.engine"
    engine_timing_filename = f"{filename}-{args.precision}-netsize-{args.network_size}.engine.timing.cache"
    engine_filepath = os.path.join(file_dir, engine_filename)
    engine_timing_filepath = os.path.join(file_dir, engine_timing_filename)

    # Generate the engine
    generate_engine(args.file, engine_filepath, engine_timing_filepath, args.precision, args.batch_size, args.network_size, args.force)

    # Update configuration file if provided
    if args.config_file:
        num_detected_classes = None
        if args.label_file:
            num_detected_classes = count_labels(args.label_file)
        update_config_file(
            args.config_file,
            args.file,
            engine_filepath,
            args.batch_size,
            args.network_size,
            num_detected_classes if num_detected_classes is not None else "",
            args.label_file
        )

if __name__ == "__main__":
    main()
