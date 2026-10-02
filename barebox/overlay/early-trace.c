// SPDX-License-Identifier: GPL-2.0-or-later
/* ROM RAM diagnostic only: breadcrumbs in the zqcal-reserved OCRAM gap. */
#include <common.h>
#include "zqcal-trace.h"
#include <init.h>
#include <asm/io.h>

static void trace_stage(u32 phase)
{
 void __iomem *p = (void *)0xf8007b00;
 writel(K4_ZQ_TRACE_ID, p + 28);
 writel(0x4b345a54, p);
 writel(phase, p + 4);
 writel(~phase, p + 8);
 writel(readl((void *)0x53fd0008), p + 12);
 writel(readl((void *)0x14000124), p + 16);
 writel(readl((void *)0x14000128), p + 20);
 writel(readl((void *)0x1400012c), p + 24);
 barrier();
}
static int trace_core(void) { trace_stage(3); return 0; }
core_initcall(trace_core);
static int trace_device(void) { trace_stage(4); return 0; }
device_initcall(trace_device);
static int trace_late(void) { trace_stage(5); return 0; }
late_initcall(trace_late);
