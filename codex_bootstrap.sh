#!/bin/bash
set -e

echo "Cloning FreeCAD"
cd ..
git clone --depth 1 --branch main --single-branch https://github.com/FreeCAD/FreeCAD.git
cd FreeCAD

echo "Symlinking the Spring workbench"
ln -s ../FreeCAD-Spring src/Mod/Spring

echo "Patching CMakeLists to include Spring"
echo 'add_subdirectory(Spring)' >> src/Mod/CMakeLists.txt

echo "Installing dependencies with pixi"
#curl -fsSL https://pixi.sh/install.sh | sh
wget -qO- https://pixi.sh/install.sh | sh
export PATH="/root/.pixi/bin:$PATH"
pixi install
mkdir -p build/debug
pixi run build
