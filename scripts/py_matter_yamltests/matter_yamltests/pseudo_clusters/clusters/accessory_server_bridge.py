#
#    Copyright (c) 2023 Project CHIP Authors
#
#    Licensed under the Apache License, Version 2.0 (the 'License');
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an 'AS IS' BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

import sys
import xmlrpc.client

_DEFAULT_KEY = 'default'
_PORT = 9000

_IP = '10.10.10.5' if sys.platform == 'linux' else '127.0.0.1'


def _make_url():
    return f'http://{_IP}:{_PORT}/'


def _get_option(request, item_name: str, default_value=None):
    if request.arguments:
        values = request.arguments['values']
        for item in values:
            name = item['name']
            if name == item_name:
                return item['value']
    return default_value


def _get_start_options(request):
    options = []

    if request.arguments:
        values = request.arguments['values']
        for item in values:
            name = item['name']
            value = item['value']

            if name == 'discriminator':
                options.extend(('--discriminator', str(value)))
            elif name == 'port':
                options.extend(('--secured-device-port', str(value)))
            elif name == 'kvs':
                options.extend(('--KVS', str(value)))
            elif name == 'minCommissioningTimeout':
                options.extend(('--min_commissioning_timeout', str(value)))
            elif name == 'filepath':
                options.extend(('--filepath', str(value)))
            elif name == 'otaDownloadPath':
                options.extend(('--otaDownloadPath', str(value)))
            elif name != 'registerKey':
                raise KeyError(f'Unknown key: {name}')

    return options


class AccessoryServerBridge():
    def start(self):
        register_key = _get_option(self, 'registerKey', _DEFAULT_KEY)
        options = _get_start_options(self)

        with xmlrpc.client.ServerProxy(_make_url(), allow_none=True) as proxy:
            proxy.start(register_key, options)

    def stop(self):
        register_key = _get_option(self, 'registerKey', _DEFAULT_KEY)

        with xmlrpc.client.ServerProxy(_make_url(), allow_none=True) as proxy:
            proxy.stop(register_key)

    def reboot(self):
        register_key = _get_option(self, 'registerKey', _DEFAULT_KEY)

        with xmlrpc.client.ServerProxy(_make_url(), allow_none=True) as proxy:
            proxy.reboot(register_key)

    def factoryReset(self):
        register_key = _get_option(self, 'registerKey', _DEFAULT_KEY)

        with xmlrpc.client.ServerProxy(_make_url(), allow_none=True) as proxy:
            proxy.factoryReset(register_key)

    def waitForMessage(self):
        register_key = _get_option(self, 'registerKey', _DEFAULT_KEY)
        message = _get_option(self, 'message')

        with xmlrpc.client.ServerProxy(_make_url(), allow_none=True) as proxy:
            proxy.waitForMessage(register_key, [message])

    def createOtaImage(self):
        otaImageFilePath = _get_option(self, 'otaImageFilePath')
        rawImageFilePath = _get_option(self, 'rawImageFilePath')
        rawImageContent = _get_option(self, 'rawImageContent')

        with xmlrpc.client.ServerProxy(_make_url(), allow_none=True) as proxy:
            proxy.createOtaImage(otaImageFilePath, rawImageFilePath, rawImageContent)

    def compareFiles(self):
        file1 = _get_option(self, 'file1')
        file2 = _get_option(self, 'file2')

        with xmlrpc.client.ServerProxy(_make_url(), allow_none=True) as proxy:
            proxy.compareFiles(file1, file2)
