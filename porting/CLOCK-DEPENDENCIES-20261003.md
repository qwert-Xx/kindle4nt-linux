<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# i.MX50 APBH and analog dependencies, 2026-10-03

Host-only work based on `4621fbb46`, branch `drivers/clock-deps`.
No device access or persistent deployment. The effective production DT is
`nxp/imx/imx50-kindle-k4.dtb`.

## APBH source evidence

The local Amazon K4 4.1.1 source is
`reference/stock-audit-2.6.31-20261001` extracted from
`Kindle_src_4.1.1_1813030025.tar.gz` (the reference inputs are outside Git).
Use **clock_mx50_yoshi.c**, not the generic clock_mx50.c: the latter even
has a different APBH parent. Yoshi `apbh_dma_clk` uses AHB and CCGR7 CG10;
`display_axi_clk`, `epdc_axi_clk` and `epdc_pix_clk` use APBH secondary
references. `pfd_recalc`, `pfd_set_rate`, `pfd_enable` and `pfd_disable`
temporarily enable the bridge for ANADIG accesses.

The NXP i.MX50 RM Rev.2, Table 2-3, lists APBH-DMA, OCOTP, DIGCTL,
GPMI, BCH, eLCDIF, ePXP, DCP, EPDC, QoSC, PERFMON and CCM ANALOG in
0x41000000..0x41019fff. Chapter 11 describes the bridge PIO/DMA sharing;
Table 11-1 assigns GPMI0..7 to DMA channels 0..7. EPDC and PxP have
independent bus-master DMA; they are bridge-register users, not APBH-DMA
channel clients. SDMA at 0x63fb0000 and eSDHC eMMC are different devices.

| 6.6 consumer | Dependency and lifetime |
| --- | --- |
| ANATOP clocks, APLL/PFD5 | DT `apbh`; CCF provider runtime PM holds the access clock around register callbacks and while prepared. Probe and registers sysfs also acquire/release runtime PM. |
| EPDC display | DT `apbh`, `epdc_axi`, `epdc_pix`; existing bulk clock enable and cleanup, including system suspend, cover register access and display DMA. |
| PxP | DT `apbh`, `pxp_axi`; existing bulk clocks cover setup, active job/IRQ and cleanup. |
| APBH-DMA | New disabled SoC node: DT `clocks` supplies APBH to mxs-dma. `mxs_dma_init` holds it for reset/probe, alloc/free channel resources hold it for the channel lifetime. |
| GPMI/BCH, other APBH blocks | No enabled nodes/drivers in the K4 DT. No synthetic always-on reference is required. NAND enablement needs its own GPMI/BCH clocks and DMA references and is outside this change. |

The APBH-DMA node uses the existing i.MX28 register-layout fallback.
Yoshi `regs-apbh.h` agrees on CTRL0/1/2, CHANNEL_CTRL and the channel
register offsets. Yoshi `devices.c` provides the 0x2000 register size;
`arch/arm/plat-mxc/include/mach/mx5x.h` provides IRQs 110..125. The node
remains disabled because K4 boots from eSDHC eMMC.

The bridge gate now uses normal CCF reference counting, without critical.
The ANATOP runtime-PM dependency is enabled **before** clock registration;
otherwise 6.6 CCF would not record `rpm_enabled`. The probe reference also
covers register reads made during registration. CCF takes runtime PM
before prepare, rate callbacks and unused-clock walks, retains it through
unprepare, and skips atomic is_enabled MMIO when the provider is suspended.
APBH remains an access clock, not a fabricated frequency parent of APLL.
APBH is prepared once with `devm_clk_get_prepared`; runtime callbacks
only call `clk_enable`/`clk_disable`. This is the same split used by PM
clocks: preparing a gate does not enable it. It avoids taking CCF's
prepare mutex from a runtime-PM transition while another CCF caller holds
that mutex and waits for the transition. An inactive provider can thus
have APBH prepare_count=1 but enable_count=0; the gate is closed.

## Bandgap source evidence and ownership

