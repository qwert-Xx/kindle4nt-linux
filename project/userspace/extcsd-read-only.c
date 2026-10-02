/* SPDX-License-Identifier: GPL-2.0-or-later */
/* Diagnostic CMD8 only; never switches partitions or writes data. */
#include <fcntl.h>
#include <unistd.h>
#include <stdint.h>
#include <stdio.h>
#include <sys/ioctl.h>
#include <linux/mmc/ioctl.h>
int main(int argc,char **argv){uint8_t data[512]={0};struct mmc_ioc_cmd c={0};int fd;if(argc!=2)return 2;fd=open(argv[1],O_RDONLY);if(fd<0){perror("open");return 1;}c.opcode=8;c.flags=0xb5;c.blksz=512;c.blocks=1;c.write_flag=0;mmc_ioc_cmd_set_data(c,data);if(ioctl(fd,MMC_IOC_CMD,&c)){perror("CMD8");close(fd);return 1;}close(fd);return write(1,data,512)==512?0:1;}
