#!/usr/bin/env python3
"""
Setup script for building the Windows Thread Pool module as a standalone extension.

This allows testing the module without integrating it into the main CPython build.
"""

from distutils.core import setup, Extension
import sys
import os

# Ensure we're on Windows
if sys.platform != 'win32':
    print("Error: This module is Windows-only")
    sys.exit(1)

# Define the extension module
threadpool_module = Extension(
    '_threadpool',
    sources=['Modules/threadpoolmodule_simple.c'],
    libraries=['kernel32'],
    define_macros=[
        ('WIN32_LEAN_AND_MEAN', None),
        ('_WIN32_WINNT', '0x0600'),  # Windows Vista or later
    ],
    extra_compile_args=['/W3'],  # Enable warnings for MSVC
)

setup(
    name='threadpool',
    version='1.0',
    description='Windows Thread Pool API for Python',
    author='CPython Development',
    ext_modules=[threadpool_module],
    python_requires='>=3.12',
)

# Instructions for building
if __name__ == '__main__':
    print("""
Windows Thread Pool Module Build Script
========================================

To build the module:
1. Ensure you have a C compiler (Visual Studio or Build Tools)
2. Run: python setup_threadpool.py build_ext --inplace
3. Test with: python test_simple_threadpool.py

Build directory structure should be:
./
├── Modules/
│   └── threadpoolmodule_simple.c
├── setup_threadpool.py
└── test_simple_threadpool.py

Make sure the Modules/ directory exists and contains threadpoolmodule_simple.c
    """) 