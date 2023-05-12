# Copyright (c) 2021 Project CHIP Authors
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

import os
import re
import shlex
from enum import Enum, auto

from .gn import GnBuilder


class IMXApp(Enum):
    CHIP_TOOL = auto()
    LIGHT = auto()
    THERMOSTAT = auto()
    ALL_CLUSTERS = auto()
    ALL_CLUSTERS_MINIMAL = auto()
    OTA_PROVIDER = auto()

    def ExamplePath(self):
        if self == IMXApp.CHIP_TOOL:
            return 'chip-tool'
        if self == IMXApp.LIGHT:
            return 'lighting-app/linux'
        if self == IMXApp.THERMOSTAT:
            return 'thermostat/linux'
        if self == IMXApp.ALL_CLUSTERS:
            return 'all-clusters-app/linux'
        if self == IMXApp.ALL_CLUSTERS_MINIMAL:
            return 'all-clusters-minimal-app/linux'
        if self == IMXApp.OTA_PROVIDER:
            return 'ota-provider-app/linux'

    def OutputNames(self):
        if self == IMXApp.CHIP_TOOL:
            yield 'chip-tool'
            yield 'chip-tool.map'
        if self == IMXApp.LIGHT:
            yield 'chip-lighting-app'
            yield 'chip-lighting-app.map'
        if self == IMXApp.THERMOSTAT:
            yield 'thermostat-app'
            yield 'thermostat-app.map'
        if self == IMXApp.ALL_CLUSTERS:
            yield 'chip-all-clusters-app'
            yield 'chip-all-clusters-app.map'
        if self == IMXApp.ALL_CLUSTERS_MINIMAL:
            yield 'chip-all-clusters-minimal-app'
            yield 'chip-all-clusters-minimal-app.map'
        if self == IMXApp.OTA_PROVIDER:
            yield 'chip-ota-provider-app'
            yield 'chip-ota-provider-app.map'


class IMXBuilder(GnBuilder):

    def __init__(self,
                 root,
                 runner,
                 app: IMXApp,
                 release: bool = False):
        super(IMXBuilder, self).__init__(
            root=os.path.join(root, 'examples', app.ExamplePath()),
            runner=runner)
        self.release = release
        self.app = app

    def GnBuildArgs(self):
        try:
            entries = os.listdir(self.SysRootPath('IMX_SDK_ROOT'))
        except FileNotFoundError:
            if self.SysRootPath('IMX_SDK_ROOT') != 'IMX_SDK_ROOT':
                raise Exception('the value of env IMX_SDK_ROOT is not a valid path.')
            # CI test, use default value
            target_cpu = 'arm64'
            arm_arch = 'armv8-a'
            sdk_target_sysroot = os.path.join(self.SysRootPath('IMX_SDK_ROOT'), 'sysroots/cortexa53-crypto-poky-linux')
            cross_compile = 'aarch64-poky-linux'
            cc = 'aarch64-poky-linux-gcc'
            cxx = 'aarch64-poky-linux-g++'
        else:
            for entry in entries:
                if entry.startswith(r'environment-setup-'):
                    env_setup_script = entry
                    break

            try:
                env_setup_script
            except NameError:
                raise Exception('The SDK environment setup script is not found, make sure the env IMX_SDK_ROOT is correctly set.')
            else:

                with open(os.path.join(self.SysRootPath('IMX_SDK_ROOT'), env_setup_script), 'r') as env_setup_script_fd:
                    lines = env_setup_script_fd.readlines()
                    for line in lines:
                        line = line.strip('\n')
                        if m := re.match(
                            r'^\s*export\s+SDKTARGETSYSROOT=(.*)', line
                        ):
                            sdk_target_sysroot = shlex.split(m[1])[0]

                        if m := re.match(r'^\s*export\s+CC=(.*)', line):
                            cc = shlex.split(m[1])[0]
                        if m := re.match(r'^\s*export\s+CXX=(.*)', line):
                            cxx = shlex.split(m[1])[0]

                        if m := re.match(r'^\s*export\s+ARCH=(.*)', line):
                            target_cpu = shlex.split(m[1])[0]
                            if target_cpu == 'arm64':
                                arm_arch = 'armv8-a'
                            elif target_cpu == 'arm':
                                arm_arch = 'armv7ve'
                            else:
                                raise Exception('ARCH should be arm64 or arm in the SDK environment setup script.')

                        if m := re.match(r'^\s*export\s+CROSS_COMPILE=(.*)', line):
                            cross_compile = shlex.split(m[1])[0][:-1]

                try:
                    sdk_target_sysroot
                except NameError:
                    raise Exception('SDKTARGETSYSROOT is not found in the SDK environment setup script.')
                else:
                    try:
                        cc
                        cxx
                    except NameError:
                        raise Exception('CC and/or CXX are not found in the SDK environment setup script.')
                    else:
                        cc = cc.replace('$SDKTARGETSYSROOT', sdk_target_sysroot)
                        cxx = cxx.replace('$SDKTARGETSYSROOT', sdk_target_sysroot)
                try:
                    target_cpu
                    cross_compile
                except NameError:
                    raise Exception('ARCH and/or CROSS_COMPILE are not found in the SDK environment setup script.')

        args = [
            'treat_warnings_as_errors=false',
            'target_os="linux"',
            f'target_cpu="{target_cpu}"',
            f'arm_arch="{arm_arch}"',
            'import(\"//build_overrides/build.gni\")',
            'custom_toolchain=\"${build_root}/toolchain/custom\"',
            f'sysroot="{sdk_target_sysroot}"',
            'target_cflags=[ "-DCHIP_DEVICE_CONFIG_WIFI_STATION_IF_NAME=\\"mlan0\\"", "-DCHIP_DEVICE_CONFIG_LINUX_DHCPC_CMD=\\"udhcpc -b -i %s \\"" ]',
            f"""target_cc="{self.SysRootPath('IMX_SDK_ROOT')}/sysroots/x86_64-pokysdk-linux/usr/bin/{cross_compile}/{cc}\"""",
            f"""target_cxx="{self.SysRootPath('IMX_SDK_ROOT')}/sysroots/x86_64-pokysdk-linux/usr/bin/{cross_compile}/{cxx}\"""",
            f"""target_ar="{self.SysRootPath('IMX_SDK_ROOT')}/sysroots/x86_64-pokysdk-linux/usr/bin/{cross_compile}/{cross_compile}-ar\"""",
        ]

        if self.release:
            args.append('is_debug=false')
        else:
            args.append('optimize_debug=true')

        return args

    def SysRootPath(self, name):
        if name not in os.environ:
            raise Exception(f'Missing environment variable "{name}"')
        return os.environ[name]

    def build_outputs(self):
        outputs = {}

        for name in self.app.OutputNames():
            path = os.path.join(self.output_dir, name)
            if os.path.isdir(path):
                for root, dirs, files in os.walk(path):
                    for file in files:
                        outputs[file] = os.path.join(root, file)
            else:
                outputs[name] = os.path.join(self.output_dir, name)

        return outputs
