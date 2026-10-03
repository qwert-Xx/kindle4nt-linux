// SPDX-License-Identifier: GPL-2.0-only
/* ROM-loaded Kindle 4 NT diagnostic; never writes persistent storage. */
#include <common.h>
#include <command.h>
#include <getopt.h>
#include <malloc.h>
#include <mmu.h>
#include <of.h>
#include <watchdog.h>
#include <linux/ioport.h>
#include <asm/cache.h>
#include <asm/io.h>

#define DB ((void __iomem *)0x14000000)
#define SRAM ((void *)0xf8004000)
#define SRAM_SIZE 0x4000
#define RESULT ((u32 *)(SRAM + 0x1000))
#define LOG ((volatile u32 *)(SRAM + 0x2000))
#define USB_CMD ((void __iomem *)0x53f80140)
#define MAX_RUNS 128
#define TEST_WORDS (64 * 1024)
#define APPLY_WORDS (4 * 1024 * 1024)
extern char k4_zq_sram_start[], k4_zq_sram_end[];

#include "zqcal-config.h"
#include "zqcal-trace.h"

static int do_zqcal(int argc, char *argv[])
{
	struct resource *res;
	unsigned int counts[32][16] = { }, best = 0, bp = 0, bd = 0;
	unsigned int n = 16, i, j, k, pu, pd;
	u32 saved[5], usb, *test;
	size_t size = k4_zq_sram_end - k4_zq_sram_start;
	void (*measure)(u32 *, void *) = SRAM;
	int opt, ret = 0;
	bool read_log = false, read_boot = false, apply = false;
	unsigned int target_pu = 0, target_pd = 0, words = TEST_WORDS;
	struct watchdog *wd = watchdog_get_default();

	while ((opt = getopt(argc, argv, "n:rab")) > 0) {
		if (opt == 'r') { read_log = true; continue; }
		if (opt == 'b') { read_boot = true; continue; }
		if (opt == 'a') { apply = true; continue; }
		if (opt != 'n' || kstrtouint(optarg, 0, &n))
			return COMMAND_ERROR_USAGE;
	}
	if (apply) {
		if (read_log || read_boot || optind + 2 != argc ||
		    kstrtouint(argv[optind], 0, &target_pu) ||
		    kstrtouint(argv[optind + 1], 0, &target_pd) ||
		    target_pu > 30 || target_pd > 14)
			return COMMAND_ERROR_USAGE;
		optind += 2; n = 1; words = APPLY_WORDS;
	}
	if (optind != argc || !n || n > MAX_RUNS)
		return COMMAND_ERROR_USAGE;
	if (!of_machine_is_compatible("amazon,kindle-d01100"))
		return -ENODEV;
	if (read_boot) {
		volatile u32 *trace = (void *)0xf8007b00;
		printf("boot OCRAM magic=%08x stage=%u inverse=%08x SRSR=%08x CTL73/74/75=%08x/%08x/%08x tag=%08x expected=%08x\n",
			trace[0], trace[1], trace[2], trace[3], trace[4], trace[5], trace[6], trace[7], K4_ZQ_TRACE_ID);
		return trace[0] == 0x4b345a54 && trace[2] == ~trace[1] &&
			trace[7] == K4_ZQ_TRACE_ID ? 0 : -EIO;
	}
	if (read_log) {
		/* Configuration readback is also available before any measurement. */
		u32 active73 = readl(DB + 0x124), active74 = readl(DB + 0x128);
		u32 active75 = readl(DB + 0x12c);
		printf("active CTL73=%08x CTL74=%08x CTL75=%08x PU=%u PD=%u\n",
			active73, active74, active75, active75 & 31, (active75 >> 8) & 15);
		if (LOG[0] == 0x5a514132) {
			printf("apply diagnostic: status=%d done=%08x target=%u/%u rollback_stage=%u memory_errors=%u checks=%08x bytes=%u\n",
				(int)LOG[3], LOG[7], LOG[4], LOG[5], LOG[8], LOG[9], LOG[10], LOG[11]);
			printf("candidate readback CTL73=%08x CTL74=%08x CTL75=%08x; rolled back, no persistent apply\n",
				LOG[12], LOG[13], LOG[14]);
			return LOG[7] == 0x444f4e45 ? (int)LOG[3] : -EINPROGRESS;
		}
		if (!k4_zq_log_valid(LOG[0], LOG[1], LOG[2])) {
			printf("no measurement record; configuration readback only\n");
			return 0;
		}
		printf("record requested=%u completed=%u status=%d done=%08x mode=%u/%u count=%u\n",
			LOG[1], LOG[2], (int)LOG[3], LOG[7], LOG[4], LOG[5], LOG[6]);
		for (i = 0; i < LOG[2]; i++)
			printf("record run %u: PU=%u PD=%u status=%d checks=%08x\n",
				LOG[16 + i * 4], LOG[17 + i * 4], LOG[18 + i * 4],
				(int)LOG[19 + i * 4], LOG[528 + i]);
		if (LOG[7] == 0x444f4e45 && !(int)LOG[3]) {
			printf("recommended PU=%u PD=%u; not applied\n", LOG[4], LOG[5]);
			printf("wm 32 0x1400012c 0x%08x\n", (LOG[5] << 8) | LOG[4]);
			printf("wm 32 0x14000128 0x%08x\n", k4_zq_config74(LOG[4], LOG[5]));
			printf("wm 32 0x14000124 0x00310000\nwm 32 0x14000124 0x00200000\n");
			printf("wm 32 0x14000128 0x%08x\n", k4_zq_config74(LOG[4], LOG[5]) | 16);
			printf("wm 32 0x14000124 0x00310000\nwm 32 0x14000124 0x00200000\n");
			printf("Only use these DCD lines at next cold initialization.\n");
		}
		return LOG[7] == 0x444f4e45 ? (int)LOG[3] : -EINPROGRESS;
	}
	if ((readl(DB) & 0xf01) != 0x101 || (readl(DB + 0x4c) & 1))
		return -EBUSY;
	/* No load pulse, automatic load or running comparator may be inherited. */
	if (readl(DB + 0x124) & ~(u32)BIT(21))
		return -EBUSY;
	/* Unsafe DDR exit parks in OCRAM, so a hardware fallback is mandatory. */
	if (!(readw((void *)0x53f98000) & 4) ||
		(readw((void *)0x53f98000) >> 8) < 59) {
		printf("zqcal: first arm a watchdog with wd 120\n");
		return -EBUSY;
	}
	if (size > 0x1000)
		return -E2BIG;
	if ((readl((void *)0x53f801a8) & 3) != 2)
		return -EBUSY; /* This diagnostic uses the ROM RAM USB-device session. */
	/* No in-flight MMC transaction may access DDR during SRAM code. */
	if (readl((void *)0x50020024) & 3 ||
		readl((void *)0x50008024) & 3 ||
		readl((void *)0x50004024) & 3) {
		printf("zqcal: DMA/MMC busy; use a fresh ROM RAM session\n");
		return -EBUSY;
	}
	res = request_iomem_region("k4-zqcal", (ulong)SRAM,
		(ulong)SRAM + SRAM_SIZE - 1);
	if (IS_ERR(res))
		return PTR_ERR(res);
	/* Rollback is only valid for a known software-loaded baseline, whose
	 * DAC fields encode the raw saved trims. Reject unknown pad state. */
	if (apply && !k4_zq_baseline_valid(readl(DB + 0x124),
		readl(DB + 0x128), readl(DB + 0x12c))) {
		ret = -EINVAL; goto release;
	}
	test = malloc(words * sizeof(*test));
	if (!test) { ret = -ENOMEM; goto release; }
	if ((ulong)test < 0x70000000 ||
	    (ulong)test + words * sizeof(*test) > 0x80000000) {
		ret = -EINVAL; goto free_test;
	}
	for (j = 0; j < words; j++)
		test[j] = (j * 0x9e3779b9U) ^ 0xa51c37e9U;
	saved[0] = readl(DB + 0x4c);
	saved[1] = readl(DB + 0x50);
	saved[2] = readl(DB + 0x124);
	saved[3] = readl(DB + 0x128);
	saved[4] = readl(DB + 0x12c);
	memcpy(SRAM, k4_zq_sram_start, size);
	ret = remap_range(SRAM, SRAM_SIZE, MAP_CACHED_RWX);
	if (ret) goto free_test;
	memset((void *)LOG, 0, 0x1000);
	LOG[0] = apply ? 0x5a514132 : 0x5a514331; LOG[1] = n; LOG[3] = -EINPROGRESS;
	sync_caches_for_execution();
	printf("zqcal: %s, stock LPDDR1, %u runs; active %08x/%08x/%08x\n",
		apply ? "explicit load/test/rollback diagnostic" : "measure only", n, saved[2], saved[3], saved[4]);
	usb = readl(USB_CMD);
	writel(usb & ~1U, USB_CMD);
	if (readl(USB_CMD) & 1) {
		writel(usb, USB_CMD); ret = -EBUSY; goto finish_log;
	}
	udelay(1000);
	for (i = 0; i < n; i++) {
		ret = watchdog_ping(wd);
		if (ret) break;
		memset(RESULT, 0, 128);
		if (apply) {
			RESULT[14] = 1; RESULT[15] = target_pu; RESULT[16] = target_pd;
			RESULT[18] = (u32)(ulong)test; RESULT[19] = words;
		}
		measure(RESULT, SRAM + SRAM_SIZE - 16);
		watchdog_ping(wd);
		bool memory_ok = true;
		for (j = 0; j < words; j++)
			if (test[j] != ((j * 0x9e3779b9U) ^ 0xa51c37e9U)) memory_ok = false;
		bool registers_ok = saved[0] == readl(DB + 0x4c) && saved[1] == readl(DB + 0x50) &&
			saved[2] == readl(DB + 0x124) && saved[3] == readl(DB + 0x128) &&
			saved[4] == readl(DB + 0x12c);
		LOG[528 + i] = k4_zq_checks(RESULT[10], (int)RESULT[13], memory_ok, registers_ok);
		ret = k4_zq_checked_status((int)RESULT[13], LOG[528 + i]);
		pu = RESULT[11]; pd = RESULT[12];
		if (pu >= 31 || pd > 14) ret = -ERANGE;
		if (apply) {
			LOG[4] = target_pu; LOG[5] = target_pd;
			LOG[8] = RESULT[21]; LOG[9] = RESULT[20];
			LOG[10] = LOG[528 + i]; LOG[11] = words * sizeof(*test);
			LOG[12] = RESULT[22]; LOG[13] = RESULT[23]; LOG[14] = RESULT[24];
			ret = k4_zq_apply_status(ret, RESULT[21], RESULT[20], LOG[10],
				target_pu, target_pd, RESULT[22], RESULT[23], RESULT[24]);
		}
		LOG[16 + i * 4] = i + 1;
		LOG[17 + i * 4] = pu;
		LOG[18 + i * 4] = pd;
		LOG[19 + i * 4] = ret;
		LOG[2] = i + 1;
		if (ret) break;
		counts[pu][pd]++;
	}
	if (!ret && !apply) {
		for (j = 0; j < 32; j++) for (k = 0; k < 16; k++)
			if (counts[j][k] > best) { best = counts[j][k]; bp = j; bd = k; }
		k = 0;
		for (j = 0; j < 32 * 16; j++)
			if (((unsigned int *)counts)[j] == best) k++;
		if (k != 1) ret = -EAGAIN;
	}
finish_log:
	LOG[3] = ret;
	if (!apply) { LOG[4] = bp; LOG[5] = bd; LOG[6] = best; }
	LOG[7] = 0x444f4e45;
	sync_caches_for_execution();
	writel(usb, USB_CMD);
	watchdog_ping(wd);
	printf("zqcal: complete, status=%d; read durable RAM result with zqcal -r\n", ret);
	remap_range(SRAM, SRAM_SIZE, MAP_UNCACHED);
free_test:
	free(test);
release:
	release_region(res);
	return ret;
}
BAREBOX_CMD_START(zqcal)
	.cmd = do_zqcal,
	BAREBOX_CMD_DESC("measure K4 NT ZQ; explicit RAM-only load/test/rollback")
	BAREBOX_CMD_OPTS("[-n COUNT] | -r | -b | -a PU PD (explicit 16MiB test with rollback)")
	BAREBOX_CMD_GROUP(CMD_GRP_HWMANIP)
BAREBOX_CMD_END
