#!/bin/sh
# SPDX-License-Identifier: GPL-2.0-only
# Offline only. All generated files must live in this worktree.
set -eu
[ "$(id -un)" = kindle ] || exit 1
[ "$#" = 5 ] || { echo "usage: $0 upstream-git frozen-usb-config usb-image new-output stock-boot0-reference" >&2; exit 2; }
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
root=$(git -C "$here" rev-parse --show-toplevel)
out=$(realpath -m "$4")
[ ! -e "$out" ] || exit 1
mkdir -p "$out/source" "$out/build"
git -C "$1" archive v2026.09.0 | tar -x -C "$out/source"
cp "$2" "$out/build/.config"
chmod u+w "$out/build/.config"
python3 "$here/prepare.py" "$out/source"
cp "$here/boot-trace.c" "$out/source/arch/arm/boards/kindle-mx50/"
cp "$here/usbconsole" "$out/source/arch/arm/boards/kindle-mx50/defaultenv-kindle-mx50/init/usbconsole"
# Use upstream MCI unchanged; probe nonremovable eMMC, no persistent environment.
for sym in MCI_STARTUP CMD_MMC_EXTCSD USB_GADGET_DFU DEFAULT_ENVIRONMENT_GENERIC_NEW_DFU ENV_HANDLING_AUTOPROBE CMD_SAVEENV CMD_LOADENV ENV_HANDLING CMD_DFU USB_GADGET_FASTBOOT USB_GADGET_MASS_STORAGE; do
 sed -i "/^CONFIG_${sym}=/d; /^# CONFIG_${sym} is not set/d" "$out/build/.config"
 printf '# CONFIG_%s is not set\n' "$sym" >> "$out/build/.config"
done
sed -i '/^CONFIG_MCI_STARTUP_NONE=/d; /^# CONFIG_MCI_STARTUP_NONE is not set/d; /^CONFIG_WATCHDOG_POLLER=/d; /^# CONFIG_WATCHDOG_POLLER is not set/d' "$out/build/.config"
printf '\nCONFIG_MCI_STARTUP_NONREMOVABLE=y
CONFIG_CMD_SLEEP=y\nCONFIG_WATCHDOG_POLLER=y\n' >> "$out/build/.config"
sed -i '/^CONFIG_MCI_STARTUP_NONE=/d; /^# CONFIG_MCI_STARTUP_NONREMOVABLE is not set/d; /^# CONFIG_CMD_SLEEP is not set/d' "$out/build/.config"
printf '# CONFIG_MCI_STARTUP_NONE is not set\n' >> "$out/build/.config"
cp "$here/usbconsole-v8" "$out/source/arch/arm/boards/kindle-mx50/defaultenv-kindle-mx50/init/usbconsole"
cp "$here/emmc-v8" "$out/source/arch/arm/boards/kindle-mx50/defaultenv-kindle-mx50/boot/emmc"
cp "$here/host-ram-v7" "$out/source/arch/arm/boards/kindle-mx50/defaultenv-kindle-mx50/boot/host-ram"
make -C "$out/source" O="$out/build" ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- olddefconfig
make -C "$out/source" O="$out/build" ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- -j8
python3 "$here/build-plugin.py" "$out/build/images/barebox-kindle-d01100.img" "$3" "$out/plugin" "$5"
echo "Offline OCRAM plugin candidate: $out/plugin/barebox-boot1-plugin-candidate.img" >&2
