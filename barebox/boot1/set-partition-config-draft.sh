#!/bin/sh
# SPDX-License-Identifier: GPL-2.0-only
# DRAFT: standard mmc-utils on the temporarily writable main device; no sector writes.
set -eu
case "${1:-}" in 0x48|0x50) ;; *) echo 'usage: set-partition-config-draft.sh 0x48|0x50' >&2; exit 2;; esac
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
bb=/bin/busybox
trap '"$bb" blockdev --setro /dev/mmcblk2' EXIT
trap 'exit 1' HUP INT TERM
"$bb" blockdev --setrw /dev/mmcblk2
"$here/mmc" extcsd write 179 "$1" /dev/mmcblk2
"$here/mmc" extcsd read /dev/mmcblk2 > "$here/ext_csd.current.txt"
"$bb" cat "$here/ext_csd.current.txt"
"$bb" grep -F "PARTITION_CONFIG: $1]" "$here/ext_csd.current.txt"
