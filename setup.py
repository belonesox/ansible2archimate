#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
 Setup for the package
"""

from setuptools import setup
setup(
    entry_points={
        'console_scripts': [
            'ansible2archimate=ansible2archimate:ansible2archimate',
        ],
    },
    name='ansible2archimate',
    version='0.95',
    packages=['ansible2archimate'],
    package_dir={'ansible2archimate': 'ansible2archimate'},
    package_data={'ansible2archimate': ['template/*.*']},
    author_email = "stanislav.fomin@gmail.com",
)

