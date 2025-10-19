################################################################################
# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
################################################################################

import sys
import platform
import os
from threading import Lock

# Detect DeepStream version and configure CUDA imports accordingly
def detect_deepstream_version():
    """Detect the installed DeepStream version using deepstream-app --version."""
    import subprocess
    
    try:
        # Use deepstream-app --version to get the actual version
        result = subprocess.run(['deepstream-app', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            output = result.stdout.strip()
            # Parse version from output like "deepstream-app version 8.0.0"
            for line in output.split('\n'):
                if 'version' in line.lower():
                    # Extract version number (e.g., "8.0.0" from "deepstream-app version 8.0.0")
                    parts = line.split()
                    for part in parts:
                        if '.' in part and part.replace('.', '').isdigit():
                            version = part
                            # Return major.minor version (e.g., "8.0" from "8.0.0")
                            major_minor = '.'.join(version.split('.')[:2])
                            return major_minor
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError, Exception):
        # deepstream-app command failed or not found
        pass
    
    # Fallback: check version directories
    deepstream_root = "/opt/nvidia/deepstream/"
    if os.path.exists(deepstream_root):
        for item in os.listdir(deepstream_root):
            if item.startswith("deepstream-"):
                version = item.replace("deepstream-", "")
                if version == "7.1":
                    return "7.1"
                elif version >= "8.0":
                    return version
    
    # Fallback: try to detect by available CUDA modules
    try:
        from cuda.bindings import runtime, driver
        return "8.0"
    except ImportError:
        try:
            from cuda import cudart, cuda
            return "7.1"
        except ImportError:
            return "8.0"  # Default to 8.0+ (new standard)

# Configure CUDA imports based on DeepStream version
DEEPSTREAM_VERSION = detect_deepstream_version()

try:
    if DEEPSTREAM_VERSION == "7.1":
        # DeepStream 7.1 uses cuda-python package (legacy)
        from cuda import cudart
        from cuda import cuda
    else:
        # DeepStream 8.0+ uses cuda.bindings (new standard)
        from cuda.bindings import runtime as cudart
        from cuda.bindings import driver as cuda
except ImportError as e:
    print(f"ERROR: Failed to import CUDA modules for DeepStream {DEEPSTREAM_VERSION}: {e}")
    print("For DeepStream 7.1, ensure cuda-python==12.6.0 is installed")
    print("For DeepStream 8.0+, ensure you're using the correct virtual environment")
    sys.exit(1)

guard_platform_info = Lock()

class PlatformInfo:
    def __init__(self):
        self.is_wsl_system = False
        self.wsl_verified = False
        self.is_integrated_gpu_system = False
        self.is_integrated_gpu_verified = False
        self.is_aarch64_platform = False
        self.is_aarch64_verified = False
        self.is_jetson_nano = False
        self.is_jetson = False
        self.deepstream_version = DEEPSTREAM_VERSION

    def is_wsl(self):
        with guard_platform_info:
            if not self.wsl_verified:
                try:
                    with open("/proc/version", "r") as version_file:
                        version_info = version_file.readline().lower()
                        self.wsl_verified = True
                        if "microsoft" in version_info:
                            self.is_wsl_system = True
                except Exception as e:
                    print(f"ERROR: Opening /proc/version failed: {e}")
        return self.is_wsl_system
    
    def is_integrated_gpu(self):
        with guard_platform_info:
            if not self.is_integrated_gpu_verified:
                try:
                    if self.deepstream_version == "7.1":
                        # DeepStream 7.1 uses cuda-python API (legacy)
                        cuda_init_result, = cuda.cuInit(0)
                        if cuda_init_result == cuda.CUresult.CUDA_SUCCESS:
                            device_count_result, num_devices = cuda.cuDeviceGetCount()
                            if device_count_result == cuda.CUresult.CUDA_SUCCESS:
                                if num_devices >= 1:
                                    property_result, properties = cudart.cudaGetDeviceProperties(0)
                                    if property_result == cuda.CUresult.CUDA_SUCCESS:
                                        self.is_integrated_gpu_system = properties.integrated
                                        self.is_integrated_gpu_verified = True
                                    else:
                                        print("ERROR: Getting cuda device property failed: {}".format(property_result))
                                else:
                                    print("ERROR: No cuda devices found to check whether iGPU/dGPU")
                            else:
                                print("ERROR: Getting cuda device count failed: {}".format(device_count_result))
                        else:
                            print("ERROR: Cuda init failed: {}".format(cuda_init_result))
                    else:
                        # DeepStream 8.0+ uses cuda.bindings API (new standard)
                        cuda_init_result = cuda.cuInit(0)
                        if cuda_init_result == cuda.CUresult.CUDA_SUCCESS:
                            device_count_result, num_devices = cuda.cuDeviceGetCount()
                            if device_count_result == cuda.CUresult.CUDA_SUCCESS:
                                if num_devices >= 1:
                                    property_result, properties = cudart.cudaGetDeviceProperties(0)
                                    if property_result == cuda.CUresult.CUDA_SUCCESS:
                                        self.is_integrated_gpu_system = properties.integrated
                                        self.is_integrated_gpu_verified = True
                                    else:
                                        print("ERROR: Getting cuda device property failed: {}".format(property_result))
                                else:
                                    print("ERROR: No cuda devices found to check whether iGPU/dGPU")
                            else:
                                print("ERROR: Getting cuda device count failed: {}".format(device_count_result))
                        else:
                            print("ERROR: Cuda init failed: {}".format(cuda_init_result))
                except Exception as e:
                    print(f"ERROR: Exception in is_integrated_gpu: {e}")
        return self.is_integrated_gpu_system

    def is_platform_aarch64(self):
        if not self.is_aarch64_verified:
            if platform.uname()[4] == 'aarch64':
                self.is_aarch64_platform = True
            self.is_aarch64_verified = True
        return self.is_aarch64_platform

    def is_jetson_device(self):
        """Checks if the device is an NVIDIA Jetson."""
        if self.is_platform_aarch64():
            try:
                with open("/proc/device-tree/model", "r") as file:
                    model_info = file.read()
                    self.is_jetson = "NVIDIA Jetson" in model_info
            except FileNotFoundError:
                raise RuntimeError("ERROR: /proc/device-tree/model not found. "
                                   "Run Docker as privileged with the --privileged flag.")
        return self.is_jetson
    
    def is_jetson_nano_device(self):
        """Checks if the device is specifically a Jetson Nano."""
        if self.is_jetson_device():
            try:
                with open("/proc/device-tree/model", "r") as file:
                    model_info = file.read()
                    self.is_jetson_nano = "Orin Nano" in model_info
            except FileNotFoundError:
                raise RuntimeError("ERROR: /proc/device-tree/model not found. "
                                   "Run Docker as privileged with the --privileged flag.")
        return self.is_jetson_nano

    def get_deepstream_version(self):
        """Get the detected DeepStream version."""
        return self.deepstream_version

    def get_deepstream_lib_path(self):
        """Get the DeepStream library path (works for both 7.1 and 8.0+)."""
        return '/opt/nvidia/deepstream/deepstream/lib'


# Configure sys.path - works for both DeepStream 7.1 and 8.0+
DEEPSTREAM_VERSION = detect_deepstream_version()
sys.path.append('/opt/nvidia/deepstream/deepstream/lib')

