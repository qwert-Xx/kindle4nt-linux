// SPDX-License-Identifier: GPL-2.0-or-later
/* Bounded RAM-only TCP streams, checked independently in each direction. */
#define _GNU_SOURCE
#include <arpa/inet.h>
#include <errno.h>
#include <fcntl.h>
#include <linux/tcp.h>
#include <poll.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <time.h>
#include <unistd.h>

#define BLOCK 4096
#define MAX_BYTES (512ULL * 1024 * 1024)
static uint32_t crc_table[256];
static int64_t deadline;
static clockid_t stream_clock = CLOCK_BOOTTIME;

static int64_t milliseconds(void)
{
	struct timespec t;
	if (clock_gettime(stream_clock, &t)) return -1;
	return (int64_t)t.tv_sec * 1000 + t.tv_nsec / 1000000;
}

static int wait_fd(int fd, short event, int idle_ms)
{
	struct pollfd p = {.fd = fd, .events = event};
	for (;;) {
		int64_t now = milliseconds(), left = deadline - now;
		int ret;
		if (now < 0 || left <= 0) { errno = ETIMEDOUT; return -1; }
		ret = poll(&p, 1, left < idle_ms ? (int)left : idle_ms);
		if (ret < 0 && errno == EINTR) continue;
		if (!ret) errno = ETIMEDOUT;
		if (ret <= 0) return -1;
		/* Drain readable bytes even when the peer has also closed. */
		if (p.revents & event) return 0;
		errno = ECONNRESET;
		return -1;
	}
}

static int transfer(int fd, unsigned char *data, size_t bytes, int sending)
{
	while (bytes) {
		ssize_t n;
		if (wait_fd(fd, sending ? POLLOUT : POLLIN, 30000)) return -1;
		n = sending ? send(fd, data, bytes, MSG_NOSIGNAL) : recv(fd, data, bytes, 0);
		if (n < 0 && (errno == EINTR || errno == EAGAIN)) continue;
		if (n <= 0) { if (!n) errno = ECONNRESET; return -1; }
		data += n;
		bytes -= n;
	}
	return 0;
}

static uint32_t get32(const unsigned char *p)
{
	return (uint32_t)p[0] << 24 | (uint32_t)p[1] << 16 |
	       (uint32_t)p[2] << 8 | p[3];
}

static void put32(unsigned char *p, uint32_t v)
{
	for (int i = 3; i >= 0; i--) { p[i] = v; v >>= 8; }
}

static void block_fill(unsigned char *data, uint64_t position, uint32_t salt)
{
	uint32_t index = position / BLOCK;
	unsigned char key = salt ^ index ^ (index >> 8) ^ (index >> 16);
	for (unsigned i = 0; i < BLOCK; i++) data[i] = ((i * 73 + 19) & 255) ^ key;
	put32(data, position >> 32);
	put32(data + 4, position);
	put32(data + 8, salt);
}

static uint32_t crc_update(uint32_t crc, const unsigned char *data)
{
	for (unsigned i = 0; i < BLOCK; i++) crc = crc_table[(crc ^ data[i]) & 255] ^ (crc >> 8);
	return crc;
}

static void tcp_info(int fd, const char *phase)
{
	struct tcp_info info = {0};
	socklen_t length = sizeof(info);
	if (getsockopt(fd, IPPROTO_TCP, TCP_INFO, &info, &length)) {
		printf("TCP_INFO_ERROR phase=%s errno=%d\n", phase, errno);
		return;
	}
	printf("TCP_INFO phase=%s rtt_us=%u rttvar_us=%u cwnd=%u ssthresh=%u "
	       "snd_mss=%u rcv_mss=%u retrans=%u total_retrans=%u unacked=%u\n",
	       phase, info.tcpi_rtt, info.tcpi_rttvar, info.tcpi_snd_cwnd,
	       info.tcpi_snd_ssthresh, info.tcpi_snd_mss, info.tcpi_rcv_mss,
	       info.tcpi_retrans, info.tcpi_total_retrans, info.tcpi_unacked);
	if (length >= offsetof(struct tcp_info, tcpi_snd_wnd) + sizeof(info.tcpi_snd_wnd)) {
		printf("TCP_INFO_EXT phase=%s rto_us=%u snd_wnd=%u notsent=%u "
		       "busy_us=%llu rwnd_us=%llu sndbuf_us=%llu delivery_Bps=%llu "
		       "app_limited=%u bytes_acked=%llu bytes_retrans=%llu\n",
		       phase, info.tcpi_rto, info.tcpi_snd_wnd, info.tcpi_notsent_bytes,
		       (unsigned long long)info.tcpi_busy_time,
		       (unsigned long long)info.tcpi_rwnd_limited,
		       (unsigned long long)info.tcpi_sndbuf_limited,
		       (unsigned long long)info.tcpi_delivery_rate,
		       info.tcpi_delivery_rate_app_limited,
		       (unsigned long long)info.tcpi_bytes_acked,
		       (unsigned long long)info.tcpi_bytes_retrans);
	} else {
		printf("TCP_INFO_EXT_UNAVAILABLE phase=%s length=%u\n", phase, length);
	}
}

