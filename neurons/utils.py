"""
The MIT License (MIT)
Copyright © 2023 Chris Wilson

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the “Software”), to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of
the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""
import requests


    
def get_remote_version():
    url = "https://raw.githubusercontent.com/zktensor/zktensor_subnet/main/__init__.py"
    response = requests.get(url)

    if response.status_code == 200:
        lines = response.text.split('\n')
        for line in lines:
            if line.startswith('__version__'):
                version_info = line.split('=')[1].strip(' "\'')
                return version_info
    else:
        print("Failed to get file content")
        return 0

def get_local_version():
    with open('__init__.py', 'r') as file:
        lines = file.readlines()
        for line in lines:
            if line.startswith('__version__'):
                version_info = line.split('=')[1].strip(' "\'')
                return version_info
    return None

def check_version():
    pass
def update_repo():
    pass