<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Production and debug trace separation

Production has no K4 boot-trace macros, RAM marker calls/stubs or disabled-debug placeholder padding. Apply all production patches first. For debug, additionally apply both patches in kernel/debug-patches/series before building the unchanged debug profile. The overlay restores the original diagnostic files and trace points byte for byte.

ARM production/debug builds and host tests passed. With fixed line numbers, preprocessed tokens match after removal of pure markers; 22 of 23 affected object disassemblies match exactly. PxP has one register allocation exchange in an equal-only readback comparison (same MMIO/barrier sequence). Consequently the stronger claim that all machine-code differences are only line numbers is not made. Hardware parameters/configurations are unchanged; the combined defconfig regression and review gates remain pending. No deployment or device test was performed for this cleanup.
