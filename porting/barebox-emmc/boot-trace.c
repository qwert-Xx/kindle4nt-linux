// SPDX-License-Identifier: GPL-2.0-only
#include <common.h>
#include <init.h>
#include <io.h>
#include <watchdog.h>
#include <driver.h>
#include <of.h>
/* One volatile record at f8008000, outside ROM buffers and plugin code. */
static int k4_host_loader_init(void)
{
 u32 record[12] = { 0x4b344231, 2 };
 struct watchdog *wd;
 int i, ret;
 if (!of_machine_is_compatible("amazon,kindle-d01100")) return 0;
 record[2] = readl(IOMEM(0x53fd0000));
 record[3] = readl(IOMEM(0x53fd0004));
 record[4] = readl(IOMEM(0x53fd0008));
 record[5] = readw(IOMEM(0x53f98000));
 record[6] = readw(IOMEM(0x53f98002));
 record[7] = readw(IOMEM(0x53f98004));
 record[8] = readl(IOMEM(0x14000050));
 record[9] = readl(IOMEM(0x14000054));
 record[10] = readl(IOMEM(0x14000058));
 record[11] = readl(IOMEM(0x1400012c));
 for (i = 0; i < 12; i++) {
  writel(record[i], IOMEM(0xf8008000 + i * 4));
 }
 wd = watchdog_get_default();
 if (!wd) return -ENODEV;
 ret = watchdog_set_timeout(wd, 120);
 if (ret) return ret;
 ret = dev_set_param(&wd->dev, "autoping", "1");
 if (ret) return ret;
 puts("K4 boot1 host loader: OCRAM phase 2; watchdog 120s/autoping; storage unprobed\n");
 return 0;
}
late_initcall(k4_host_loader_init);
