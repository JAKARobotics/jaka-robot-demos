#!/bin/bash
#------------------------------------------------------------------------------
# Build Script for Pybind11 Project
#------------------------------------------------------------------------------
# REQUIREMENTS:
# 1. One or more Python versions (3.9-3.13) installed in system
# 2. CMake installed and available in PATH
#------------------------------------------------------------------------------
PY_VERSIONS=("3.8" "3.9" "3.10" "3.11" "3.12" "3.13")

# Install directories
rm -rf ./install

# Prepare install directory
INSTALL_DIR=./install/lib/pyorbbecsdk
mkdir -p "$INSTALL_DIR"

# Copy examples, config, requirements
cp -r ./examples "$INSTALL_DIR"
cp -r ./config "$INSTALL_DIR"
cp ./requirements.txt "$INSTALL_DIR"/examples

# build
for py_version in "${PY_VERSIONS[@]}"; do
    echo "Building for Python $py_version..."
    
    # Clean old build and create
    rm -rf ./build
    mkdir -p build
    
    # python path
    python_path=$(which python${py_version})
    if [ ! -x "$python_path" ]; then
        echo "Python ${py_version} not found, skipping."
        cd ..
        continue
    fi
    
    # Installing dependencies...
    # "$python_path" -m pip install -r ./requirements.txt

    # pybind11 dir
    pybind11_dir=$("$python_path" -m pybind11 --cmakedir 2>/dev/null)
    if [ -z "$pybind11_dir" ]; then
        echo "pybind11 not installed for Python ${py_version}, skipping."
        cd ..
        continue
    fi

    # Configure and build
    cd build
    if ! cmake .. -DPython3_EXECUTABLE="$python_path" -Dpybind11_DIR="$pybind11_dir"; then
        echo "CMake failed for Python ${py_version}, skipping."
        cd ..
        continue
    fi

    if ! make -j"$(nproc)"; then
        echo "Make failed for Python ${py_version}, skipping."
        cd ..
        continue
    fi

    make install

    cd ..

    # Build wheel
    if ! "$python_path" setup.py bdist_wheel; then
        echo "Wheel build failed for Python ${py_version}, skipping."
        continue
    fi

    # # repair whl
    # if ! auditwheel repair ./dist/*.whl; then
    #     echo "Auditwheel failed for Python ${py_version}, skipping."
    # fi
    
    # Clean pyorbbec*.so
    rm -f ./install/lib/pyorbbec*.so

    echo "Python ${py_version} wheel build done"
done

echo "All whl generated"
