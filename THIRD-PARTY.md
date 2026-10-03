<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Third-party components and external proprietary inputs

Only project source, patches, recipes and build scripts are distributed. Upstream archives and APKs are external inputs, pinned in [sources/manifest.json](sources/manifest.json). Each upstream archive/package retains its own full notices. A license listed below summarizes package metadata; it does not relicense bundled subcomponents.

| Component | Version | License | Source |
| --- | --- | --- | --- |
| Linux | 6.6.157 | GPL-2.0-only | [upstream](https://www.kernel.org/pub/linux/kernel/v6.x/linux-6.6.157.tar.xz) |
| barebox | 2026.09.0 | GPL-2.0-only | [upstream](https://www.barebox.org/download/barebox-2026.09.0.tar.bz2) |
| BusyBox | 1.31.1 | GPL-2.0-only | [upstream](https://busybox.net/downloads/busybox-1.31.1.tar.bz2) |
| Dropbear | 2024.86 | MIT AND BSD-2-Clause | [upstream](https://matt.ucc.asn.au/dropbear/releases/dropbear-2024.86.tar.bz2) |
| wpa_supplicant | 2.11 | BSD-3-Clause | [upstream](https://w1.fi/releases/wpa_supplicant-2.11.tar.gz) |
| libnl | 3.12.0 | LGPL-2.1-only | [upstream](https://github.com/thom311/libnl/releases/download/libnl3_12_0/libnl-3.12.0.tar.gz) |
| iw | 6.17 | ISC | [upstream](https://www.kernel.org/pub/software/network/iw/iw-6.17.tar.xz) |
| wireless-regdb | 2026.09.03 | ISC | [upstream](https://www.kernel.org/pub/software/network/wireless-regdb/wireless-regdb-2026.09.03.tar.xz) |
| kexec-tools | 2.0.32 | GPL-2.0-only | [upstream](https://www.kernel.org/pub/linux/utils/kernel/kexec/kexec-tools-2.0.32.tar.xz) |
| Linaro cross toolchain | 4.9.4-2017.01 | GPL-3.0-or-later AND LGPL-2.1-or-later AND BSD-3-Clause | [upstream](https://releases.linaro.org/components/toolchain/binaries/4.9-2017.01/arm-linux-gnueabi/gcc-linaro-4.9.4-2017.01-x86_64_arm-linux-gnueabi.tar.xz) |
| e2fsprogs | 1.47.1 | GPL-2.0-only AND LGPL-2.0-only AND BSD-3-Clause AND MIT | [upstream](https://www.kernel.org/pub/linux/kernel/people/tytso/e2fsprogs/v1.47.1/e2fsprogs-1.47.1.tar.xz) |
| mmc-utils | v1.0 | GPL-2.0-only AND BSD-3-Clause | [upstream](https://git.kernel.org/pub/scm/utils/mmc/mmc-utils.git/snapshot/mmc-utils-v1.0.tar.gz) |
| Alpine libedit | 20260508.3.1-r1 | BSD-3-Clause | [official APK](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/libedit-20260508.3.1-r1.apk) |
| Alpine openssh | 10.3_p1-r1 | SSH-OpenSSH | [official APK](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/openssh-10.3_p1-r1.apk) |
| Alpine openssh-client-common | 10.3_p1-r1 | SSH-OpenSSH | [official APK](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/openssh-client-common-10.3_p1-r1.apk) |
| Alpine openssh-client-default | 10.3_p1-r1 | SSH-OpenSSH | [official APK](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/openssh-client-default-10.3_p1-r1.apk) |
| Alpine openssh-keygen | 10.3_p1-r1 | SSH-OpenSSH | [official APK](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/openssh-keygen-10.3_p1-r1.apk) |
| Alpine openssh-server | 10.3_p1-r1 | SSH-OpenSSH | [official APK](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/openssh-server-10.3_p1-r1.apk) |
| Alpine openssh-server-common | 10.3_p1-r1 | SSH-OpenSSH | [official APK](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/openssh-server-common-10.3_p1-r1.apk) |
| Alpine openssh-server-common-openrc | 10.3_p1-r1 | SSH-OpenSSH | [official APK](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/openssh-server-common-openrc-10.3_p1-r1.apk) |
| Alpine openssh-sftp-server | 10.3_p1-r1 | SSH-OpenSSH | [official APK](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/openssh-sftp-server-10.3_p1-r1.apk) |
| Alpine minirootfs | 3.24.2 | See contained Alpine package metadata | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/releases/armv7/alpine-minirootfs-3.24.2-armv7.tar.gz) |
| Alpine host_apk | 3.0.8-r0 | GPL-2.0-only | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/x86_64/apk-tools-static-3.0.8-r0.apk) |
| Alpine host_mini | 3.24.2 | See contained Alpine package metadata | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/releases/x86_64/alpine-minirootfs-3.24.2-x86_64.tar.gz) |
| Alpine agetty | 2.42.3-r1 | Public-Domain | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/agetty-2.42.3-r1.apk) |
| Alpine agetty-openrc | 0.63.2-r0 | BSD-2-Clause | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/agetty-openrc-0.63.2-r0.apk) |
| Alpine alpine-baselayout | 3.7.2-r1 | GPL-2.0-only | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/alpine-baselayout-3.7.2-r1.apk) |
| Alpine alpine-baselayout-data | 3.7.2-r1 | GPL-2.0-only | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/alpine-baselayout-data-3.7.2-r1.apk) |
| Alpine alpine-keys | 2.6-r0 | MIT | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/alpine-keys-2.6-r0.apk) |
| Alpine alpine-release | 3.24.2-r0 | MIT | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/alpine-release-3.24.2-r0.apk) |
| Alpine apk-tools | 3.0.8-r0 | GPL-2.0-only | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/apk-tools-3.0.8-r0.apk) |
| Alpine blkid | 2.42.3-r1 | LGPL-1.0-only | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/blkid-2.42.3-r1.apk) |
| Alpine busybox | 1.37.0-r31 | GPL-2.0-only | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/busybox-1.37.0-r31.apk) |
| Alpine busybox-binsh | 1.37.0-r31 | GPL-2.0-only | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/busybox-binsh-1.37.0-r31.apk) |
| Alpine busybox-ifupdown | 1.37.0-r31 | GPL-2.0-only | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/busybox-ifupdown-1.37.0-r31.apk) |
| Alpine ca-certificates | 20260909-r0 | MPL-2.0 AND MIT | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/ca-certificates-20260909-r0.apk) |
| Alpine ca-certificates-bundle | 20260909-r0 | MPL-2.0 AND MIT | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/ca-certificates-bundle-20260909-r0.apk) |
| Alpine cfdisk | 2.42.3-r1 | GPL-2.0-or-later | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/cfdisk-2.42.3-r1.apk) |
| Alpine dbus-libs | 1.16.2-r2 | AFL-2.1 OR GPL-2.0-or-later | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/dbus-libs-1.16.2-r2.apk) |
| Alpine dmesg | 2.42.3-r1 | GPL-3.0-or-later AND GPL-2.0-or-later AND GPL-2.0-only AND GPL-1.0-only AND LGPL-2.1-or-later AND BSD-1-Clause AND BSD-3-Clause AND BSD-4-Clause-UC AND MIT AND Public-Domain | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/dmesg-2.42.3-r1.apk) |
| Alpine e2fsprogs | 1.47.4-r0 | GPL-2.0-or-later AND LGPL-2.0-or-later AND BSD-3-Clause AND MIT | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/e2fsprogs-1.47.4-r0.apk) |
| Alpine e2fsprogs-libs | 1.47.4-r0 | GPL-2.0-or-later AND LGPL-2.0-or-later AND BSD-3-Clause AND MIT | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/e2fsprogs-libs-1.47.4-r0.apk) |
| Alpine findmnt | 2.42.3-r1 | GPL-2.0-or-later | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/findmnt-2.42.3-r1.apk) |
| Alpine flock | 2.42.3-r1 | MIT | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/flock-2.42.3-r1.apk) |
| Alpine fstrim | 2.42.3-r1 | GPL-2.0-or-later | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/fstrim-2.42.3-r1.apk) |
| Alpine hexdump | 2.42.3-r1 | BSD-4-Clause-UC | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/hexdump-2.42.3-r1.apk) |
| Alpine iw | 6.17-r0 | ISC | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/iw-6.17-r0.apk) |
| Alpine kmod | 34.2-r1 | GPL-2.0-or-later | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/kmod-34.2-r1.apk) |
| Alpine libapk | 3.0.8-r0 | GPL-2.0-only | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/libapk-3.0.8-r0.apk) |
| Alpine libblkid | 2.42.3-r1 | LGPL-2.1-or-later | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/libblkid-2.42.3-r1.apk) |
| Alpine libcap-ng | 0.8.5-r2 | GPL-2.0-or-later AND LGPL-2.1-or-later | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/libcap-ng-0.8.5-r2.apk) |
| Alpine libcap2 | 2.78-r0 | BSD-3-Clause OR GPL-2.0-only | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/libcap2-2.78-r0.apk) |
| Alpine libcom_err | 1.47.4-r0 | GPL-2.0-or-later AND LGPL-2.0-or-later AND BSD-3-Clause AND MIT | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/libcom_err-1.47.4-r0.apk) |
| Alpine libcrypto3 | 3.5.9-r0 | Apache-2.0 | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/libcrypto3-3.5.9-r0.apk) |
| Alpine libeconf | 0.8.3-r0 | MIT | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/libeconf-0.8.3-r0.apk) |
| Alpine libfdisk | 2.42.3-r1 | LGPL-2.1-or-later | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/libfdisk-2.42.3-r1.apk) |
| Alpine libgcc | 15.2.0-r5 | GPL-2.0-or-later AND LGPL-2.1-or-later | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/libgcc-15.2.0-r5.apk) |
| Alpine libmount | 2.42.3-r1 | LGPL-2.1-or-later | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/libmount-2.42.3-r1.apk) |
| Alpine libncursesw | 6.6_p20260516-r0 | X11 | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/libncursesw-6.6_p20260516-r0.apk) |
| Alpine libnl3 | 3.11.0-r0 | LGPL-2.1-or-later | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/libnl3-3.11.0-r0.apk) |
| Alpine libsmartcols | 2.42.3-r1 | LGPL-2.1-or-later | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/libsmartcols-2.42.3-r1.apk) |
| Alpine libssl3 | 3.5.9-r0 | Apache-2.0 | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/libssl3-3.5.9-r0.apk) |
| Alpine libuuid | 2.42.3-r1 | BSD-3-Clause | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/libuuid-2.42.3-r1.apk) |
| Alpine linux-pam | 1.7.1-r2 | BSD-3-Clause | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/linux-pam-1.7.1-r2.apk) |
| Alpine logger | 2.42.3-r1 | BSD-4-Clause-UC | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/logger-2.42.3-r1.apk) |
| Alpine losetup | 2.42.3-r1 | GPL-2.0-or-later | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/losetup-2.42.3-r1.apk) |
| Alpine lsblk | 2.42.3-r1 | GPL-2.0-or-later | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/lsblk-2.42.3-r1.apk) |
| Alpine lscpu | 2.42.3-r1 | GPL-2.0-or-later | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/lscpu-2.42.3-r1.apk) |
| Alpine mcookie | 2.42.3-r1 | Public-Domain | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/mcookie-2.42.3-r1.apk) |
| Alpine mount | 2.42.3-r1 | GPL-3.0-or-later AND GPL-2.0-or-later AND GPL-2.0-only AND GPL-1.0-only AND LGPL-2.1-or-later AND BSD-1-Clause AND BSD-3-Clause AND BSD-4-Clause-UC AND MIT AND Public-Domain | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/mount-2.42.3-r1.apk) |
| Alpine musl | 1.2.6-r2 | MIT | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/musl-1.2.6-r2.apk) |
| Alpine musl-utils | 1.2.6-r2 | MIT AND BSD-2-Clause AND GPL-2.0-or-later | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/musl-utils-1.2.6-r2.apk) |
| Alpine ncurses-terminfo-base | 6.6_p20260516-r0 | X11 | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/ncurses-terminfo-base-6.6_p20260516-r0.apk) |
| Alpine openrc | 0.63.2-r0 | BSD-2-Clause | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/openrc-0.63.2-r0.apk) |
| Alpine openrc-user | 0.63.2-r0 | BSD-2-Clause | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/openrc-user-0.63.2-r0.apk) |
| Alpine partx | 2.42.3-r1 | GPL-2.0-or-later | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/partx-2.42.3-r1.apk) |
| Alpine pcsc-lite-libs | 2.4.0-r4 | BSD-3-Clause AND BSD-2-Clause AND ISC | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/pcsc-lite-libs-2.4.0-r4.apk) |
| Alpine runuser | 2.42.3-r1 | GPL-2.0-or-later | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/runuser-2.42.3-r1.apk) |
| Alpine scanelf | 1.3.9-r1 | GPL-2.0-only | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/scanelf-1.3.9-r1.apk) |
| Alpine setarch | 2.42.3-r1 | GPL-3.0-or-later AND GPL-2.0-or-later AND GPL-2.0-only AND GPL-1.0-only AND LGPL-2.1-or-later AND BSD-1-Clause AND BSD-3-Clause AND BSD-4-Clause-UC AND MIT AND Public-Domain | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/setarch-2.42.3-r1.apk) |
| Alpine setpriv | 2.42.3-r1 | GPL-2.0-or-later | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/setpriv-2.42.3-r1.apk) |
| Alpine sfdisk | 2.42.3-r1 | GPL-1.0-or-later | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/sfdisk-2.42.3-r1.apk) |
| Alpine skalibs-libs | 2.15.0.0-r0 | ISC | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/skalibs-libs-2.15.0.0-r0.apk) |
| Alpine ssl_client | 1.37.0-r31 | GPL-2.0-only | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/ssl_client-1.37.0-r31.apk) |
| Alpine umount | 2.42.3-r1 | GPL-3.0-or-later AND GPL-2.0-or-later AND GPL-2.0-only AND GPL-1.0-only AND LGPL-2.1-or-later AND BSD-1-Clause AND BSD-3-Clause AND BSD-4-Clause-UC AND MIT AND Public-Domain | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/umount-2.42.3-r1.apk) |
| Alpine util-linux | 2.42.3-r1 | GPL-3.0-or-later AND GPL-2.0-or-later AND GPL-2.0-only AND GPL-1.0-only AND LGPL-2.1-or-later AND BSD-1-Clause AND BSD-3-Clause AND BSD-4-Clause-UC AND MIT AND Public-Domain | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/util-linux-2.42.3-r1.apk) |
| Alpine util-linux-misc | 2.42.3-r1 | GPL-3.0-or-later AND GPL-2.0-or-later AND GPL-2.0-only AND GPL-1.0-only AND LGPL-2.1-or-later AND BSD-1-Clause AND BSD-3-Clause AND BSD-4-Clause-UC AND MIT AND Public-Domain | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/util-linux-misc-2.42.3-r1.apk) |
| Alpine util-linux-openrc | 2.42.3-r1 | GPL-3.0-or-later AND GPL-2.0-or-later AND GPL-2.0-only AND GPL-1.0-only AND LGPL-2.1-or-later AND BSD-1-Clause AND BSD-3-Clause AND BSD-4-Clause-UC AND MIT AND Public-Domain | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/util-linux-openrc-2.42.3-r1.apk) |
| Alpine utmps-libs | 0.1.3.3-r0 | ISC | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/utmps-libs-0.1.3.3-r0.apk) |
| Alpine uuidgen | 2.42.3-r1 | GPL-1.0-only | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/uuidgen-2.42.3-r1.apk) |
| Alpine wipefs | 2.42.3-r1 | GPL-2.0-or-later | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/wipefs-2.42.3-r1.apk) |
| Alpine xz-libs | 5.8.4-r0 | GPL-2.0-or-later AND 0BSD AND Public-Domain AND LGPL-2.1-or-later | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/xz-libs-5.8.4-r0.apk) |
| Alpine zlib | 1.3.2-r0 | Zlib | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/zlib-1.3.2-r0.apk) |
| Alpine zstd-libs | 1.5.7-r2 | BSD-3-Clause OR GPL-2.0-or-later | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/zstd-libs-1.5.7-r2.apk) |
| Alpine wpa_supplicant | 2.11-r4 | BSD-3-Clause | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/wpa_supplicant-2.11-r4.apk) |
| Alpine wpa_supplicant-openrc | 2.11-r4 | BSD-3-Clause | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/wpa_supplicant-openrc-2.11-r4.apk) |
| Alpine bridge | 1.5-r5 | GPL-2.0-or-later | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/bridge-1.5-r5.apk) |
| Alpine ifupdown-ng | 0.13.0-r0 | ISC | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/ifupdown-ng-0.13.0-r0.apk) |
| Alpine ifupdown-ng-wifi | 0.13.0-r0 | ISC | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/ifupdown-ng-wifi-0.13.0-r0.apk) |
| Alpine signed index | frozen 3.24.2 package snapshot | Alpine package metadata | [upstream](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/armv7/APKINDEX.tar.gz) |
| QEMU host user emulation | 8.2.2+ds-0ubuntu1.18 | GPL-2.0-only | [upstream](https://archive.ubuntu.com/ubuntu/pool/universe/q/qemu/qemu-user-static_8.2.2%2bds-0ubuntu1.18_amd64.deb) |

## Original stock source and copyright

Stock GPL source: Amazon Kindle 4.1.1 kernel and the matching Yoshi U-Boot sources, obtained through [Amazon source-code notices](https://www.amazon.com/gp/help/customer/display.html?nodeId=200203720). Amazon/Lab126/Freescale notices must remain with derivative code. The per-file evidence and unresolved questions are in [COPYRIGHT-PROVENANCE.md](COPYRIGHT-PROVENANCE.md). Upstream GPL source is not proprietary firmware.

## Inputs from your own device or backups

These files are not included, and this project does not grant redistribution rights. Extraction is a separate manual operation, not executed by the build. Prefer an existing host backup; the release task does not access hardware.

- **AR6003 firmware/calibration**: copy the firmware directory used by the stock driver (typically `/lib/firmware/ath6k/AR6003/hw2.1.1/`) from your own stock root backup. Preserve board calibration and all original bytes. Stage the matching path under `device-inputs/lib/firmware/`; identify the actual firmware/board paths from your stock driver rather than substituting another device’s calibration.
- **Panel waveform/VCOM data**: copy the matching stock WBF/WRF pair and panel calibration from your own backup; consult [waveform analysis](project/docs/KNOWN-ISSUES.md) and the original driver/loader names. Keep these under the paths requested by the kernel firmware loader in `device-inputs/lib/firmware/`. Do not use a waveform merely because the screen size matches. Hash both files and preserve their pairing; the loader consumes the WRF proxy, not a raw WBF alone.
- **boot0/idme**: read the complete eMMC boot0 area from your own existing backup (or in a separately authorized RAM maintenance session: `dd if=/dev/mmcblk2boot0 of=/tmp/boot0.bin bs=512`, after confirming the block-device identity). Copy it to the host and compare hashes, then supply `device-inputs/boot0.bin`. It contains device identity/idme: never commit or share it. The boot1 wrapper reads the original ROM header/entry reference; it does not publish this backup. Do not write boot0 to extract it.
- **Wi-Fi/SSH configuration**: stage your own `etc/wpa_supplicant.conf`, `root/.ssh/authorized_keys` and an external OpenSSH ECDSA identity via `--ssh-host-key` for Alpine. BusyBox RAM maintenance separately uses optional `etc/dropbear/` identity. They are not project source. Hash/examine the external inputs locally and never commit credentials or private host keys.

Alpine uses the official main wpa_supplicant 2.11-r4 APK and matching OpenRC split package, authenticated with Alpine keys. BusyBox maintenance and persistent roots build unmodified upstream 2.11 statically with libnl. No local WPA signing key or repository is required.

Official Alpine minirootfs/APKs (including Alpine BusyBox 1.37.0) are package inputs authenticated with Alpine keys extracted from the hash-locked minirootfs. K4’s separate BusyBox 1.31.1 maintenance binaries are source-built. The package recipes and source URLs of Alpine packages are available from [Alpine aports](https://gitlab.alpinelinux.org/alpine/aports); the APK license metadata is recorded above. This workflow does not claim to rebuild every Alpine distribution package from source.

Host environment: Ubuntu ARMhf GCC 13.3.0-6ubuntu2~24.04.1, binutils 2.42, glibc cross development files and Python 3.12; make, openssl, GNU tar, GnuPG, patch and pkg-config. Host tools are prerequisites, not redistributed project components. Static glibc/toolchain redistribution would require their own GPL/LGPL obligations. No binary distribution is planned.
