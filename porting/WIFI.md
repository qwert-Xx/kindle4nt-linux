# Kindle K4 / Yoshi SDIO Wi-Fi 移植记录

## 2026-09-27 更新：nl80211 与签名监管数据库

wpa_supplicant 2.12（只编译 nl80211）、wpa_cli、iw 6.17 已在 6.6
RAM 启动通过 WPA2-PSK/CCMP 关联、DHCP 续租/客户端重建、s2idle 后
联网和网关通信。wireless-regdb 2026.09.03 的证书与内核内置证书一致，
内容签名校验及实机 `iw reg reload` 通过，未禁用签名检查。
四组 ping 共 8/8，USB 正常、eMMC 只读哈希一致，随后恢复旧内核。
构建脚本、哈希、实测记录与功能限制见 `WIFI-USERSPACE.md`。
下方 WEXT 和缺失 regulatory.db 描述是历史测试状态。

## 2026-09-27 更新：常驻网络的 CUTPOWER 恢复已修复

追踪确认旧 `WMI_READY` 在停止硬件后仍为 1，放行 cfg80211 后台删除
密钥命令并污染已重置的 HTC endpoint，同时恢复可能跳过等待新固件。
已在停止 IRQ/异步 I/O 后清除此标志，并让 SDIO resume 传递真实错误。
修复后追踪开启与独立追踪关闭两轮均完整通过租约/客户端重建/s2idle
恢复/网关通信/eMMC 只读哈希联合测试，详见 `WIFI-PM.md`。下节故障
记录保留为修复前证据；长期租约和冷启动仍不在本次验收范围内。

## 2026-09-27 常驻 DHCP 与新发现的恢复故障

`wifi-connect` 新增持有 flock 的单实例服务，管理前台 supplicant 与
udhcpc 子进程。DHCP 使用 `-f -R -t 4 -T 3 -A 5`，取消 `-q/-n`，
保留租约计时与重试；子进程退出会重建。`start` 幂等，`--resume`
请求现有 DHCP 客户端重新确认租约并等待新的 ready 标记。carrier
下降时撤销 readiness，保留尚未失效的租约；carrier 回升时发送 USR1。
真正的 deconfig/NAK 清除 wlan0 地址、该接口默认路由和私有 resolver；
bound/renew 更新地址、替换该接口默认路由、全部 DNS 和租约序列号。
不会删除 USB 接口的连接路由。服务与子进程的日志/状态只在 RAM。

