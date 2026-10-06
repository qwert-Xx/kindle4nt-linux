// SPDX-License-Identifier: GPL-2.0-only
/* Submit the existing framebuffer canvas through the lf-6.6 mxcfb ABI. */
#include <errno.h>
#include <fcntl.h>
#include <getopt.h>
#include <linux/mxcfb.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <unistd.h>

#define ARRAY_SIZE(array) (sizeof(array) / sizeof((array)[0]))

static const char * const waveforms[] = {
	"du", "gc16", "gc16-fast", "a2", "gl16", "gl16-fast",
};

static int print_usage(const char *program, int status)
{
	fprintf(status ? stderr : stdout,
		"usage: %s [--device /dev/fb0] [--full|--partial]\n"
		"       [--waveform du|gc16|gc16-fast|a2|gl16|gl16-fast|auto]\n"
		"       [--region x,y,w,h] [--wait|--no-wait]\n"
		"Default: entire canvas, FULL, GC16, wait. --region implies PARTIAL.\n",
		program);
	return status;
}

static int region(const char *text, struct mxcfb_rect *r)
{
	uint32_t values[4];
	char *end;

	for (unsigned int i = 0; i < 4; i++) {
		unsigned long value;

		if (*text < '0' || *text > '9')
			return -1;
		errno = 0;
		value = strtoul(text, &end, 10);
		if (errno || value > UINT32_MAX || *end != (i == 3 ? '\0' : ','))
			return -1;
		values[i] = value;
		text = end + (i != 3);
	}
	*r = (struct mxcfb_rect){ values[1], values[0], values[2], values[3] };
	return !r->width || !r->height ? -1 : 0;
}

int main(int argc, char **argv)
{
	static const struct option options[] = {
		{ "device", required_argument, NULL, 'd' },
		{ "full", no_argument, NULL, 'f' },
		{ "partial", no_argument, NULL, 'p' },
		{ "waveform", required_argument, NULL, 'w' },
		{ "region", required_argument, NULL, 'r' },
		{ "wait", no_argument, NULL, 's' },
		{ "no-wait", no_argument, NULL, 'n' },
		{ "help", no_argument, NULL, 'h' },
		{ NULL, 0, NULL, 0 },
	};
	struct mxcfb_update_data update = {
		.waveform_mode = 2, .update_mode = UPDATE_MODE_FULL,
		.temp = TEMP_USE_AMBIENT,
	};
	struct mxcfb_update_marker_data marker = { 0 };
	struct fb_var_screeninfo v;
	const char *device = "/dev/fb0";
	bool wait = true, has_region = false, has_mode = false;
	int fd, c, status = 0;

	while ((c = getopt_long(argc, argv, "", options, NULL)) != -1) {
		switch (c) {
		case 'd':
			device = optarg;
			break;
		case 'f':
		case 'p':
			update.update_mode = c == 'f' ? UPDATE_MODE_FULL : UPDATE_MODE_PARTIAL;
			has_mode = true;
			break;
		case 'w':
			update.waveform_mode = WAVEFORM_MODE_AUTO;
			if (!strcmp(optarg, "auto"))
				break;
			for (unsigned int i = 0; i < ARRAY_SIZE(waveforms); i++)
				if (!strcmp(optarg, waveforms[i]))
					update.waveform_mode = i + 1;
			if (update.waveform_mode == WAVEFORM_MODE_AUTO)
				return print_usage(argv[0], 2);
			break;
		case 'r':
			if (region(optarg, &update.update_region))
				return print_usage(argv[0], 2);
			has_region = true;
			break;
		case 's':
		case 'n':
			wait = c == 's';
			break;
		case 'h':
			return print_usage(argv[0], 0);
		default:
			return print_usage(argv[0], 2);
		}
	}
	if (optind != argc)
		return print_usage(argv[0], 2);
	if (has_region && !has_mode)
		update.update_mode = UPDATE_MODE_PARTIAL;
	fd = open(device, O_RDWR | O_CLOEXEC);
	if (fd < 0) {
		perror(device);
		return 1;
	}
	if (ioctl(fd, FBIOGET_VSCREENINFO, &v)) {
		perror("FBIOGET_VSCREENINFO");
		status = 1;
		goto out;
	}
	if (!has_region)
		update.update_region = (struct mxcfb_rect){ 0, 0, v.xres, v.yres };
	update.update_marker = wait ? (uint32_t)getpid() : 0;
	if (ioctl(fd, MXCFB_SEND_UPDATE, &update)) {
		perror("MXCFB_SEND_UPDATE");
		status = 1;
		goto out;
	}
	marker.update_marker = update.update_marker;
	if (wait && ioctl(fd, MXCFB_WAIT_FOR_UPDATE_COMPLETE, &marker)) {
		perror("MXCFB_WAIT_FOR_UPDATE_COMPLETE");
		status = 1;
	}
out:
	close(fd);
	return status;
}