RM 5.5.3 (`CCM_ANALOG_MISC`, pp.394-395) specifies REF_PWD bit18,
REF_SELFBIAS_OFF bit20 and the minimum 10 us after bandgap powerup before
setting bit20. Clear bit20 before powering the reference down. APLL startup
keeps its existing two 15..30 us waits around HOLD_RING_OFF and its LOCK
poll; output remains 480 MHz. The original Yoshi `apll_enable` powers APLL
and polls LOCK; it relies on firmware's powered reference, rather than
implementing the bandgap-off startup. Yoshi disables the analog charger
detector using MISC bit16 and uses the external detector/PMIC instead.
Reference manual source: <https://www.nxp.com/docs/en/reference-manual/IMX50RM.pdf>.
The locally cached Rev.2 manual was used for the register details.

The new CCF tree is `imx50_bandgap -> imx50_apll -> imx50_pfd5`.
Provider indices 0 (APLL) and 1 (PFD5) are unchanged; index 2 exports the
shared bandgap for other analog consumers. It is a power dependency with
no frequency output. APLL and direct bandgap users share CCF prepare
counts: the first vote powers/settles it, and only the last vote restores
its entry state. An enabled analog charger detector also holds an explicit
vote; K4's stock detector-disable policy means no such permanent vote on
K4. No charger, PFD sibling, PLL rate or CPU clock bit is changed by
bandgap callbacks. APBH runtime PM covers the parent as well as its child.

The reference callback preserves an already powered firmware reference,
including its original bias selection, matching the existing APLL policy
that retains an inherited running PLL. It restores a reference that was
originally off to off after the last software user leaves. This is not a
new policy for shutting down inherited APLL or other PFDs; those existing
ownership semantics are retained. There is one startup implementation for
both entry states and no EOPNOTSUPP branch. Lock/power-write failures are
reported as hardware errors and unwind the parent/PM votes. `CLK_IGNORE_UNUSED`
on the analog clocks remains the existing ownership policy; it does not
hold APBH awake. Runtime PM is required in Kconfig so registration cannot
silently lose the access dependency when CONFIG_PM stubs are selected.

## Host validation and reproduction

All outputs and logs are in this worktree's ignored `.k4-build/`.
No existing output directory or frozen package was reused. Validation uses
function/consumer behavior, not artifact hash equality; download/input
SHA256 checks are unchanged.

```sh
OUT="$PWD/.k4-build/clock-deps"
make O="$OUT" ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- k4_defconfig
make O="$OUT" ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- olddefconfig
make O="$OUT" ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- \
  KERNELRELEASE=6.6.157-k4-clock-deps -j8 zImage modules \
  nxp/imx/imx50-kindle-k4.dtb
python3 -m unittest discover -s project -p 'test_*.py'
python3 project/userspace/test_compare.py
for suite in imx50-anatop imx50-pixel epdc-axi-clock epdc-owner epdc-hw \
             imx50-standby pxp-service epdc-fb epdc-buffer imx50-idle; do
    python3 "porting/test-$suite.py" || exit
done
```

The final full build includes code commit `8eaf8711a` and passed:
`zImage`, production DTB and all **23 modules**, including **modpost**.
No compiler/modpost warnings or errors occurred in the final-build log.
Every module's vermagic starts with `6.6.157-k4-clock-deps`.
Compiler: ARM GCC 13.3.0; linker: binutils 2.42. Artifacts are owned by
`kindle:kindle`. Relevant code diff passes checkpatch with 0 errors/warnings
(commit signoff checks excluded) and `git diff --check` passes.

Logs: `.k4-build/final-build.log`, `project-tests.log`, `userspace-test.log`,
`clock-regressions.log`, `access-regressions.log`, `dt-bindings.log`,
`dtbs-check-consumers.log` and `code-style.log`. The final ANATOP callback
harness was rerun after the runtime lock-order refinement and passed.
The shared-vote/runtime model is simulated; no real-device acceptance is
implied by these results.

The two changed binding schemas and their examples pass `dt_binding_check`.
The production DTB passes targeted `dtbs_check` (`CHECK_DTBS=y`) for six
schemas: ANATOP, imx5 clocks, MXS DMA, imx50 PxP, EPDC owner and framebuffer.
The environment uses `$TOOLS/dtschema-venv/bin` on PATH.
Optional yamllint is absent; a full-tree schema preprocessing warning for
pre-existing duplicate `maxim,max6625` compatible is unrelated to this
change. No changed-schema validation diagnostics occurred. A complete
all-SoC/all-binding clean bill is not claimed.

