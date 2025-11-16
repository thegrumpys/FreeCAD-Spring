#!/bin/bash
set -e

# Clone FreeCAD
cd ..
git clone --depth 1 --branch main --single-branch https://github.com/FreeCAD/FreeCAD.git
cd FreeCAD

# Symlink your workbench
ln -s ../FreeCAD-Spring src/Mod/Spring

# Patch CMakeLists to add Spring
echo 'add_subdirectory(Spring)' >> src/Mod/CMakeLists.txt

# Install using pixi
curl -fsSL https://pixi.sh/install.sh | sh
export PATH="/root/.pixi/bin:$PATH"
pixi install
mkdir -p build/debug
pixi run build
