// SPDX-License-Identifier: GPL-2.0-or-later
/* Explicit fbdev exerciser. No argument only queries geometry. */
#include <errno.h>
#include <fcntl.h>
#include <linux/fb.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <unistd.h>

static int fail(const char *operation)
{
	perror(operation);
	return 1;
}

static int show_usage(const char *program)
{
	fprintf(stderr, "usage: %s ACTION\n", program);
	fputs("  info | pattern-write | pattern-mmap | patch-write\n", stderr);
	fputs("  blank | unblank | console-bind\n", stderr);
	fputs("  mode BPP DEGREES | mode-pattern BPP DEGREES\n  mmap-mode-pattern BPP DEGREES\n", stderr);
	return 2;
}

static int number(const char *text, unsigned long *value)
{
	char *end;

	errno = 0;
	*value = strtoul(text, &end, 10);
	return errno || end == text || *end;
}

static void pixel(void *base, size_t offset, unsigned int bpp, uint32_t rgb)
{
	unsigned int r = (rgb >> 16) & 255, g = (rgb >> 8) & 255, b = rgb & 255;

	if (bpp == 32)
		*(uint32_t *)((char *)base + offset) = rgb;
	else if (bpp == 16)
		*(uint16_t *)((char *)base + offset) = ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3);
	else
		*((uint8_t *)base + offset) = (77 * r + 150 * g + 29 * b + 128) >> 8;
}

