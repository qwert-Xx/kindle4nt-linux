<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# kindle4nt-linux

为 Kindle 4 非触屏 D01100（Yoshi / Tequila）提供 Linux 6.6.157、barebox 与 Alpine 根系统的源码、补丁和构建配方。

[English](README.md)。作者 qwert-Xx。本项目非官方，与 Amazon、Lab126、NXP/Freescale 及上游项目无隶属或背书关系；Kindle 等名称及商标归各自权利人所有。

**改写 eMMC boot1 或 p1 会破坏数据，可能变砖或失去保修。** 先准备完整、已核验的备份和恢复路径。按住 **“下”键并复位**进入 i.MX ROM 下载模式，再加载 USB barebox 和 Linux RAM 维护系统。不要把短暂的 Ctrl-C 窗口当作唯一恢复入口；把 EXT_CSD[179] 改回原值不会恢复已覆盖的 p1。

## 当前状态

仅支持 **D01100**，主要依据单台设备记录，尚无多机型或多台设备广泛验证。此次整理仅运行主机工具，不增加实机验收结论。

| 项目 | 既有验证 | 未验证与已知问题 |
| --- | --- | --- |
| 启动与存储 | boot1 barebox v8、179=0x50、p1 Alpine 3.24.2 自动启动及三轮正常 reboot | 电池独立冷启动、第二台设备、耐久与完整回退演练 |
| 显示与待机 | 首次刷新、两档 CPU 的 RTC STOP、内存保持及醒后刷新 | 实体电源轨/功耗、长时及大量循环 |
| 网络与时间 | WPA2-PSK/CCMP、DHCP、USB 串口/SSH、NTP、正常关机 SRTC 回写与 HTTPS apk update | 其他无线模式、实体拔插、apk upgrade |
| 恢复 | 下键/复位 ROM 与 RAM 维护路径、v8 串口 Ctrl-C | 五秒窗口末尾和主机枚举时序；历史 RAM guard 到 ROM 根因未定 |
| 公开构建 | [本轮主机结果](project/docs/RELEASE-VALIDATION.md) | 用户自己的私有输入会改变根 tar 哈希，不等于新增硬件验收 |


Alpine 使用官方 OpenSSH 10.3_p1-r1 与标准 sshd OpenRC 服务，22 端口、所有 IPv4/IPv6 地址监听，仅 root 公钥认证，启用 internal-sftp。USB 地址 169.254.212.2 和 Wi-Fi 均可连接；USB gadget 仍在 k4-platform，ttyGS0 root shell 保留。RAM 维护根保持 Dropbear/2222。Alpine 不再包含 Dropbear 包、k4-usb-ssh 或 k4-userspace-service。

主机密钥用构建参数 `--ssh-host-key /absolute/ssh_host_ecdsa_key` 提供仓库外 OpenSSH 格式 ECDSA 私钥（600），公钥自动派生（644）；沿用既有身份。未提供时，官方 sshd 首次启动按 `key_types_to_generate="ecdsa"` 生成，不在构建时随机生成。`--authorized-keys /absolute/authorized_keys` 提供 root 公钥授权（600），也可沿用外部 K4 根的 root/.ssh/authorized_keys。私钥和凭据不入库。Alpine 连接：`ssh root@169.254.212.2`；RAM 维护：`ssh -p 2222 root@169.254.212.2`。



## 准备

参考主机为 Ubuntu 24.04、Python 3.12、ARM hard-float GCC 13.3 / binutils 2.42。准备 make、主机编译工具、flex、bison、bc、libssl-dev、pkg-config、patch、tar、xz、curl、GnuPG、openssl、kmod 与 ARM 交叉编译器。维护 BusyBox 使用清单锁定的旧 Linaro 工具链。使用普通用户；本轮验证使用 kindle 用户（UID 1000）。详见[源码输入](sources/README.md)和[构建说明](project/docs/BUILD.md)。

缓存、构建输出和私有输入均置于仓库外。按照 [THIRD-PARTY.md](THIRD-PARTY.md) 从自有设备/备份提取 AR6003 固件/校准、面板波形及 boot0/idme；无线配置、SSH 授权与主机身份另行提供。仓库不发布任何镜像、APK、根 tar、凭据、私钥或专有固件。

## Alpine 标准网络

启用官方wpa_supplicant 2.11-r4、wpa_cli、networking与ifupdown-ng；WPACLI_OPTS使用Alpine默认wpa_cli.sh，在连接变化时通知DHCP。wlan0 DHCP、usb0静态169.254.212.2/16，conf.d依赖K4 coldplug。外置device-inputs/etc/wpa_supplicant.conf写入根默认子目录/etc/wpa_supplicant/wpa_supplicant.conf（600），凭据不入Git。仅Alpine删除K4 Wi-Fi supervisor，BusyBox维护根保持。[配置、既有设备验证和离线比对](project/docs/ALPINE-STANDARD-NETWORK-OFFLINE-20261003.md)。

## 快速开始

一条主机构建命令：下载清单输入、校验哈希与 Linux 签名、应用补丁，构建 Linux、barebox、用户态、官方签名 WPA APK 与 Alpine 根：

```sh
python3 project/release.py --cache /external/source-cache --out /external/new-build --private-inputs /external/device-inputs
```

已有核验缓存时增加 `--offline`。Wi-Fi 使用官方main 2.11-r4，无需用户签名密钥。冻结 Alpine 索引可能已被镜像更新；应保留核验缓存，不静默换版本。

部署必须另行手动操作：Ctrl-C 或下键复位进入 ROM → USB barebox → RAM 维护 → 完整备份并核验 → 写入/读回核验 boot1 与 p1 → 激活并重启。先完整阅读 [boot1](project/docs/BAREBOX-BOOT1.md) 与 [Alpine 部署](project/docs/ALPINE-ROOT.md)，绝不能格式化当前正在运行的 p1。构建命令不部署。

## 维护、恢复与许可

正常 Alpine 根持续喂看门狗；RAM 维护使用有限 guard。内核、DTB、模块必须匹配，并保存已知可用 RAM 救援包。下键复位进入 ROM 后，可在 RAM 中恢复自己的完整 boot1/p1 备份；单独选择 boot0 不等于恢复原厂系统。见[已知问题](project/docs/KNOWN-ISSUES.md)与 [RAM 恢复](project/docs/RAM-BOOT.md)。

内核/barebox 补丁及派生代码 GPL-2.0-only；原创脚本/工具 GPL-2.0-or-later；文档 CC-BY-4.0。上游文件原作者通知及逐文件许可表达式仍有效。[LICENSES](LICENSES) 提供全文，[版权出处表](COPYRIGHT-PROVENANCE.md)和[第三方清单](THIRD-PARTY.md)记录逐文件依据；版权分类已由项目所有者审阅批准，无待确认项。

感谢 Linux、barebox、Alpine、BusyBox 和其他上游维护者，以及 Amazon/Lab126/Freescale 原厂开源代码作者。本仓库只分发源码、补丁、配方和构建脚本，正式发布仍待用户审阅。
