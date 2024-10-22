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
import sys
import json

from python_module.component.manage_sources import manage_source, list_active_media
from python_module.component.manage_models import choose_model
from python_module.component.onnx_to_trt import process_onnx
from prettytable import PrettyTable

# Define constants for colors (optional)
RED = "\033[31m"
RESET = "\033[0m"

CONFIG_FILE = 'config/python_app/save_session.json'

def load_config():
    """Load the existing configuration from a JSON file."""
    if os.path.isfile(CONFIG_FILE) and os.path.getsize(CONFIG_FILE) > 0:
        with open(CONFIG_FILE, 'r') as file:
            return json.load(file)
    return None

def save_config(config):
    """Save the configuration to a JSON file."""
    with open(CONFIG_FILE, 'w') as file:
        json.dump(config, file)

def pre_process():
    # Load previous configuration if it exists
    previous_config = load_config()

    if previous_config:
        print("Previous configuration found.")
        list_active_media()

        # Create a PrettyTable to display the model configuration
        table = PrettyTable()
        table.field_names = ["Model Type", "Model Name"]
        table.align["Model Type"] = "l"
        table.align["Model Name"] = "l"
        # Add previous configuration values to the table
        num_sources = previous_config.get("num_sources", 0)
        model_file = previous_config.get("model_file", "Not Set")
        label_file = previous_config.get("label_file", "Not Set")
        model_type = previous_config.get("model_type", "Not Set")
        
        # Insert the values into the table
        if model_type == 'det':
            model_type_table= 'Detection'
        if model_type == 'seg':
            model_type_table= 'Segmentation'
        base_name = os.path.basename(model_file)
        model_name, _ = os.path.splitext(base_name)
        table.add_row([ model_type_table, model_name])


        
        
        # Print the table
        print("\nPrevious Model Configuration:")
        print(table)

        use_previous = input("Do you want to keep the previous configuration? (y/n): ").strip().lower()

    else:
        use_previous = 'n'  # Force reconfiguration if no previous config

    if use_previous == 'y':
        # Use previous configurations
        return model_type
    else:
        # User needs to configure
        num_sources = manage_source()
        if num_sources < 1:
            sys.stderr.write(f"{RED}No active media sources were found. Please add or activate a media source before proceeding.{RESET}\n")
            return model_type

        model_file, label_file, model_type = choose_model()

    # Determine model type and configuration file based on user choice
    if model_type == "Detection":
        config_file = 'config/pgie/config_pgie_yolo_det.txt'
        model_type = "det"
    elif model_type == "Segmentation":
        config_file = 'config/pgie/config_pgie_yolo_seg.txt'
        model_type = "seg"

    # Determine precision based on the model file name
    precision = 'qat' if 'qat' in model_file else 'fp16'
    
    # Save current configurations
    current_config = {
        "num_sources": num_sources,
        "model_file": model_file,
        "label_file": label_file,
        "model_type": model_type,
        "precision": precision,
    }
    save_config(current_config)
    print("Configuration saved.")
    
    process_onnx(
        file=model_file,
        label_file=label_file,
        batch_size=num_sources,
        network_size=640,
        precision=precision,
        config_file=config_file,
        force=False
    )
    return model_type
 
