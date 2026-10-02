#!/bin/sh
# SPDX-License-Identifier: GPL-2.0-or-later
# Usage: build.sh UPSTREAM_GIT CONFIG NEW_OUTPUT [ZQ_FRAGMENT]; no device/storage operations.
set -eu
[ "$#" = 3 ] || [ "$#" = 4 ] || { echo "usage: $0 barebox-git config new-output [zq-fragment]" >&2; exit 2; }
source=$1
config=$2
out=$3
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
[ ! -e "$out" ] || { echo "output already exists" >&2; exit 1; }
mkdir -p "$out/source" "$out/build"
git -c safe.directory="$source" -C "$source" archive v2026.09.0 | tar -x -C "$out/source"
(cd "$out/source" && patch -p1 < "$here/integration.patch")
cp "$here/zqcal.c" "$here/zqcal-sram.S" "$here/zqcal-config.h" "$here/early-trace.c" "$out/source/arch/arm/boards/kindle-mx50/"
# Distinguish upstream/runtime and per-device DCD breadcrumbs; remnants
# from the other image must never count as a fresh cold-entry marker.
python3 - "$out/source/arch/arm/boards/kindle-mx50/zqcal-trace.h" "${4:-}" <<'PY'
from pathlib import Path
import sys
pu, pd = 23, 8
if sys.argv[2]:
    import re
    rows = re.findall(r'wm 32 0x1400012[cC] 0x([0-9a-fA-F]+)', Path(sys.argv[2]).read_text())
    assert len(rows) == 1
    value = int(rows[0], 16); pu, pd = value & 31, (value >> 8) & 15
Path(sys.argv[1]).write_bytes(('#define K4_ZQ_TRACE_ID 0x%08xU\n' % (0x5a510000 | pu << 8 | pd)).encode())
PY
# Earliest D01100 entry runs after ROM DCD, before stack/DDR entry.
python3 - "$out/source/arch/arm/boards/kindle-mx50/lowlevel.c" <<'PY'
from pathlib import Path
import sys
p = Path(sys.argv[1]); s = p.read_text().replace('#include <common.h>', '#include <common.h>\n#include "zqcal-trace.h"')
needle = '\tfdt = __dtb_imx50_kindle_d01100_start + get_runtime_offset();'
assert s.count(needle) == 1
# A 3-word magic/stage/complement survives without DDR access; no stack needed.
entry = '\timx5_cpu_lowlevel_init();'
pos = s.index(entry, s.index('ENTRY_FUNCTION(start_imx50_kindle_d01100'))
s = s[:pos] + '\twritel(K4_ZQ_TRACE_ID, (void *)0xf8007b1c);\n\twritel(0x4b345a54, (void *)0xf8007b00);\n\twritel(1, (void *)0xf8007b04);\n\twritel(~1U, (void *)0xf8007b08);\n' + s[pos:]
s = s.replace(needle, '\twritel(2, (void *)0xf8007b04);\n\twritel(~2U, (void *)0xf8007b08);\n' + needle)
p.write_bytes(s.encode())
PY
# No profile means unchanged upstream ZQ; a machine profile is always explicit.
if [ "$#" = 4 ]; then
 python3 "$here/zq_profile.py" apply --profile "$4" --header "$out/source/arch/arm/boards/kindle-mx50/flash-header-kindle-lpddr1.imxcfg"
 cp "$4" "$out/selected-zq.imxcfg"
fi
# Diagnostic image: always expose USB serial, and never autoboot a disk kernel.
cp "$here/usbconsole-diagnostic" "$out/source/arch/arm/boards/kindle-mx50/defaultenv-kindle-mx50/init/usbconsole"
cp "$config" "$out/build/.config"
printf '\nCONFIG_CMD_ZQCAL=y\nCONFIG_WATCHDOG_POLLER=y\n' >> "$out/build/.config"
make -C "$out/source" O="$(cd "$out/build" && pwd)" ARCH=arm CROSS_COMPILE="${CROSS_COMPILE:-arm-linux-gnueabihf-}" olddefconfig
make -C "$out/source" O="$(cd "$out/build" && pwd)" ARCH=arm CROSS_COMPILE="${CROSS_COMPILE:-arm-linux-gnueabihf-}" -j"${JOBS:-8}"
