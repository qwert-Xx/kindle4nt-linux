// SPDX-License-Identifier: GPL-2.0-or-later
/* Awake alarm or explicit --s2idle/--standby/--mem. Never sets the RTC clock. */
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <linux/rtc.h>
#include <poll.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/ioctl.h>
#include <time.h>
#include <unistd.h>

#ifdef K4_PMIC_RTC
#define RTC_DEVICE "/dev/rtc1"
#define RTC_WAKEUP "/sys/class/rtc/rtc1/device/power/wakeup"
#else
#define RTC_DEVICE "/dev/rtc0"
#define RTC_WAKEUP "/sys/class/rtc/rtc0/device/power/wakeup"
#endif

static volatile sig_atomic_t interrupted;

#ifdef K4_VFP_PROBE
struct vfp_state {
	uint64_t d[32];
	uint32_t fpscr;
};
extern int k4_vfp_suspend(int fd, const struct vfp_state *expected,
			  struct vfp_state *observed);

static int write_mem_vfp(void)
{
	struct vfp_state expected = {0}, observed = {0};
	uint32_t seed = (uint32_t)getpid();
	int fd, ret, i, bad = 0;

	for (i = 0; i < 32; i++) {
		seed = seed * 1664525U + 1013904223U;
		expected.d[i] = (uint64_t)seed << 32 | (seed ^ 0xa5c31f87U);
	}
	/* Default-NaN, round +infinity, nonzero sticky flags; exceptions disabled. */
	expected.fpscr = 0x02400015;
	fd = open("/sys/power/state", O_WRONLY | O_CLOEXEC);
	if (fd < 0) {
		perror("open power/state");
		return -1;
	}
	ret = k4_vfp_suspend(fd, &expected, &observed);
	close(fd);
	if (ret != 4) {
		fprintf(stderr, "VFP suspend write returned %d\n", ret);
		return -1;
	}
	for (i = 0; i < 32; i++)
		if (expected.d[i] != observed.d[i]) {
			fprintf(stderr, "VFP d%d mismatch: %016llx != %016llx\n", i,
				(unsigned long long)expected.d[i],
				(unsigned long long)observed.d[i]);
			bad++;
		}
	if (expected.fpscr != observed.fpscr) {
		fprintf(stderr, "FPSCR mismatch: %08x != %08x\n",
			expected.fpscr, observed.fpscr);
		bad++;
	}
	printf("VFP_CONTEXT %s d0-d31=256_bytes fpscr=%08x mismatches=%d\n",
	       bad ? "FAIL" : "PASS", observed.fpscr, bad);
	return bad ? -1 : 0;
}
#endif

static void stop(int sig)
{
	interrupted = sig;
}

static int read_text(const char *path, char *buf, size_t size)
{
	int fd = open(path, O_RDONLY | O_CLOEXEC);
	ssize_t n;

	if (fd < 0) {
		perror(path);
		return -1;
	}
	n = read(fd, buf, size - 1);
	close(fd);
	if (n <= 0) {
		fprintf(stderr, "Cannot read %s\n", path);
		return -1;
	}
	buf[n] = 0;
	return 0;
}

static int write_text(const char *path, const char *buf)
{
	int fd = open(path, O_WRONLY | O_CLOEXEC);
	ssize_t n;
	size_t len = strlen(buf);

	if (fd < 0) {
		perror(path);
		return -1;
	}
	n = write(fd, buf, len);
	if (n < 0)
		perror(path);
	close(fd);
	return n == (ssize_t)len ? 0 : -1;
}

static int button_irq_count(unsigned int *count)
{
	char text[256], *field;

	if (read_text("/sys/bus/platform/devices/k4-mc13892-power-button/state",
		      text, sizeof(text)))
		return -1;
	field = strstr(text, " irqs=");
	return field && sscanf(field, " irqs=%u", count) == 1 ? 0 : -1;
}

