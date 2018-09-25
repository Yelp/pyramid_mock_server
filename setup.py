#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2014-2017, Yelp, Inc.

import os
from setuptools import setup

base_dir = os.path.dirname(__file__)

setup(
    name='pyramid_mock_server',
    version='1.2.0',
    license='BSD 3-Clause License',

    description='Create pyramid server that return mocked response from an OpenAPI spec',
    long_description=open(os.path.join(base_dir, 'README.md')).read(),
    url='https://github.com/Yelp/pyramid_mock_server',

    author='Yelp, Inc.',
    author_email='opensource+pyramid_mock_server@yelp.com',

    packages=['pyramid_mock_server'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    install_requires=[
        'jinja2>=2.7',
        'pyramid>=1.4',
        'six',
        'venusian>=1.0',
    ],
    extra_requires={
        'Swagger': ['pyramid_swagger >= 2.3.0'],
    },
)
