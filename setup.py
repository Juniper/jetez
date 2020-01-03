# Copyright 2018 Juniper Networks, Inc. All rights reserved
#
# Licensed under the Juniper Networks Script Software License (the "License").
# You may not use this script file except in compliance with the License, which is located at
# http://www.juniper.net/support/legal/scriptlicense/
# Unless required by applicable law or otherwise agreed to in writing by the parties,
# software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES
# OR CONDITIONS OF ANY KIND, either express or implied.
from setuptools import setup

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(name='JetEZ',
      version='0.4',
      author = "Christian Giese",
      author_email = "cgiese@juniper.net",
      url = "https://git.juniper.net/cgiese/JetEZ",
      license = "Juniper Networks Script Software License",
      packages=['jet'],
      install_requires=requirements,
      include_package_data=True,
      entry_points={
          'console_scripts': [
              'jetez = jet.main:main'
          ]
      },
      )
