#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-or-later
# Static ARM nl80211 tools; all third-party sources/output stay outside Git.
set -euo pipefail
repo=$(cd "$(dirname "$0")" && pwd)
cache=${1:?CACHE}
out=${2:?OUT}
cross=arm-linux-gnueabihf-
export SOURCE_DATE_EPOCH=1790812800
mapflags="-ffile-prefix-map=$out=/build/k4-wifi -fdebug-prefix-map=$out=/build/k4-wifi"
mkdir -p "$out/work" "$out/bin"
cd "$cache"
python3 "$repo/../../sources/fetch.py" --cache "$cache" --offline --name wpa_supplicant --name libnl --name iw
if [ ! -d "$out/work/libnl-3.12.0" ]; then
	tar -xzf libnl-3.12.0.tar.gz -C "$out/work"
fi
if [ ! -d "$out/work/wpa_supplicant-2.12" ]; then
	tar -xzf wpa_supplicant-2.12.tar.gz -C "$out/work"
fi
patch_file="$repo/wpa-aborted-scan-retry.patch"
wpa_dir="$out/work/wpa_supplicant-2.12"
if patch -d "$wpa_dir" -p1 --batch --forward --dry-run < "$patch_file" >/dev/null; then
	patch -d "$wpa_dir" -p1 --batch --forward < "$patch_file"
elif ! patch -d "$wpa_dir" -p1 --batch --reverse --dry-run < "$patch_file" >/dev/null; then
	echo 'WPA aborted-scan patch does not match the work sources' >&2
	exit 1
fi
cd "$out/work/libnl-3.12.0"
./configure --host=arm-linux-gnueabihf --prefix="$out/prefix" \
	--disable-shared --enable-static --disable-cli --disable-pthreads \
	CFLAGS="-O2 -mno-unaligned-access $mapflags" > "$out/libnl-configure.log" 2>&1
make -j8 > "$out/libnl-build.log" 2>&1
make install > "$out/libnl-install.log" 2>&1
cd "$out/work/wpa_supplicant-2.12/wpa_supplicant"
cp "$repo/wpa.config" .config
export PKG_CONFIG_LIBDIR="$out/prefix/lib/pkgconfig"
make -j8 CC="${cross}gcc" EXTRA_CFLAGS="-O2 -mno-unaligned-access $mapflags" \
	LDFLAGS="-static -Wl,--build-id=sha1 -L$out/prefix/lib" wpa_supplicant wpa_cli > "$out/wpa-build.log" 2>&1
for program in wpa_supplicant wpa_cli; do
	cp "$program" "$out/bin/$program"
	"${cross}strip" --strip-unneeded "$out/bin/$program"
done
if [ ! -d "$out/work/iw-6.17" ]; then
	tar -xJf "$cache/iw-6.17.tar.xz" -C "$out/work"
fi
cd "$out/work/iw-6.17"
make -j8 CC="${cross}gcc -mno-unaligned-access $mapflags" \
	LDFLAGS="-static -Wl,--build-id=sha1 -L$out/prefix/lib" > "$out/iw-build.log" 2>&1
cp iw "$out/bin/iw"
"${cross}strip" --strip-unneeded "$out/bin/iw"
file "$out/bin/"*
sha256sum "$out/bin/"* > "$out/SHA256SUMS"
cat "$out/SHA256SUMS"
