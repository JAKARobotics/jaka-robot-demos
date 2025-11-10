@echo off
@REM # Return to the project root directory
cd /d %~dp0
cd ..\..

@REM # Create a python virtual environment and enter
call python -m venv ./venv
call venv\Scripts\activate

@REM # Install required libraries
call python -m pip install -r requirements.txt
call python -m pip install setuptools

@REM # Remove ./build directory
@REM cd ..
rmdir /s /q build

@REM # Create build directory and navigate into it
mkdir build
cd build

@REM # Run CMake
cmake -Dpybind11_DIR=./venv/Lib/site-packages/pybind11/share/cmake/pybind11 ..

@REM # Build Release with cmake
cmake --build . --config Release

@REM # Move back to the parent directory
cd ..

@REM # Remove old /install directory and create new /install/lib directory
rmdir /s /q install
mkdir ./install/lib/pyorbbecsdk/examples
mkdir ./install/lib/pyorbbecsdk/config

@REM # Copy shared objects (*.pyd) from /build to /install/lib
robocopy ./build/Release/ ./install/lib/ *.pyd /E

@REM # Copy all c++ librarys except *.cmake to /install/lib
robocopy ./sdk/lib/win_x64/ ./install/lib/ /E

@REM # Copy examples to /install/lib
robocopy ./examples/ ./install/lib/pyorbbecsdk/examples /S
robocopy ./config ./install/lib/pyorbbecsdk/config /S
copy requirements.txt install\lib\pyorbbecsdk\examples

@REM # Run Python setup.py to build a wheel package
python setup.py bdist_wheel

@REM # Exit python virtual env
@REM call deactivate

