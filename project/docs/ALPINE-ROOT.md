<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# 当前配方：Alpine 标准网络与 OpenSSH

当前根与证据以 [OpenSSH 离线交付](ALPINE-OPENSSH-OFFLINE-20261003.md) 为准；下面旧交付SHA为历史记录。

<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Alpine 3.24.2 armv7 官方 Wi-Fi 根配方

仅发布配方；固件、校准、波形、凭据、SSH身份和产物不入Git。官方 main 的 wpa_supplicant 和 wpa_supplicant-openrc 固定2.11-r4，APK/SHA见 packages.lock.json 与 PACKAGES.tsv。无需本地仓库、用户签名密钥或本地APK构建。使用官方OpenRC wpa_supplicant、wpa_cli与networking/ifupdown-ng；WPACLI_OPTS启用默认动作脚本。配置、依赖及验证见 ALPINE-STANDARD-NETWORK-OFFLINE-20261003.md。凭据放默认子目录，600；仅Alpine根删除K4 Wi-Fi supervisor，BusyBox根保持。

kindle UID1000、LF、纯离线组装。download.py取得锁定输入；build.py用官方签名索引和包、--no-network/--no-scripts安装。内核、方案A DTB和23模块须匹配 kernel.lock.json。BusyBox tar为外部私有输入。

```sh
python3 project/alpine/download.py --out /absolute/cache
python3 project/alpine/build.py --cache /absolute/cache --busybox-tar /absolute/busybox-root.tar.gz --busybox-sha EXPECTED_SHA --kernel /absolute/zImage --dtb /absolute/imx50-kindle-k4.dtb --modules /absolute/lib/modules --out /absolute/new-alpine-a
# 相同输入另建 new-alpine-b
python3 project/alpine/verify.py --build /absolute/new-alpine-a --compare /absolute/new-alpine-b
```

扫描中止结论及既有实机证据见 WIFI-SCAN-ABORT.md；新离线产物和复现结果见 WIFI-211-OFFLINE-20261003.md。本次没有操作设备；离线构建不是新增设备验收。

Alpine 使用官方 OpenSSH 10.3_p1-r1 与标准 sshd OpenRC 服务，22 端口、所有 IPv4/IPv6 地址监听，仅 root 公钥认证，启用 internal-sftp。USB 地址 169.254.212.2 和 Wi-Fi 均可连接；USB gadget 仍在 k4-platform，ttyGS0 root shell 保留。RAM 维护根保持 Dropbear/2222。Alpine 不再包含 Dropbear 包、k4-usb-ssh 或 k4-userspace-service。

主机密钥用构建参数 `--ssh-host-key /absolute/ssh_host_ecdsa_key` 提供仓库外 OpenSSH 格式 ECDSA 私钥（600），公钥自动派生（644）；沿用既有身份。未提供时，官方 sshd 首次启动按 `key_types_to_generate="ecdsa"` 生成，不在构建时随机生成。`--authorized-keys /absolute/authorized_keys` 提供 root 公钥授权（600），也可沿用外部 K4 根的 root/.ssh/authorized_keys。私钥和凭据不入库。Alpine 连接：`ssh root@169.254.212.2`；RAM 维护：`ssh -p 2222 root@169.254.212.2`。

## 时间与原厂做法

原厂启动 hwclock -u -s，正常 halt/reboot hwclock -u -w。Alpine OpenRC hwclock采用同一UTC SRTC rtc0，hctosys/systohc=YES、adjfile=NO；rtc1为PMIC，不自动按日期大小切换、不回写PMIC。
可选 k4-ntpd 用 BusyBox ntpd -n -p pool.ntp.org、依赖Wi-Fi/hwclock；DHCP/DNS/UDP123需可用，正常关机保存纠正后的时间。RTC为1970时 hwclock 本身不能创造正确日期。强制reboot、掉电/watchdog不保证关机回写。无固定构建时间兜底或TLS绕过。禁用/启用：rc-update del/add k4-ntpd default。原厂epoch下限策略未照搬。
既有Alpine验收确认NTP纠正、正常重启SRTC读写与官方HTTPS apk update；未执行upgrade或完整耗尽电池测试。

## 部署与回退（说明，不自动执行）

1. 准备主机核验的p1/完整用户区与boot备份、ROM人工恢复路径、足电和维护工具。v8 Ctrl-C→shell→YMODEM加载方案A RAM维护包；确认RAM运行、guard健康且时间足够、p1未挂载（含/dev/root或UUID），eMMC只读。不要在正在运行的Alpine根执行格式化。
2. 上传tar、修正后的 project/tools/deploy-emmc-root、静态mke2fs维护包到RAM tmpfs，逐项核验SHA。maintenance包内旧脚本有 ! grep 缺陷，必须使用本草案共享修正版。
3. 显式执行 `sh deploy-emmc-root /tmp/rootfs.tar.gz EXPECTED_SHA /tmp/maintenance`。脚本只格式化p1，解包/sync/卸载/只读重挂载逐文件核验，恢复主设备和分区只读；不写boot0/boot1/179。错误SHA和已挂载检测在解除只读或格式化前退出。
4. guard健康期限内主动reboot。v8从p1 /boot直接启动，无initrd。确认根rw、OpenRC、持续watchdog、模块/无线/显示/时间健康。
5. 回退BusyBox用相同RAM流程重写p1为核验过的自洽BusyBox tar。当前23模块对齐备选SHA `16733c41230b910e4f4b4ead7b8eb50024f2779df042fcce66dfc75752070264`；原K历史21模块包仍为自洽备选，不是当前设备完整备份。回退流程尚未实际演练。
6. 下键+复位→ROM→USB barebox→RAM用于人工救援；boot1可从完整v7备份恢复并核验全区/只读。179=0x48仅选择boot0，不恢复已替换p1；原厂系统还需原厂根备份。不得把启动选择当完整回退。

后续为长期稳定性、第二台K4和发布前用户许可审阅。不得从本配方复现推定新的设备验收。
