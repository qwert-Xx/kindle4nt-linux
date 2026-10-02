#!/bin/sh
# SPDX-License-Identifier: GPL-2.0-only
# DRAFT: after Down/ROM -> ordinary USB barebox -> Linux RAM recovery.
set -eu
exec "$(dirname "$0")/set-partition-config-draft.sh" 0x48
