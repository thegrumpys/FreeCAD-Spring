#!/usr/bin/env bash
set -e

echo "Disabling SSL verification inside Codex..."
git config --global http.sslVerify false

echo "Cloning FreeCAD repository..."
cd ..
#git clone --depth 1 --branch main --single-branch https://github.com/FreeCAD/FreeCAD.git
git clone --filter=blob:none https://github.com/FreeCAD/FreeCAD.git
cd FreeCAD

echo "Creating pixi cache and home directories (Codex-safe)..."
mkdir -p /tmp/pixi-cache
mkdir -p /tmp/pixi-home

export PIXI_CACHE_DIR="/tmp/pixi-cache"
export PIXI_HOME="/tmp/pixi-home"

echo "Installing pixi runtime..."
wget -qO- https://pixi.sh/install.sh | sh

export PATH="/tmp/pixi-home/bin:$PATH"

echo "Installing pixi dependencies..."
pixi config set --local run-post-link-scripts insecure
pixi --no-progress install

echo "Configuring and building FreeCAD..."
mkdir -p build/debug
pixi --no-progress run configure
pixi --no-progress run build    # <-- this builds FreeCAD, but excludes Spring

echo "Symlinking FreeCAD-Spring workbench..."
ln -s ../FreeCAD-Spring src/Mod/Spring

echo "Adding Spring to CMakeLists.txt..."
echo 'add_subdirectory(Spring)' > src/Mod/CMakeLists.txt

echo "export PIXI_CACHE_DIR=/tmp/pixi-cache"
echo "export PIXI_HOME=/tmp/pixi-home"
echo "export PATH=/tmp/pixi-home/bin:\$PATH"
