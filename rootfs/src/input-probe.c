/* SPDX-License-Identifier: GPL-2.0-or-later */
/* evdev observation only; never grabs devices or injects input events. */
#define _GNU_SOURCE
#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <linux/input.h>
#include <poll.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <time.h>
#include <unistd.h>

#define BIT_BYTES ((KEY_CNT + 7) / 8)
#define DEVICES 3
struct observed_input {
	const char *name;
	unsigned short keys[8];
	unsigned int count;
	unsigned char down[KEY_CNT], paired[KEY_CNT];
};
static struct observed_input inputs[DEVICES] = {
	{ .name = "fiveway-keys", .keys = { KEY_UP, KEY_DOWN, KEY_LEFT,
		KEY_RIGHT, KEY_F24 }, .count = 5 },
	{ .name = "matrix-keypad", .keys = { KEY_LEFTCTRL, KEY_MENU, KEY_PAGEDOWN,
		KEY_F21, KEY_F23, KEY_PAGEUP, KEY_HOME, KEY_BACK }, .count = 8 },
	{ .name = "k4-power-button", .keys = { KEY_POWER }, .count = 1 },
};

static int bit(const unsigned char *bits, unsigned int code)
{
	return !!(bits[code / 8] & (1U << (code % 8)));
}

static int released(int fd)
{
	unsigned char keys[BIT_BYTES] = {0};
	unsigned int i;

	if (ioctl(fd, EVIOCGKEY(sizeof(keys)), keys) < 0)
		return -1;
	for (i = 0; i < sizeof(keys); i++)
		if (keys[i])
			return -1;
	return 0;
}

static int open_inputs(struct pollfd *fds)
{
	DIR *dir = opendir("/dev/input");
	struct dirent *entry;
	unsigned int i;
	int ret = -1;

	if (!dir)
		return -1;
	while ((entry = readdir(dir))) {
		char path[512], name[128] = {0};
		int fd;

		if (strncmp(entry->d_name, "event", 5))
			continue;
		snprintf(path, sizeof(path), "/dev/input/%s", entry->d_name);
		fd = open(path, O_RDONLY | O_NONBLOCK | O_CLOEXEC);
		if (fd < 0)
			goto out;
		if (ioctl(fd, EVIOCGNAME(sizeof(name)), name) < 0) {
			close(fd);
			goto out;
		}
		for (i = 0; i < DEVICES; i++)
			if (!strcmp(name, inputs[i].name))
				break;
		if (i == DEVICES) {
			close(fd);
			continue;
		}
		if (fds[i].fd >= 0) {
			close(fd);
			goto out;
		}
		fds[i].fd = fd;
		fds[i].events = POLLIN;
		{
			unsigned char caps[BIT_BYTES] = {0};
			unsigned int k;

			if (ioctl(fd, EVIOCGBIT(EV_KEY, sizeof(caps)), caps) < 0)
				goto out;
			for (k = 0; k < inputs[i].count; k++)
				if (!bit(caps, inputs[i].keys[k]))
					goto out;
		}
		if (released(fd))
			goto out;
		printf("INPUT_OPEN name=%s node=%s keys=%u released=1\n",
		       name, path, inputs[i].count);
	}
	for (i = 0; i < DEVICES; i++)
		if (fds[i].fd < 0)
			goto out;
	ret = 0;
out:
	closedir(dir);
	return ret;
}

static int accept_event(struct observed_input *input, const struct input_event *ev)
{
	unsigned int k;

	if (ev->type == EV_SYN && ev->code == SYN_DROPPED)
		return -1;
	if (ev->type != EV_KEY)
		return 0;
	for (k = 0; k < input->count; k++)
		if (input->keys[k] == ev->code)
			break;
	if (k == input->count || ev->value < 0 || ev->value > 2)
		return -1;
	if (ev->value == 1) {
		if (input->down[ev->code])
			return -1;
		input->down[ev->code] = 1;
	} else if (ev->value == 0) {
		if (!input->down[ev->code])
			return -1;
		input->down[ev->code] = 0;
		input->paired[ev->code] = 1;
	} else if (!input->down[ev->code]) {
		return -1;
	}
	printf("INPUT_KEY name=%s code=%u value=%d time=%lld.%06ld\n",
	       input->name, ev->code, ev->value,
	       (long long)ev->input_event_sec, (long)ev->input_event_usec);
	return 1;
}

