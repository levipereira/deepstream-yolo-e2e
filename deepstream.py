#!/usr/bin/python3
"""
Creative Commons Attribution-NonCommercial 4.0 International License

You are free to share and adapt the material under the following terms:
- Attribution: Give appropriate credit.
- NonCommercial: Not for commercial use without permission.

For inquiries: levi.pereira@gmail.com
Repository: DeepStream / YOLO (https://github.com/levipereira/deepstream-yolo-e2e)
License: https://creativecommons.org/licenses/by-nc/4.0/legalcode
"""

import sys
import argparse
from prettytable import PrettyTable
from python_module.component.pipeline import run_pipeline
from python_module.common.utils import clear_screen
from python_module.common.platform_info import PlatformInfo
import os

os.environ['GST_DEBUG'] = 'ERROR'  
os.system('stty sane')

def display_output_options():
    """Display available output options to the user in a table format."""
    platform_info = PlatformInfo()
    table = PrettyTable()
    table.field_names = ["Index", "Output Option", "Description"]
    table.align["Index"] = "l"
    table.align["Output Option"] = "l"
    table.align["Description"] = "l"

    options = [
        ("1", "display", "Output to display window"),
        ("2", "file", "Save output to a file"),
        ("3", "rtsp", "Stream output via RTSP"),
        ("4", "silent", "No output"),
    ]
    
    # Check if display option should be disabled (DeepStream 8.0 + WSL)
    if platform_info.is_wsl() and platform_info.get_deepstream_version() >= "8.0":
        # Mark display option as disabled but keep it visible
        options[0] = ("1", "display (DISABLED)", "Output to display window - Not available on WSL")
    
    for option in options:
        table.add_row(option)

    print("Please choose the output option:")
    print(table)
    
    # Show note at the bottom if display option was disabled
    if platform_info.is_wsl() and platform_info.get_deepstream_version() >= "8.0":
        print("Note: Display option disabled on DeepStream 8.0 + WSL due to MESA X11 compatibility issues")

def display_encoding_options():
    """Display available encoding options to the user in a table format."""
    table = PrettyTable()
    table.field_names = ["Index", "Encoding Option", "Description"]
    table.align["Index"] = "l"
    table.align["Encoding Option"] = "l"
    table.align["Description"] = "l"

    options = [
        ("1", "cpu", "CPU encoding (default)"),
        ("2", "gpu", "GPU encoding (hardware accelerated)"),
    ]
    
    for option in options:
        table.add_row(option)

    print("Please choose the encoding option:")
    print(table)

def get_user_choice():
    """Get the user's choice for output option."""
    platform_info = PlatformInfo()
    
    # Define all options with original indices
    all_options = ["display", "file", "rtsp", "silent"]
    
    while True:
        try:
            choice = int(input("Enter the number corresponding to your choice: "))
            if choice in range(1, 5):  # Valid choices are 1-4
                selected_option = all_options[choice - 1]
                
                # Check if display option was selected on WSL + DeepStream 8.0
                if (selected_option == "display" and 
                    platform_info.is_wsl() and 
                    platform_info.get_deepstream_version() >= "8.0"):
                    print("Error: Display option is not available on DeepStream 8.0 + WSL due to MESA X11 compatibility issues")
                    print("Please select a different option.")
                    continue
                
                return selected_option
            else:
                print("Invalid choice. Please select a number between 1 and 4.")
        except ValueError:
            print("Invalid input. Please enter a valid number.")
        except KeyboardInterrupt:
            print("\nInput interrupted. Exiting application.")
            sys.exit(0)

def get_encoding_choice():
    """Get the user's choice for encoding option."""
    while True:
        try:
            choice = int(input("Enter the number corresponding to your choice: "))
            if choice in range(1, 3):  # Valid choices are 1-2
                return ["cpu", "gpu"][choice - 1]
            else:
                print("Invalid choice. Please select a number between 1 and 2.")
        except ValueError:
            print("Invalid input. Please enter a valid number.")
        except KeyboardInterrupt:
            print("\nInput interrupted. Exiting application.")
            sys.exit(0)

def parse_args():
    platform_info = PlatformInfo()
    
    parser = argparse.ArgumentParser(prog="pipeline_yolo.py",
                                     description="pipeline_yolo multi stream, multi model inference reference app")
    
    # Adding the output argument as optional
    parser.add_argument(
        "-o",
        "--output",
        help="Output",
        choices=["display", "file", "rtsp", "silent"],
    )
    
    # Adding the encoding argument as optional
    parser.add_argument(
        "-e",
        "--encoding",
        help="Encoding type (only valid for file and rtsp outputs)",
        choices=["cpu", "gpu"],
        default="cpu",
    )

    # Parse arguments
    args = parser.parse_args()

    # Validate display option for DeepStream 8.0 on WSL
    if args.output == "display" and platform_info.is_wsl() and platform_info.get_deepstream_version() >= "8.0":
        print("Error: Display option is not available on DeepStream 8.0 + WSL due to MESA X11 compatibility issues")
        print("Available options: file, rtsp, silent")
        sys.exit(1)

    # If the user provided an output option via the command line, use it.
    if args.output:
        # If output is file or rtsp and no encoding specified, ask for encoding choice
        if args.output in ["file", "rtsp"] and not hasattr(args, 'encoding'):
            display_encoding_options()
            selected_encoding = get_encoding_choice()
            args.encoding = selected_encoding
        return args

    # Otherwise, prompt the user for the output option.
    display_output_options()
    selected_output = get_user_choice()
    
    
    # If output is file or rtsp, ask for encoding choice
    if selected_output in ["file", "rtsp"]:
        display_encoding_options()
        selected_encoding = get_encoding_choice()
        return argparse.Namespace(output=selected_output, encoding=selected_encoding)
    
    return argparse.Namespace(output=selected_output, encoding="cpu")

if __name__ == '__main__':
    clear_screen()
    try:
        args = parse_args()
        sys.exit(run_pipeline(args))
    except KeyboardInterrupt:
        os.system('stty sane')
        print("\nApplication terminated by user.")
        sys.exit(0)