信号语义和 pidfile 创建顺序核对了 BusyBox 1.31 分支
[dhcpc.c](https://raw.githubusercontent.com/mirror/busybox/1_31_stable/networking/udhcp/dhcpc.c)，
并与本机 1.31.1 的 `udhcpc --help` 对照。fd 9 不传给长驻子进程。
服务本身被 SIGKILL 后的孤儿接管、自然 43200 秒租期到期、DHCP 服务
失联、长时间运行与无线环境变化尚未验证。

两轮 RAM 中已通过：自动连接、同一 DHCP PID 续租（序列 1→2）、
重复 start 不创建新服务/客户端、主动结束 DHCP 子进程后自动重建
（序列 3），上述各阶段网关 ping 均 2/2，默认路由只有一条。
第二轮 service=81、wpa=90、DHCP=92→293。未改变充电控制权。

**联合休眠测试未通过，不能将现有服务作为已验收的完整恢复方案。**
两轮都由 SRTC 唤醒 s2idle，但 wlan0 没恢复 carrier，`--resume` 超时。
首轮曾在 link-down 发送 USR2 释放租约，第二轮删除这一动作后仍失败，
因此不能认定 DHCP release 是根因。第二轮明确记录：

```text
36.831047 wiphy_suspend begins
36.836094 wiphy_suspend returned 0
36.836511 ath6kl: wmi ctrl ep is full
36.836735 ath6kl: req failed (status:-84, ep:1, len:7 creds:1)
36.836764 ath6kl: tx complete error: -84
51.508028 ath6kl: temporary war to avoid sdio crc error
51.762524 wiphy_resume returned 0
54.639373 PM: suspend exit
```

首轮 supplicant 后续不断报告 `SIOCSIWSCAN: Device or resource busy`。
当前证据指向需要检查的 ath6kl CUTPOWER / 异步 WMI/SDIO 清理路径；
还不能断言队列满、-EILSEQ 与重连失败的因果关系。上游
`ath6kl_sdio_resume()` 忽略 `ath6kl_cfg80211_resume()` 返回值，也需核查，
不能仅凭 PM success 计数宣称无线恢复。之前低频 DVFS 联合测试曾通过；
本轮在默认 800 MHz 下，频率、负载/时序及用户态差异尚未隔离。

第二轮 s2idle 17.873 秒、RTC_AF/RTC_IRQF=1；USB SSH 可用。eMMC ro=1，
偏移 0 和 16 MiB 各 1 MiB 哈希都与基线一致。首轮未在复位前取得新增
哈希，不宣称首轮哈希验收。两轮均看门狗恢复旧 2.6.31、kexec_loaded=0。
日志在 `<build>/wifi-lease-suite.log`、`wifi-lease-v2-suite.log`、
`wifi-lease-v2-debug.log` 和 `wifi-lease-v2-final.log`。

镜像 SHA-256：

- zImage：`d4260283293a827a31717a84c965ef815533cb1744dede90604e85f2d09a37f2`
- charge-240 DTB：`543f670e6244bc2a139f9327600bab6f8335fe9c8fc3de628e97b12954109d9b`
- 第一轮私有 initramfs：`c76783aefc360d7511d3c469e5f8aac21b5211ac935e3fe872d2a4b822f96f5f`
- 第二轮私有 initramfs：`9c402f81c83380e1022d50451b63f62d9673fab7a64302e9193a4dfc484920e1`

下一步优先复现并修复这一联合恢复故障，增加针对异步队列和恢复错误的
诊断；不依赖重启掩盖失败。下方 -q 描述为早期镜像历史。

## 2026-09-27 自动联网、DVFS 与 s2idle 联合验证

新增 `porting/initramfs/wifi-connect`：仅在私有镜像包含本机无线配置时，由复合 USB init 在后台启动。使用已有静态 wpa_supplicant 2.10/WEXT，等待 carrier，申请 DHCP，成功后生成 RAM readiness 标记。`--resume` 复用已有 supplicant 进程，等待连接恢复并重新申请 DHCP，不启动重复进程。PID、配置和 supplicant 日志权限为 0600，配置和固件始终位于仓库外或设备 RAM。

现有静态 supplicant 没编译 `-f` 文件日志选项，最初镜像因该参数打印 usage。首轮在 RAM 内修正后完成了联合测试，但不把它算成自动联网启动通过。最终脚本使用前台 supplicant 作为后台子进程，并由 shell 重定向日志，避免 `-B` daemonize 后关闭日志输出。配置内容和完整无线日志不输出到聊天或 Git。

最终完整镜像验证：

| 产物 | SHA-256 |
| --- | --- |
| zImage | `d2a83615d439e66f0a1c4cfb9ca4593ef7dbe1ff8845e2442963989fb2cafb28` |
| imx50-kindle-k4-dvfs-probe.dtb | `14b9dfd688fb5d8a2880a8a7b23cc5ef81a3b137762dce62761cfd5319db978c` |
| k4-wifi-dvfs-s2idle-final-initramfs.cpio.gz | `8808494fcdc0f6a0375ac09112974734d98e20c54481f44f5d4713fcb412d40e` |

本地镜像和设备 `/tmp` 镜像均为 0600，上传哈希一致。6.6 从 RAM 启动后无需手动启动 supplicant，即自动关联并获得 `192.0.2.129/24`、租期 43200 秒和网关 `192.0.2.1`。随后从 USB SSH 后台运行 `pm-wifi-dvfs-probe`：

| 阶段 | CPU / SW1 | 对网关 ping |
| --- | --- | --- |
| 初始关联 | 800 MHz / 1.05 V | 3/3 |
| 降频降压 | 160 MHz / 0.85 V | 3/3 |
| 该低频状态进入 s2idle，SRTC 唤醒后 | 160 MHz / 0.85 V | DHCP 后 3/3 |
| 回到高频 | 800 MHz / 1.05 V | 3/3 |

每次都核验 PLL1 仍为 800 MHz，最终打印 `K4_WIFI_DVFS_S2IDLE_PASS`。RTC 15 秒闹钟的 suspend syscall 总历时 18.004 秒，返回 RTC_AF/RTC_IRQF，pm_wakeup_irq=40，success=1/fail=0，随后关闭闹钟。supplicant 事件序列含初始 CONNECTED、休眠时 DISCONNECTED、恢复后的 CONNECTED；还出现额外 CONNECTED 报告，因此不把消息数量当作精确关联次数，也不据此宣称长期稳定。唤醒后的 DHCP 和实际网关通信提供连接恢复证据。

最终 eMMC ro=1，两个原始 1 MiB 取样哈希仍为 `c6f7f713bb57aad2203df61ffc348103848e41dea9451ae4b86c98ddd6862265` 和 `4613632586282e084c1e148d63be1ee6d800f14d6691e9dc1d5628d3921e5a18`，USB SSH/UDC 正常。脚本退出时将 CPU 留在 800 MHz/1.05 V，失败路径也尝试恢复这一档位。两轮均由看门狗恢复旧 2.6.31，`kexec_loaded=0`，日志 `reset=watchdog` 和 `K4_PM_S2IDLE_RETURN rc=0`。原始结果保存在仓库外 `build-k4-v6.6.157/wifi-dvfs-s2idle-final.log`。

这是既有固件和 WEXT 用户态下的短时联合验证。DHCP 使用 -q 取得租约后退出，本测试脚本不承担长期租约续期服务；长时间断线重连、吞吐/丢包边界、现代 nl80211 用户态、监管域、真实冷启动和深度休眠仍需处理。

2026-09-25 在 Linux 6.6.157 的 RAM 启动中依次验证 ESDHC2、Wi-Fi 电源 GPIO、上游 `ath6kl_sdio`、固件加载、关联和局域网通信。所有镜像经旧内核 kexec 从 RAM 装载，eMMC 用户区保持只读。

## 旧板级依据

- `mx50_yoshi.c` 的 `mmc2_data`：ESDHC2、4 位总线、SDIO IRQ、SD 高速模式、最高 50 MHz。旧内核将无线模块枚举为高速度 SDIO 卡，使用旧 `ar6k_wlan` 驱动。
- `mx50_yoshi_gpio.c` 为 SD2 CMD、CLK、D0–D3 配置 pad；CMD、CLK 置 SION。Wi-Fi 电源由 SD3_WP 对应的 GPIO5_28 输出高电平，旧代码延时 40 ms；冷启动的电源控制尚未迁入设备树。
- 旧根文件系统的 AR6003 hw2.1.1 固件位于 `/opt/ar6k/target/AR6003/hw2.1.1/bin`。6.6 内核含 `ath6kl_sdio` 对 Atheros `0x0271:0x0301` 的设备 ID 表项，所需固件命名与旧系统不同；仍需逐项核对映射和板级校准数据。不要把旧固件文件直接提交到内核仓库。

## 首次 RAM 启动结果

`imx50-kindle-k4-sdio-id.dts` 继承已验证的 PMIC、USB、eMMC 探针设备树，启用 ESDHC2 和旧板级 SD2 引脚设置。zImage SHA-256 `67ef9a6d587e449c9740a001d4c8d69bfc6e8d1d05d305a0382eb90a7a2fb8b4`，DTB `fa5abd6d10e1737fe37377255eb19cf69d3e8a4ea59d0d62abfb0bf12d720369`，initramfs `5f1208f70cdfbff3cd3935349740ad0205dc5bdd97b3ecf977eb3365eee342d2`；设备端上传哈希与本地一致。

COM9 日志显示 `50008000.mmc` 为 `mmc1`，约 1.54 秒识别为高速 SDIO 卡。`/sys/bus/sdio/devices/mmc1:0001:1` 的 vendor 为 `0x0271`、device 为 `0x0301`、modalias 为 `sdio:c00v0271d0301`。同轮 eMMC 仍识别 SEM02G 并自动设为只读，USB UDC 为 `configured`。看门狗随后恢复旧 `2.6.31-rt11-lab126`，`kexec_loaded=0`，旧日志含 `reset=watchdog` 和 eMMC 只读 RAM 标记。

## 电源 GPIO 与驱动

`imx50-kindle-k4-sdio-power.dts` 将旧板级的 SD3_WP 复用为 GPIO5_28，保留开漏与上拉的 pad 设置，以 GPIO hog 输出高电平，并给 ESDHC2 增加 40 ms 上电等待。DTB SHA-256 `c9d1f39850fd5e61cfd24334bedab29d4c0f97aaac2e90ce1ad6d56c2bd2b632`。COM9 的 debugfs 显示 `gpio-156 ... k4-wifi-power ... out hi`，SDIO 卡身份保持 `0x0271:0x0301`，eMMC `ro=1`、UDC `configured`。本轮也由看门狗恢复旧系统。此证据仍不能证明从完全断电状态由新内核首次上电。

`porting/k4-wifi.config` 启用上游内建 `ATH6KL` 和 `ATH6KL_SDIO`。构建得到的 zImage SHA-256 为 `ef780358e8028c868d370980efd1dc0660caf54c93aa62e98a98d68dcb234168`。`prepare-wifi-firmware.sh` 从旧 RAM 根文件系统归档提取设备自身的四份固件，放在仓库外的构建目录，再由 `K4_WIFI_FIRMWARE_DIR` 可选地纳入诊断 initramfs：

| 旧文件 | 6.6 固件文件 | 字节数 |
| --- | --- | ---: |
| `otp.bin` | `otp.bin` | 2977 |
| `athwlan.bin` | `athwlan.bin` | 53236 |
| `data.patch.hw3_0.bin` | `data.patch.bin` | 140 |
| `AR6103_QCA_15dBm_08032011.bin`（旧 `active_calibration` 指向它） | `bdata.bin` | 1792 |

固件文件不进入 Git；板级校准只取自本机备份，不用通用 `bdata.SD31.bin` 代替。设备端上传哈希与构建产物一致。6.6 首先尝试不存在的 `fw-5.bin` 至 `fw-2.bin`，然后回退到 API 1 四文件路径；dmesg 明确显示 `ath6kl: ar6003 hw 2.1.1 sdio fw 3.1.87.30 api 1`。`wlan0` 出现且 `ifconfig wlan0 up` 成功，USB UDC 仍为 `configured`，eMMC `ro=1`。驱动报告旧固件缺少 RSN-CAP-OVERRIDE，因此禁用 802.11n HT；`regulatory.db` 未随本轮最小 initramfs 提供，后续需处理监管域。

## 局域网验证

下一轮将此前构建的静态 `wpa_supplicant` 2.10 和已有的无线配置从旧测试归档仅放进仓库外的私有 initramfs（SHA-256 `d2c5ca6131f05331a51ba3259c4272863fa12a88bed0a7629f0465d89fb82681`）。该程序使用 WEXT 接口；首次因 initramfs 缺少 `/var/run/wpa_supplicant` 目录未启动，建立目录后成功运行。诊断脚本现已在可选包含无线配置时创建此目录，并将含配置的本地 initramfs 设为 `0600`；上传脚本也将设备 `/tmp` 的 initramfs 设为 `0600`。

`wlan0` 随后显示 `UP BROADCAST RUNNING`，收到 IPv6 地址与网络包，`/sys/class/net/wlan0/carrier=1`。临时将接口设为原测试网段的 `192.0.2.112/24`，对局域网网关 `192.0.2.1` 连续 3 次 ping 全部成功，0% 丢包。该静态地址仅用于一次 RAM 测试。该轮结束后设备恢复旧 `2.6.31-rt11-lab126`，`kexec_loaded=0`，旧日志含 `reset=watchdog` 和 eMMC 只读标记；含无线配置的 `/tmp` initramfs 已随重启消失。

再加入只在私有无线 initramfs 中使用的 `udhcpc-wifi` 脚本，自动设置 DHCP 租约、默认路由和 DNS。新 initramfs SHA-256 `00adba00653b60c2a5243a4e80cf8b88b5d01ac7491092578f095ad6733cbadb`，设备端哈希一致，设备 `/tmp` 文件权限为 `0600`。同一 6.6 zImage/DTB 下，`wpa_supplicant` 关联后 BusyBox `udhcpc` 获得 `192.0.2.129/24`、43200 秒租约和 `192.0.2.1` 默认路由；对网关 3 次 ping 全部成功。COM9 同时确认 eMMC `ro=1`、UDC `configured`。本轮由看门狗恢复旧 `2.6.31-rt11-lab126`，`kexec_loaded=0`。重新关联、吞吐、长期稳定性以及重启后的自动联网尚未验证。

## 下一步

1. 把 GPIO hog 演进为有明确供电来源的模型；确认从断电冷启动时能给卡上电。
2. 在新的用户空间实现自动连接与断线恢复；核对本机固件的监管域和实际支持的 Wi-Fi 功能。
3. 验证休眠唤醒、长期传输和与 PMIC 供电关系。当前的实际通信证据只覆盖旧内核已上电后经 kexec 切入 6.6 的场景。

## 2026-09-25 MMC 电源时序探针

原先 `imx50-kindle-k4-sdio-power.dts` 把 GPIO5_28 注册为始终输出高电平的 GPIO hog，这能保持旧内核已打开的无线模块，但不能描述由 MMC 主机控制的上电顺序。新增独立 `imx50-kindle-k4-wifi-pwrseq-probe.dts`：仅在此 RAM 探针里移除 hog，给 ESDHC2 指向 `mmc-pwrseq-simple`，把 GPIO5_28 声明为低有效 reset，并在释放后等待 40 ms。旧板级代码输出高电平使能 Wi-Fi，因此低有效 reset 与其电平语义一致。没有修改原有稳定探针。

使用 zImage SHA-256 `56b112054fd8cf5def98b1eb3ad661ad7fa10be91945f19371830f722832f4ac`、新 DTB `b64cb14a0373e257694d600738fdac233387178e3d9bf7c799380a08cafbd0cc`、不含无线固件的复合 USB SSH initramfs `81e33592342dbe36c35ec0a2bf673948e8ab49ae997d4b70d028d97082944632`，设备端哈希匹配。6.6 日志显示 `50008000.mmc: allocated mmc-pwrseq`、随后 `mmc1: new high speed SDIO card`；设备 ID 仍为 `0x0271:0x0301`。debugfs 的 GPIO156 显示 `reset ... out hi ACTIVE LOW`，不再是 hog。缺少本机 `bdata.bin` 时 `ath6kl` 按预期返回 `-2`，这轮不用于判断固件路径。eMMC `ro=1`、USB SSH 正常。

第二轮把本机已有的 AR6003 固件仅放入仓库外私有 initramfs，SHA-256 `0266e15fa7216aa9c1c1c72e97ce3f45c97cb1947e7d0bc1e588fabc2d9a5bd0`；zImage/DTB 不变，上传端哈希匹配。6.6 再次分配 `mmc-pwrseq`，`ath6kl` 报 `ar6003 hw 2.1.1 sdio fw 3.1.87.30 api 1`，`wlan0` 出现且 `ifconfig wlan0 up` 成功。GPIO156 仍由 reset 时序驱动保持高电平；UDC `configured`、eMMC `ro=1`。看门狗随后恢复旧 `2.6.31-rt11-lab126`、`kexec_loaded=0`，旧日志保留 6.6 SSH 与串口就绪标记。该镜像未包含无线连接配置，没有测试关联和 DHCP；此前基于 GPIO hog 的独立探针已通过这两项。GPIO 最终电平和重新枚举可以证明时序驱动接管并能启动卡，仍不能单凭软件日志证明完全断电冷启动的供电电压、低电平脉宽或休眠恢复。