static unsigned int pairs(void)
{
	unsigned int i, k, count = 0;

	for (i = 0; i < DEVICES; i++)
		for (k = 0; k < inputs[i].count; k++)
			count += inputs[i].paired[inputs[i].keys[k]];
	return count;
}

int main(int argc, char **argv)
{
	struct pollfd fds[DEVICES];
	struct timespec start, now;
	unsigned long seconds, key_events = 0;
	unsigned int i;
	char *end;
	int require_keys, ret = 1;

	/* Pure metadata; no evdev open or event consumption. */
	if (argc == 2 && !strcmp(argv[1], "--capabilities")) {
		puts("K4_TEST_CAPABILITIES={\"tool\":\"input\",\"version\":1,\"modes\":[\"observe\",\"keys\"]}");
		return 0;
	}
	if (argc != 3 || (strcmp(argv[1], "observe") && strcmp(argv[1], "keys")))
		goto usage;
	errno = 0;
	seconds = strtoul(argv[2], &end, 10);
	if (errno || !argv[2][0] || *end || seconds < 1 || seconds > 600)
		goto usage;
	require_keys = !strcmp(argv[1], "keys");
	setvbuf(stdout, NULL, _IOLBF, 0);
	for (i = 0; i < DEVICES; i++)
		fds[i] = (struct pollfd) { .fd = -1 };
	if (open_inputs(fds) || clock_gettime(CLOCK_BOOTTIME, &start)) {
		fprintf(stderr, "Input discovery/capability/released-state check failed\n");
		goto out;
	}
	puts("INPUT_OBSERVER_READY");
	for (;;) {
		int ready;

		if (clock_gettime(CLOCK_BOOTTIME, &now))
			goto out;
		if ((unsigned long)(now.tv_sec - start.tv_sec) >= seconds)
			break;
		ready = poll(fds, DEVICES, 500);
		if (ready < 0) {
			if (errno == EINTR)
				continue;
			goto out;
		}
		for (i = 0; i < DEVICES; i++) {
			struct input_event events[32];
			ssize_t bytes;
			unsigned int e;

			if (fds[i].revents & (POLLERR | POLLHUP | POLLNVAL))
				goto out;
			if (!(fds[i].revents & POLLIN))
				continue;
			bytes = read(fds[i].fd, events, sizeof(events));
			if (bytes < 0 && (errno == EAGAIN || errno == EINTR))
				continue;
			if (bytes <= 0 || bytes % sizeof(events[0]))
				goto out;
			for (e = 0; e < (unsigned int)bytes / sizeof(events[0]); e++) {
				int accepted = accept_event(&inputs[i], &events[e]);

				if (accepted < 0)
					goto out;
				key_events += accepted;
			}
		}
		if (require_keys && pairs() == 14)
			break;
	}
	for (i = 0; i < DEVICES; i++)
		if (released(fds[i].fd))
			goto out;
	printf("INPUT_OBSERVATION_END key_events=%lu paired_keys=%u released=1\n",
	       key_events, pairs());
	if (require_keys && pairs() != 14) {
		fprintf(stderr, "Physical key coverage incomplete\n");
		goto out;
	}
	puts(require_keys ? "INPUT_PHYSICAL_KEYS_PASS" : "INPUT_OBSERVATION_PASS");
	ret = 0;
out:
	for (i = 0; i < DEVICES; i++)
		if (fds[i].fd >= 0)
			close(fds[i].fd);
	return ret;
usage:
	fprintf(stderr, "usage: %s observe|keys SECONDS(1..600)\n", argv[0]);
	return 2;
}