static int stream(int fd)
{
	unsigned char header[24], actual[BLOCK], expected[BLOCK], footer[16];
	uint32_t mode, salt, crc = ~0U;
	uint64_t bytes;
	int64_t start = milliseconds();
	if (transfer(fd, header, sizeof(header), 0)) return -1;
	mode = get32(header + 8);
	salt = get32(header + 12);
	bytes = (uint64_t)get32(header + 16) << 32 | get32(header + 20);
	if (memcmp(header, "K4NET001", 8) || mode > 1 || !bytes ||
	    bytes > MAX_BYTES || bytes % BLOCK) { errno = EINVAL; return -1; }
	tcp_info(fd, "before");
	for (uint64_t pos = 0; pos < bytes; pos += BLOCK) {
		block_fill(expected, pos, salt);
		if (mode) {
			if (transfer(fd, expected, BLOCK, 1)) return -1;
		} else {
			if (transfer(fd, actual, BLOCK, 0)) return -1;
			if (memcmp(actual, expected, BLOCK)) {
				fprintf(stderr, "DATA_MISMATCH offset=%llu\n", (unsigned long long)pos);
				errno = EILSEQ;
				return -1;
			}
		}
		crc = crc_update(crc, expected);
		if ((pos + BLOCK) % (8 * 1024 * 1024) == 0) {
			printf("STREAM_PROGRESS direction=%s bytes=%llu elapsed_ms=%lld\n",
			       mode ? "device-to-host" : "host-to-device",
			       (unsigned long long)(pos + BLOCK),
			       (long long)(milliseconds() - start));
			tcp_info(fd, "progress");
		}
	}
	memcpy(footer, "K4DONE01", 8);
	put32(footer + 8, ~crc);
	put32(footer + 12, bytes / BLOCK);
	if (transfer(fd, footer, sizeof(footer), 1)) return -1;
	tcp_info(fd, "after");
	printf("STREAM_PASS direction=%s bytes=%llu crc32=%08x elapsed_ms=%lld\n",
	       mode ? "device-to-host" : "host-to-device", (unsigned long long)bytes,
	       ~crc, (long long)(milliseconds() - start));
	return 0;
}

static int number(const char *text, unsigned max, unsigned *value)
{
	char *end;
	unsigned long n;
	if (!text[0] || text[0] == '-') return -1;
	errno = 0;
	n = strtoul(text, &end, 10);
	if (errno || *end || !n || n > max) return -1;
	*value = n;
	return 0;
}

static int accept_nonblocking(int listener)
{
	int fd = accept4(listener, NULL, NULL, SOCK_CLOEXEC | SOCK_NONBLOCK);

	if (fd >= 0 || errno != ENOSYS) return fd;
	fd = accept(listener, NULL, NULL);
	if (fd < 0) return fd;
	if (fcntl(fd, F_SETFD, FD_CLOEXEC) || fcntl(fd, F_SETFL, O_NONBLOCK)) {
		int saved = errno;
		close(fd);
		errno = saved;
		return -1;
	}
	printf("STREAM_ACCEPT_LEGACY nonblocking=1 cloexec=1\n");
	return fd;
}

int main(int argc, char **argv)
{
	struct sockaddr_in address = {.sin_family = AF_INET};
	unsigned port, sessions, seconds, tos = 0;
	int listener = -1, fd = -1, result = 1, reuse = 1;
	int64_t now;
	setvbuf(stdout, NULL, _IONBF, 0);
	if (argc > 5 && !strcmp(argv[argc - 1], "--awake")) {
		stream_clock = CLOCK_MONOTONIC;
		argc--;
	}
	if ((argc != 5 && argc != 6) || inet_pton(AF_INET, argv[1], &address.sin_addr) != 1 ||
	    number(argv[2], 65535, &port) || number(argv[3], 32, &sessions) ||
	    number(argv[4], 1800, &seconds) ||
	    (argc == 6 && strcmp(argv[5], "0") && number(argv[5], 255, &tos))) {
		fprintf(stderr, "Usage: network-stream-probe IPv4 PORT SESSIONS SECONDS [TOS] [--awake]\n");
		return 1;
	}
	address.sin_port = htons(port);
	now = milliseconds();
	if (now < 0) goto out;
	deadline = now + seconds * 1000;
	for (unsigned i = 0; i < 256; i++) {
		uint32_t v = i;
		for (unsigned b = 0; b < 8; b++) v = (v >> 1) ^ ((v & 1) ? 0xedb88320 : 0);
		crc_table[i] = v;
	}
	listener = socket(AF_INET, SOCK_STREAM | SOCK_CLOEXEC | SOCK_NONBLOCK, 0);
	if (listener < 0 || setsockopt(listener, SOL_SOCKET, SO_REUSEADDR, &reuse, sizeof(reuse)) ||
	    setsockopt(listener, IPPROTO_IP, IP_TOS, &tos, sizeof(tos)) ||
	    bind(listener, (struct sockaddr *)&address, sizeof(address)) || listen(listener, 4)) goto out;
	printf("STREAM_READY address=%s port=%u sessions=%u deadline_s=%u tos=%u clock=%s\n",
	       argv[1], port, sessions, seconds, tos,
	       stream_clock == CLOCK_BOOTTIME ? "boottime" : "monotonic-awake");
	for (unsigned i = 0; i < sessions; i++) {
		if (wait_fd(listener, POLLIN, 120000)) goto out;
		fd = accept_nonblocking(listener);
		if (fd < 0 || stream(fd)) goto out;
		close(fd);
		fd = -1;
	}
	printf("NETWORK_STREAM_PASS sessions=%u\n", sessions);
	result = 0;
out:
	if (result) perror("network-stream-probe");
	if (fd >= 0) close(fd);
	if (listener >= 0) close(listener);
	return result;
}
