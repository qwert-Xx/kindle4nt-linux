// SPDX-License-Identifier: GPL-2.0-or-later
/* Two independent RTC counters; PMIC wake with an SRTC fallback for STOP. */
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <linux/rtc.h>
#include <poll.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <time.h>
#include <unistd.h>

static volatile sig_atomic_t interrupted;
static void stop(int sig) { interrupted = sig; }

static int text_read(const char *path, char *text, size_t size)
{
	int fd = open(path, O_RDONLY | O_CLOEXEC);
	ssize_t n;
	if (fd < 0) return -1;
	n = read(fd, text, size - 1);
	close(fd);
	if (n <= 0) return -1;
	text[n] = 0;
	return 0;
}

static int text_write(const char *path, const char *text)
{
	int fd = open(path, O_WRONLY | O_CLOEXEC);
	ssize_t n;
	if (fd < 0) return -1;
	n = write(fd, text, strlen(text));
	close(fd);
	return n == (ssize_t)strlen(text) ? 0 : -1;
}

static int rtc_seconds(int fd, long long *seconds)
{
	struct rtc_time r;
	struct tm t = {0};
	if (ioctl(fd, RTC_RD_TIME, &r)) return -1;
	t.tm_year = r.tm_year; t.tm_mon = r.tm_mon; t.tm_mday = r.tm_mday;
	t.tm_hour = r.tm_hour; t.tm_min = r.tm_min; t.tm_sec = r.tm_sec;
	*seconds = timegm(&t);
	return 0;
}

static int sample(const int *fd, long long *seconds, const char *label)
{
	struct timespec now;
	/* Read SRTC on both sides of the SPI read to bound sequencing skew. */
	long long last;
	if (rtc_seconds(fd[0], &seconds[0]) || rtc_seconds(fd[1], &seconds[1]) ||
	    rtc_seconds(fd[0], &last) || clock_gettime(CLOCK_BOOTTIME, &now))
		return -1;
	printf("%s srtc=%lld..%lld pmic=%lld delta=%lld..%lld boottime=%lld.%09ld\n",
	       label, seconds[0], last, seconds[1], seconds[1]-last,
	       seconds[1]-seconds[0], (long long)now.tv_sec, now.tv_nsec);
	return last - seconds[0] <= 1 ? 0 : -1;
}

static int arm(int fd, int delay)
{
	struct rtc_wkalrm alarm = {.enabled = 1};
	long long seconds;
	struct tm t;
	time_t target;
	if (rtc_seconds(fd, &seconds)) return -1;
	target = seconds + delay;
	if (!gmtime_r(&target, &t)) return -1;
	alarm.time.tm_year=t.tm_year; alarm.time.tm_mon=t.tm_mon;
	alarm.time.tm_mday=t.tm_mday; alarm.time.tm_hour=t.tm_hour;
	alarm.time.tm_min=t.tm_min; alarm.time.tm_sec=t.tm_sec;
	printf("arm fd=%d delay=%d target=%lld\n", fd, delay, (long long)target);
	return ioctl(fd, RTC_WKALM_SET, &alarm);
}