```sh
SCHEMAS='clock/fsl,imx50-anatop-clocks.yaml:dma/fsl,mxs-dma.yaml'
make O="$PWD/.k4-build/dt-schema" ARCH=arm \
  CROSS_COMPILE=arm-linux-gnueabihf- DT_SCHEMA_FILES="$SCHEMAS" dt_binding_check
SCHEMAS="$SCHEMAS:clock/imx5-clock.yaml:soc/imx/fsl,imx50-pxp.yaml"
SCHEMAS="$SCHEMAS:display/amazon,k4-imx50-epdc.yaml:display/amazon,k4-epdc-fb.yaml"
make O="$PWD/.k4-build/dt-schema" ARCH=arm \
  CROSS_COMPILE=arm-linux-gnueabihf- k4_defconfig
make O="$PWD/.k4-build/dt-schema" ARCH=arm \
  CROSS_COMPILE=arm-linux-gnueabihf- CHECK_DTBS=y DT_SCHEMA_FILES="$SCHEMAS" \
  nxp/imx/imx50-kindle-k4.dtb
```

Host results: project unittest **32/32**, userspace comparison **5/5**,
and all ten callback/consumer regression suites pass. The new test compiles
actual production C callbacks with a simulated MMIO/time/CCF reference
counter/runtime-PM harness and UBSan. It covers originally off bandgap/APLL,
minimum wait ordering, two simultaneous analog votes, inherited reference
and PLL states, LOCK timeout, failed reference power-write and 100 cycles.
It checks isolation of unrelated bits and absence of leaked APBH enables.
It does not execute the Linux runtime-PM scheduler or prove analog lock
and physical power behavior. Existing suites cover pixel/AXI dividers and
live-rate rejection, EPDC owner/IRQ/DMA/blank/PM unwind, PxP DMA in both
DMA_DEBUG modes, framebuffer and WAIT/STOP/SRPG/OSC/idle paths.

## Device acceptance checklist (for the separate device task)

These are proposed device steps; none were executed by this thread.
Record baseline and new results separately for RAM/kexec and for a direct
cold boot. kexec inherits firmware clock state and cannot establish the
bandgap-off or cold-boot cases. Use the project's RAM recovery procedure
and an explicitly scoped device task; no storage writes are needed for
these functional comparisons.

1. **Baseline and instrument behavior.** On the baseline kernel and then
   this kernel, save uname, DT identity, dmesg, `/sys/kernel/debug/clk/clk_summary`,
   ANATOP `registers`, provider `power/runtime_status`, display state and PxP
   diagnostic. Discover actual sysfs device paths rather than assuming a
   device number. A typical ANATOP path is
   `/sys/bus/platform/devices/41018000.clock-controller`; framebuffer device
   attributes are reached through `/sys/class/graphics/fb0/device`.
   Read raw CCF counts after completing summary/register reads:

   ```sh
   cat /sys/kernel/debug/clk/clk_summary > /tmp/clk-summary.txt
   APBH=$(find /sys/kernel/debug/clk -type d -name apbh_dma)
   cat "$APBH/clk_enable_count" "$APBH/clk_prepare_count"
   cat /sys/bus/platform/devices/41018000.clock-controller/power/runtime_status
   ```

   **Sampling matters:** 6.6 `clk_summary_show` first calls
   `clk_pm_runtime_get_all`, so its own read temporarily enables APBH.
   ANATOP `registers` similarly resumes the provider. A nonzero APBH enable
   count inside clk_summary alone is not evidence of an idle leak. The
   individual count files above do not resume the provider; after normal
   consumers go idle expect enable_count=0 and runtime_status=suspended.
   prepare_count can remain 1 for the provider's prepared access clock.
   Repeated summary/register reads must leave the same idle counts/status.
   No raw APBH MMIO read with a gated access clock is required.

