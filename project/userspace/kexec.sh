#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-or-later
# Prerequisites: verified kexec-tools archive and verified Linaro toolchain.
set -euo pipefail
cache=${1:?CACHE}; out=${2:?NEW_EXTERNAL_OUT}; cross=${3:?LINARO_CROSS_PREFIX}
[ ! -e "$out" ] || { echo 'Output must be fresh' >&2; exit 1; }
mkdir -p "$out"
python3 "$(dirname "$0")/../../sources/fetch.py" --cache "$cache" --offline --name kexec-tools
tar -xJf "$cache/kexec-tools-2.0.32.tar.xz" -C "$out"
patch -d "$out/kexec-tools-2.0.32" -p1 < "$(dirname "$0")/kexec-dtb-handoff.patch"
cd "$out/kexec-tools-2.0.32"
CC="${cross}gcc" LD="${cross}ld" AS="${cross}as" AR="${cross}ar" STRIP="${cross}strip" CFLAGS=-O2 LDFLAGS=-static ./configure --host=arm-linux-gnueabi --without-zlib
make -j8