int main(int argc, char **argv)
{
	int fd[2] = {-1, -1}, mode, result=1, touched[2]={0};
	long long before[2], after[2];
	char text[256], count[32], path[128];
	struct sigaction action={.sa_handler=stop};
	struct pollfd polls[2];
	unsigned long events;
	setvbuf(stdout, NULL, _IONBF, 0);
	if (argc != 2) return 1;
	mode = !strcmp(argv[1], "--awake") ? 0 :
	       !strcmp(argv[1], "--s2idle") ? 1 :
	       !strcmp(argv[1], "--mem") ? 2 : -1;
	if (mode < 0) return 1;
	sigemptyset(&action.sa_mask);
	if (sigaction(SIGINT, &action, NULL) || sigaction(SIGTERM, &action, NULL))
		return 1;
	for (int i=0; i<2; i++) {
		struct rtc_wkalrm previous={0};
		snprintf(path,sizeof(path),"/sys/class/rtc/rtc%d/name",i);
		if (text_read(path,text,sizeof(text)) || !strstr(text,i ? "mc13" : "mxc_rtc")) goto out;
		snprintf(path,sizeof(path),"/dev/rtc%d",i);
		fd[i]=open(path,O_RDONLY|O_NONBLOCK|O_CLOEXEC);
		if (fd[i]<0 || ioctl(fd[i],RTC_WKALM_RD,&previous) || previous.enabled) {
			fprintf(stderr,"RTC%d unreadable or already armed\n",i); goto out;
		}
		if (mode) {
			snprintf(path,sizeof(path),"/sys/class/rtc/rtc%d/device/power/wakeup",i);
			if (text_read(path,text,sizeof(text)) || strcmp(text,"enabled\n")) goto out;
		}
	}
	if (sample(fd,before,"BEFORE")) goto out;
	if (mode) {
		if (text_read("/sys/power/pm_test",text,sizeof(text)) || !strstr(text,"[none]")) goto out;
		if (mode==2 && (text_read("/sys/power/mem_sleep",text,sizeof(text)) || !strstr(text,"[deep]"))) goto out;
		if (text_read("/sys/power/wakeup_count",count,sizeof(count))) goto out;
		/* Independent 45-second fallback for a lost PMIC wake event. */
		touched[0]=1;
		if (arm(fd[0],45)) goto out;
	}
	touched[1]=1;
	if (arm(fd[1],mode ? 15 : 5)) goto out;
	if (mode) {
		if (interrupted || text_write("/sys/power/wakeup_count",count) ||
		    text_write("/sys/power/state",mode==2 ? "mem\n" : "freeze\n")) {
			perror("suspend"); goto out;
		}
		if (text_read("/sys/power/pm_wakeup_irq",text,sizeof(text))) goto out;
		printf("wake parent IRQ=%s",text);
		/* Observed parent on this frozen image; not a driver constant. */
		if (atoi(text)!=312) goto out;
	}
	polls[0]=(struct pollfd){.fd=fd[0],.events=POLLIN};
	polls[1]=(struct pollfd){.fd=fd[1],.events=POLLIN};
	if (interrupted || poll(&polls[1],1,mode ? 500 : 15000)<=0 ||
	    !(polls[1].revents&POLLIN) || poll(&polls[0],1,0)!=0 ||
	    read(fd[1],&events,sizeof(events))!=sizeof(events) ||
	    (events&(RTC_AF|RTC_IRQF))!=(RTC_AF|RTC_IRQF)) goto out;
	printf("PMIC_EVENT raw=%lx SRTC_FALLBACK_NOT_FIRED\n",events);
	if (sample(fd,after,"AFTER")) goto out;
	printf("COUNTER_ADVANCE srtc=%lld pmic=%lld offset_change=%lld\n",
	       after[0]-before[0],after[1]-before[1],
	       (after[1]-after[0])-(before[1]-before[0]));
	if (llabs((after[1]-after[0])-(before[1]-before[0]))>1) {
		fprintf(stderr,"RTC counter divergence\n"); goto out;
	}
	result=0;
out:
	for (int i=0; i<2; i++) if (fd[i]>=0) {
		if (touched[i]) {
			struct rtc_wkalrm after_alarm={0};
			if (ioctl(fd[i],RTC_AIE_OFF,0) || ioctl(fd[i],RTC_WKALM_RD,&after_alarm) || after_alarm.enabled) result=1;
			printf("RTC%d cleanup enabled=%u pending=%u\n",i,after_alarm.enabled,after_alarm.pending);
		}
		close(fd[i]);
	}
	printf("DUAL_RTC %s %s\n",argv[1],result ? "FAIL" : "PASS");
	return result;
}
