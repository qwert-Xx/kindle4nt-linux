<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Debug source overlay

Apply the exported debug series after the production series, before building the debug profile. 02-k4-trace-hooks.patch restores the exact pre-cleanup trace source, including its original line numbers. Production does not contain marker stubs or boot hooks.