int main(int argc, char **argv)
{
	const char *action = argc > 1 ? argv[1] : "info";
	struct fb_var_screeninfo v;
	struct fb_fix_screeninfo f;
	void *pixels = NULL;
	size_t bytes, mapped_bytes = 0, done = 0;
	unsigned long bpp = 0, degrees = 0;
	int fd, control, mapped = 0;
	int held = !strcmp(action, "mmap-mode-pattern");
	int mode = held || !strcmp(action, "mode") || !strcmp(action, "mode-pattern");
	int changed = 0;

	if (mode) {
		if (argc != 4 || number(argv[2], &bpp) || number(argv[3], &degrees) ||
		    (bpp != 8 && bpp != 16 && bpp != 32) || degrees > 270 || degrees % 90)
			return show_usage(argv[0]);
	} else if (argc > 2 || (strcmp(action, "info") && strcmp(action, "pattern-write") &&
			strcmp(action, "pattern-mmap") && strcmp(action, "patch-write") &&
			strcmp(action, "blank") && strcmp(action, "console-bind") &&
			strcmp(action, "unblank"))) {
		return show_usage(argv[0]);
	}
	fd = open("/dev/fb0", !strcmp(action, "info") ? O_RDONLY : O_RDWR);
	if (fd < 0)
		return fail("open fb0");
	if (ioctl(fd, FBIOGET_VSCREENINFO, &v))
		return fail("framebuffer variable geometry");
	if (held) {
		if (ioctl(fd, FBIOGET_FSCREENINFO, &f))
			return fail("get mapping capacity");
		mapped_bytes = f.smem_len;
		if (!mapped_bytes)
			return 1;
		pixels = mmap(NULL, mapped_bytes, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
		if (pixels == MAP_FAILED)
			return fail("map before mode change");
		((volatile unsigned char *)pixels)[mapped_bytes - 1] = 0x5a;
		changed = v.bits_per_pixel != bpp || v.rotate != degrees / 90;
	}
	if (mode) {
		v.rotate = degrees / 90;
		v.xres = v.xres_virtual = v.rotate & 1 ? 600 : 800;
		v.yres = v.yres_virtual = v.rotate & 1 ? 800 : 600;
		v.bits_per_pixel = bpp;
		v.grayscale = bpp == 8;
		v.xoffset = v.yoffset = v.nonstd = 0;
		v.vmode = FB_VMODE_NONINTERLACED;
		v.activate = FB_ACTIVATE_NOW | FB_ACTIVATE_FORCE;
		if (ioctl(fd, FBIOPUT_VSCREENINFO, &v) || ioctl(fd, FBIOGET_VSCREENINFO, &v))
			return fail("set framebuffer mode");
		if (v.bits_per_pixel != bpp || v.rotate != degrees / 90) {
			fprintf(stderr, "mode readback mismatch\n");
			return 1;
		}
	}
	if (ioctl(fd, FBIOGET_FSCREENINFO, &f))
		return fail("framebuffer fixed geometry");
	printf("%.16s %ux%u virtual=%ux%u bpp=%u rotation=%u stride=%u capacity=%u\n",
	       f.id, v.xres, v.yres, v.xres_virtual, v.yres_virtual,
	       v.bits_per_pixel, v.rotate * 90, f.line_length, f.smem_len);
	if (!strcmp(action, "info") || !strcmp(action, "mode")) {
		close(fd);
		return 0;
	}
	if (held && (f.smem_len != mapped_bytes ||
	    (changed && ((volatile unsigned char *)pixels)[mapped_bytes - 1] != 0xff))) {
		fprintf(stderr, "held mapping or mode clear mismatch\n");
		return 1;
	}
	/* This is the physical K4 pattern layout, not a restriction in the API. */
	bytes = (size_t)f.line_length * v.yres;
	if ((v.xres != 800 || v.yres != 600) && (v.xres != 600 || v.yres != 800)) {
		fprintf(stderr, "unexpected panel geometry\n");
		return 1;
	}
	if ((v.bits_per_pixel != 32 && v.bits_per_pixel != 16 && v.bits_per_pixel != 8) ||
	    f.line_length != v.xres * (v.bits_per_pixel / 8) || f.smem_len < bytes) {
		fprintf(stderr, "unexpected format for this probe\n");
		return 1;
	}
	if (!strcmp(action, "console-bind")) {
		struct fb_con2fbmap map = { .console = 1 };

		if (ioctl(fd, FBIOGET_CON2FBMAP, &map))
			return fail("get console map");
		printf("Console 1 framebuffer before=%u\n", map.framebuffer);
		map.framebuffer = 0;
		if (ioctl(fd, FBIOPUT_CON2FBMAP, &map) || ioctl(fd, FBIOGET_CON2FBMAP, &map))
			return fail("bind framebuffer console");
		if (map.framebuffer != 0)
			return 1;
		printf("Console 1 framebuffer after=%u\n", map.framebuffer);
		close(fd);
		return 0;
	}
	if (!strcmp(action, "blank") || !strcmp(action, "unblank")) {
		int level = !strcmp(action, "blank") ? FB_BLANK_POWERDOWN : FB_BLANK_UNBLANK;

		if (ioctl(fd, FBIOBLANK, level))
			return fail("FBIOBLANK");
		close(fd);
		return 0;
	}
	if (!strcmp(action, "patch-write")) {
		uint32_t row[80] = {0};
		size_t length = 80 * (v.bits_per_pixel / 8);
		unsigned int left = v.xres / 2 - 40, top = v.yres / 3 - 40;

		for (unsigned int y = top; y < top + 80; y++) {
			off_t offset = (off_t)y * f.line_length + left * (v.bits_per_pixel / 8);

			if (pwrite(fd, row, length, offset) != (ssize_t)length)
				return fail("write patch");
		}
		goto refresh;
	}
	mapped = held || !strcmp(action, "pattern-mmap");
	if (!held) {
		mapped_bytes = bytes;
		pixels = mapped ? mmap(NULL, bytes, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0) :
			malloc(bytes);
	}
	if (pixels == MAP_FAILED || !pixels)
		return fail("pattern buffer");
	for (unsigned int y = 0; y < v.yres; y++) {
		for (unsigned int x = 0; x < v.xres; x++) {
			unsigned int grey = (x * 16 / v.xres) * 17;
			uint32_t rgb;

			if (y >= v.yres * 2 / 3)
				grey = ((x / 40 + y / 40) & 1) ? 255 : 0;
			if (!strcmp(action, "pattern-mmap"))
				grey = 255 - grey;
			rgb = grey * 0x010101;
			if (held || !strcmp(action, "mode-pattern")) {
				int distance = abs((int)x - (int)v.xres / 2);

				/* White-framed origin mark and an arrow pointing to logical UP. */
				if ((x >= 16 && x < 96 && y >= 16 && y < 96) ||
				    (distance < 70 && y >= 24 && y < 200))
					rgb = 0xffffff;
				if ((x >= 32 && x < 80 && y >= 32 && y < 80) ||
				    (y >= 40 && y < 90 && distance <= (int)y - 40) ||
				    (y >= 90 && y < 150 && distance <= 10))
					rgb = 0;
				if (distance < 60 && y >= 164 && y < 196) {
					int stripe = ((int)x - ((int)v.xres / 2 - 60)) / 40;

					rgb = stripe == 0 ? 0xff0000 : stripe == 1 ? 0x00ff00 : 0x0000ff;
				}
			}
			pixel(pixels, (size_t)y * f.line_length + x * (v.bits_per_pixel / 8),
			      v.bits_per_pixel, rgb);
		}
	}
	if (held) {
		/* Exercise the old VMA beyond the active canvas, still inside its allocation. */
		if (bytes < mapped_bytes) {
			((volatile unsigned char *)pixels)[mapped_bytes - 1] = 0xa5;
			if (((volatile unsigned char *)pixels)[mapped_bytes - 1] != 0xa5)
				return 1;
		}
		printf("Held mmap survives mode change: capacity=%zu active=%zu changed=%d\n",
		       mapped_bytes, bytes, changed);
	}
	if (!mapped) {
		while (done < bytes) {
			ssize_t n = write(fd, (char *)pixels + done, bytes - done);

			if (n < 0 && errno == EINTR)
				continue;
			if (n <= 0)
				return fail("write pattern");
			done += n;
		}
	}
refresh:
	if (fsync(fd))
		return fail("fsync fb0");
	/* fsync drains deferred work; explicit refresh returns its I/O result. */
	control = open("/sys/bus/platform/devices/framebuffer/refresh", O_WRONLY);
	if (control < 0)
		return fail("open refresh");
	if (write(control, "1\n", 2) != 2)
		return fail("refresh");
	close(control);
	if (mapped)
		munmap(pixels, mapped_bytes);
	else
		free(pixels);
	close(fd);
	puts("Display request completed; inspect framebuffer/state and the physical panel.");
	return 0;
}