2. **Display and bridge DMA use.** Submit known full-screen and partial
   grayscale images through the normal fb0/refresh/flush interfaces. Compare
   visible results, completion/error counters, image dimensions and timing
   with the baseline. Each display update also exercises PxP conversion DMA;
   use the existing service consumer for rotation cases if needed. During
   activity the EPDC/PxP APBH enable references must be held, then released
   by idle/blank cleanup. Blank/unblank via the standard fb0 blank attribute,
   refresh again, and confirm the display/PxP clocks and supplier states
   recover. Repeat enough cycles to reveal leaked enable votes. The display
   parents/rates remain PLL1_SW, AXI 200 MHz and pixel 32 MHz; do not switch
   display to PFD5 as part of this comparison.

3. **Bandgap-off startup and shared users.** Production display uses PLL1,
   so successful display updates alone do not exercise APLL or bandgap
   startup. Use a temporary kernel CCF consumer of provider index 0 (APLL)
   and index 2 (bandgap), with a second independent consumer vote. Test:
   both originally off; reference already on but APLL off; both already on.
   For an off-entry trial, use an isolated RAM/loader setup with APLL/PFD
   consumers stopped and analog charger detection disabled, and the manual's
   bit20-before-bit18 shutdown sequence. Do not force reference powerdown
   under a running analog consumer. Record the entry bits before preparing;
   don't infer entry state from a warm boot.
   Acquire bandgap directly, acquire APLL, release APLL: bandgap must remain
   ready and the second vote intact. Release the last vote: an originally
   off reference returns off; an inherited on reference stays on. Reverse
   acquisition/release order as well. For PFD5 gate/rate testing use an
   isolated CCF consumer of index 1 with a legal fractional rate; this is
   separate from the production display path. Verify LOCK, 480 MHz parent,
   correct PFD rate, repeated prepare/unprepare and EBUSY on live PFD retiming.
   There must be no EOPNOTSUPP. A real failure to power up/lock remains an
   error; host fault injection already verifies its unwind. No changes to
   CPU clocks, shared PLL rates or permanent root/boot configuration are
   needed to construct this temporary test.

4. **Concurrency and suspend/resume.** Read clk_summary and ANATOP registers
   concurrently with CCF acquire/release and display/blank cycles; verify
   no hung tasks, clock/PM warnings or extra idle enable votes. After
   successful display/DMA work, suspend through the existing system power
   interface, wake through the normal supported source, and repeat display
   updates. Compare WAIT/STOP behavior, wake success, clock counts and
   visible output with baseline. Probe/register reads must resume APBH and
   release it afterward; atomic PFD gates run only while their provider is
   prepared. A system suspend cycle is not automatically proof of every
   deep-sleep/wake combination.

5. **Actual APBH-DMA/GPMI scope.** K4's eMMC and SDMA are not APBH-DMA
   consumers; eMMC I/O is useful regression coverage but does not validate
   GPMI/APBH channel transfers. The APBH-DMA node is disabled in production.
   Optional controller-only tests can enable that node in a separate RAM DT
   and exercise probe and channel alloc/free (without NAND writes), checking
   APBH votes. Real GPMI/BCH NAND transfers require a separate supported NAND
   DT/clock implementation and suitable hardware. Do not report them as
   validated by this K4 display test. K4 bridge/DMA acceptance here is EPDC
   and PxP, including release and re-acquire of APBH.

6. **Power comparison.** Measure baseline/new device input current with the
   same voltage, battery charge, charging-source state, temperature, network
   association/traffic, USB configuration, display image and idle interval.
   Compare active refresh, stable blank/idle and supported suspend, with
   repeated paired samples and measurement uncertainty. Close summary and
   register polling during idle measurements, since polling wakes APBH.
   State the measured delta; don't assume a saving from the source change.
   Preserve the same unrelated CPU/display PLL settings. Functionality and
   low-power state consistency are the acceptance criteria, not byte/hash
   equality of generated kernels or modules.

Hardware evidence still required: bridge gating/recovery, analog off-entry
startup/LOCK, concurrent sysfs/CCF operation, display/PxP completion,
suspend/wake, paired power measurements and independent cold boot.
