#------------------------------------------------------------------------------
# Build Script for Pybind11 Project
#------------------------------------------------------------------------------
# REQUIREMENTS:
# 1. One or more Python versions (3.9-3.13) installed in:
#    %LOCALAPPDATA%\Programs\Python\Python<version>
# 2. CMake installed and available in PATH
#------------------------------------------------------------------------------

# Project root directory
Set-Location -Path $PSScriptRoot
Set-Location -Path ..\..

# Python versions to target
$pythonVersions = @(38, 39, 310, 311, 312, 313)

# Directory setup
$buildDir = "build"
$installDir = "install"
$installLibDir = "install/lib"
$exampleDstDir = "$installLibDir/pyorbbecsdk/examples"
$configDstDir = "$installLibDir/pyorbbecsdk/config"

# Clean install dir
if (Test-Path -Path $installDir) {
    Write-Host "Removing existing install directory..."
    Remove-Item -Path $installDir -Recurse -Force -ErrorAction SilentlyContinue
}

# Recreate install directory structure
Write-Host "Creating install subdirectories..."
New-Item -ItemType Directory -Force -Path $exampleDstDir, $configDstDir | Out-Null

# Copy assets
$copyTasks = @(
    @{ Src = "examples\*"; Dst = $exampleDstDir },
    @{ Src = "config\*"; Dst = $configDstDir },
    @{ Src = "requirements.txt"; Dst = $exampleDstDir }
)

foreach ($task in $copyTasks) {
    if (Test-Path $task.Src) {
        Write-Host "Copying $($task.Src)..."
        Copy-Item -Path $task.Src -Destination $task.Dst -Recurse -Force
    }
}

# Copy all C++ libraries except *.cmake to install/lib
Copy-Item -Path "sdk\lib\win_x64\*" -Destination "install\lib\" -Recurse -Force -Exclude *.cmake

# Build for each Python version
foreach ($version in $pythonVersions) {
    $pythonPath = "$env:LOCALAPPDATA\Programs\Python\Python$version\python.exe"
    $venvDir = "venv$version"
    $venvPythonPath = ".\$venvDir\Scripts\python.exe"

    # Clean up the build directory if it exists
    if (Test-Path -Path $buildDir) {
        Write-Host "`nRemoving existing build directory..."
        Remove-Item -Path $buildDir -Recurse -Force -ErrorAction SilentlyContinue
    }

    # Create a fresh build directory
    Write-Host "`nCreating build directory..."
    New-Item -ItemType Directory -Path $buildDir | Out-Null

    try {
        if (-not (Test-Path $pythonPath)) {
            Write-Warning "`nPython executable not found for version $version"
            continue
        }

        # Create virtual environment
        Write-Host "[Python $version] Creating virtual environment..."
        & $pythonPath -m venv $venvDir

        if (-not (Test-Path $venvPythonPath)) {
            Write-Warning "Virtual environment Python not found: $venvPythonPath"
            continue
        }

        Write-Host "Installing dependencies..."
        & $venvPythonPath -m pip install --upgrade pip setuptools > $null
        & $venvPythonPath -m pip install -r requirements.txt > $null

        $pybind11Dir = & $venvPythonPath -m pybind11 --cmakedir
        if (-not $pybind11Dir) {
            Write-Warning "Failed to get pybind11 cmake dir for Python $version"
            continue
        }
        Write-Host "Using pybind11 cmake dir: $pybind11Dir"

        # Configure and build
        Set-Location -Path $buildDir
        cmake .. -DPython3_EXECUTABLE="$pythonPath" -Dpybind11_DIR="$pybind11Dir"
        cmake --build . --config Release
        Set-Location ..

        # Copy built .pyd
        Copy-Item "$buildDir/Release/*.pyd" -Destination $installLibDir -Force -ErrorAction SilentlyContinue

        # Build wheel
        Write-Host "`nBuilding wheel for Python $version..."
        & $venvPythonPath setup.py bdist_wheel
        Write-Host "Build completed for Python $version" -ForegroundColor Cyan

        # Clean .pyd
        Get-ChildItem -Path $installLibDir -Filter "*.pyd" -Recurse | Remove-Item -Force -ErrorAction SilentlyContinue
    }
    catch {
        Write-Host "[Error] Build failed for Python ${version}: $_" -ForegroundColor Red

        # Ensure we return even on failure
        Set-Location ..
    }
}

Write-Host "`nAll Python versions processing completed!" -ForegroundColor Green