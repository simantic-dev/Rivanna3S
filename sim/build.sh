#!/bin/sh
# Builds the five unmodified firmware images into sim/build/bin. The repo's
# cmake/arm-gcc.cmake hard-codes /usr/bin, so a copy with the toolchain path is
# written into the build directory; nothing in the firmware tree changes.
# usage: sim/build.sh [path-to-arm-gnu-toolchain/bin]   (default: from PATH)
set -e
cd "$(dirname "$0")/.."
TC=${1:-$(dirname "$(command -v arm-none-eabi-gcc)")}
mkdir -p sim/build
sed "s|^set(ARM_TOOLCHAIN_PATH .*|set(ARM_TOOLCHAIN_PATH \"$TC\")|" cmake/arm-gcc.cmake > sim/build/arm-gcc-local.cmake
cmake -S . -B sim/build -G Ninja -DCMAKE_TOOLCHAIN_FILE="$PWD/sim/build/arm-gcc-local.cmake" \
  -DCMAKE_BUILD_TYPE=Debug -DBOARD=STM32G474RET6
cmake --build sim/build
