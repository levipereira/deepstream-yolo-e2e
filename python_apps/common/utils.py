################################################################################
# SPDX-FileCopyrightText: Copyright (c) 2019-2021 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

import ctypes
import sys
import os
import configparser
sys.path.append('/opt/nvidia/deepstream/deepstream/lib')

def long_to_uint64(l):
    value = ctypes.c_uint64(l & 0xffffffffffffffff).value
    return value

def parse_config(config_file):
    config = configparser.ConfigParser()
    config.read(config_file)

    media_entries = []

    for section in config.sections():
        enable = config.getint(section, 'enable')
        if enable == 1:
            type = config.get(section, 'type')
            url = config.get(section, 'url')

            if not os.path.isfile(url) and type == 'file':
                print(f"File not found: {url}")
            if type == "file":
                url = f"file://{url}"
            media_entries.append((type, url))
    return media_entries


 