int main(int argc, char **argv)
{
	struct rtc_wkalrm previous = {0}, alarm = {0}, after = {0};
	struct rtc_time now;
	struct tm tm = {0};
	struct sigaction sa = {.sa_handler = stop};
	unsigned long events = 0;
	struct pollfd pfd;
	time_t target;
	int fd, result = 1, s2idle = 0, delay = 5;
	int standby = 0, mem = 0;
	int vfp = 0;
	int button = 0;
	unsigned int button_before = 0, button_after = 0;
	char text[128], wakeup_count[32];
	struct timespec start, end;

	/* Pure metadata query: must return before opening RTC/sysfs. */
	if (argc == 2 && !strcmp(argv[1], "--capabilities")) {
#ifdef K4_PMIC_RTC
		puts("K4_TEST_CAPABILITIES={\"tool\":\"rtc-alarm\",\"version\":1,\"modes\":[\"awake\",\"--s2idle\"]}");
#else
		puts("K4_TEST_CAPABILITIES={\"tool\":\"rtc-alarm\",\"version\":1,\"modes\":[\"awake\",\"--s2idle\",\"--standby\",\"--mem\",\"--mem-button\"]}");
#endif
		return 0;
	}
	setvbuf(stdout, NULL, _IONBF, 0);
	if (argc == 2 && !strcmp(argv[1], "--s2idle")) {
		s2idle = 1;
		delay = 15;
	} else if (argc == 2 && !strcmp(argv[1], "--standby")) {
		standby = 1;
		delay = 15;
	} else if (argc == 2 && !strcmp(argv[1], "--mem")) {
		mem = 1;
		delay = 15;
	} else if (argc == 2 && !strcmp(argv[1], "--mem-button")) {
		mem = button = 1;
		delay = 60;
#ifdef K4_VFP_PROBE
	} else if (argc == 2 && !strcmp(argv[1], "--mem-vfp")) {
		mem = vfp = 1;
		delay = 15;
#endif
	} else if (argc != 1) {
		fprintf(stderr, "Usage: %s [--s2idle|--standby|--mem|--mem-button|--mem-vfp]\n", argv[0]);
		return 1;
	}
#ifdef K4_PMIC_RTC
	/* STOP needs a separate SRTC fallback before the first PMIC wake trial. */
	if (mem || standby ||
	    read_text("/sys/class/rtc/rtc1/name", text, sizeof(text)) ||
	    !strstr(text, "mc13")) {
		fprintf(stderr, "Require PMIC rtc1 and awake/s2idle mode\n");
		return 1;
	}
#endif
	sigemptyset(&sa.sa_mask);
	if (sigaction(SIGINT, &sa, NULL) || sigaction(SIGTERM, &sa, NULL)) {
		perror("sigaction");
		return 1;
	}
	if (s2idle || standby || mem) {
		if (button && (button_irq_count(&button_before) ||
		    read_text("/sys/bus/platform/devices/k4-mc13892-power-button/power/wakeup",
			      text, sizeof(text)) || strcmp(text, "enabled\n"))) {
			fprintf(stderr, "Require power button wake enabled and readable count\n");
			return 1;
		}
		if (read_text("/sys/power/pm_test", text, sizeof(text)) ||
		    !strstr(text, "[none]") ||
		    read_text("/sys/power/state", text, sizeof(text)) ||
		    !strstr(text, mem ? "mem" : standby ? "standby" : "freeze") ||
		    read_text(RTC_WAKEUP,
			      text, sizeof(text)) || strcmp(text, "enabled\n")) {
			fprintf(stderr, "Require PM test none, requested state and RTC wake enabled\n");
			return 1;
		}
		if (mem && (read_text("/sys/power/mem_sleep", text, sizeof(text)) ||
			    !strstr(text, "[deep]"))) {
			fprintf(stderr, "Require selected deep mem_sleep for STOP test\n");
			return 1;
		}
		if (read_text("/sys/power/wakeup_count", wakeup_count,
			      sizeof(wakeup_count)))
			return 1;
	}
	fd = open(RTC_DEVICE, O_RDONLY | O_NONBLOCK | O_CLOEXEC);
	if (fd < 0) {
		perror(RTC_DEVICE);
		return 1;
	}
	if (ioctl(fd, RTC_WKALM_RD, &previous)) {
#ifdef K4_PMIC_RTC
		/* Hardware TODA=0x1ffff cannot match; there is no valid alarm to replace. */
		if (errno != ENODATA) {
#endif
		perror("RTC_WKALM_RD");
		goto close_fd;
#ifdef K4_PMIC_RTC
		}
		printf("before: no valid PMIC alarm programmed\n");
#endif
	}
	printf("before: enabled=%u pending=%u\n", previous.enabled,
	       previous.pending);
	if (previous.enabled) {
		fprintf(stderr, "Refusing to replace an enabled alarm\n");
		goto close_fd;
	}
	if (ioctl(fd, RTC_RD_TIME, &now)) {
		perror("RTC_RD_TIME");
		goto close_fd;
	}
	tm.tm_sec = now.tm_sec;
	tm.tm_min = now.tm_min;
	tm.tm_hour = now.tm_hour;
	tm.tm_mday = now.tm_mday;
	tm.tm_mon = now.tm_mon;
	tm.tm_year = now.tm_year;
	target = timegm(&tm) + delay;
	if (!gmtime_r(&target, &tm)) {
		perror("gmtime_r");
		goto close_fd;
	}
	alarm.time.tm_sec = tm.tm_sec;
	alarm.time.tm_min = tm.tm_min;
	alarm.time.tm_hour = tm.tm_hour;
	alarm.time.tm_mday = tm.tm_mday;
	alarm.time.tm_mon = tm.tm_mon;
	alarm.time.tm_year = tm.tm_year;
	alarm.enabled = 1;
	printf("arming: %04d-%02d-%02d %02d:%02d:%02d UTC (+%d seconds)\n",
	       tm.tm_year + 1900, tm.tm_mon + 1, tm.tm_mday,
	       tm.tm_hour, tm.tm_min, tm.tm_sec, delay);
	if (interrupted)
		goto close_fd;
	if (ioctl(fd, RTC_WKALM_SET, &alarm)) {
		perror("RTC_WKALM_SET");
		goto disarm;
	}
	if (s2idle || standby || mem) {
		if (interrupted ||
		    write_text("/sys/power/wakeup_count", wakeup_count) ||
		    clock_gettime(CLOCK_BOOTTIME, &start))
			goto disarm;
		printf("entering %s; RTC alarm is the %s wake source\n",
		       mem ? "mem/deep" : standby ? "standby" : "s2idle",
		       button ? "backup; short power button press is the planned" : "planned");
		int write_result;
#ifdef K4_VFP_PROBE
		if (vfp)
			write_result = write_mem_vfp();
		else
#else
		(void)vfp;
#endif
			write_result = write_text("/sys/power/state", mem ? "mem\n" : standby ? "standby\n" : "freeze\n");
		if (write_result ||
		    clock_gettime(CLOCK_BOOTTIME, &end))
			goto disarm;
		printf("suspend syscall elapsed: %.3f seconds\n",
		       end.tv_sec - start.tv_sec +
		       (end.tv_nsec - start.tv_nsec) / 1e9);
	}
	pfd = (struct pollfd){.fd = fd, .events = POLLIN};
	if (button) {
		int wake_irq = -1, i;

		/* Nested PMIC IRQ delivery can finish just after the suspend syscall. */
		for (i = 0; i < 30; i++) {
			if (button_irq_count(&button_after))
				goto disarm;
			if (button_after != button_before)
				break;
			usleep(100000);
		}
		if (read_text("/sys/power/pm_wakeup_irq", text, sizeof(text)) ||
		    sscanf(text, "%d", &wake_irq) != 1)
			goto disarm;
		/* 312 is this test image's observed PMIC parent IRQ, not driver policy. */
		printf("BUTTON_WAKE parent_irq=%d button_irqs=%u->%u rtc_ready=%d\n",
		       wake_irq, button_before, button_after, poll(&pfd, 1, 0));
		if (!interrupted && wake_irq == 312 && button_after > button_before &&
		    poll(&pfd, 1, 0) == 0)
			result = 0;
		goto disarm;
	}
	/* Do not count an alarm arriving later after a premature wake as success. */
	if (interrupted || poll(&pfd, 1, (s2idle || standby || mem) ? 0 : 15000) <= 0 ||
	    !(pfd.revents & POLLIN)) {
		fprintf(stderr, "No alarm event %s (signal=%d)\n",
			(s2idle || standby || mem) ? "at resume" : "within 15 seconds",
			interrupted);
		goto disarm;
	}
	if (read(fd, &events, sizeof(events)) != sizeof(events)) {
		perror("read RTC event");
		goto disarm;
	}
	printf("event: raw=0x%lx count=%lu RTC_AF=%u RTC_IRQF=%u\n",
	       events, events >> 8, !!(events & RTC_AF),
	       !!(events & RTC_IRQF));
	if ((events & (RTC_AF | RTC_IRQF)) == (RTC_AF | RTC_IRQF))
		result = 0;
disarm:
	/* Keep the expired alarm date; only restore the original disabled state. */
	if (ioctl(fd, RTC_AIE_OFF, 0)) {
		perror("RTC_AIE_OFF");
		result = 1;
	}
	if (ioctl(fd, RTC_WKALM_RD, &after)) {
		perror("RTC_WKALM_RD after");
		result = 1;
	} else {
		printf("after: enabled=%u pending=%u\n", after.enabled,
		       after.pending);
		if (after.enabled)
			result = 1;
	}
	printf("result: %s\n", result ? "FAIL" : "PASS");
close_fd:
	close(fd);
	return result;
}
