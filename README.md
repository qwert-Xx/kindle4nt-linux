<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Kindle 4 NT D01100

Local public-history draft, not a hardware-accepted release. Read [scope and status](project/docs/README.md), [build](project/docs/BUILD.md), [RAM recovery](project/docs/RAM-BOOT.md), [ZQ](project/docs/ZQCAL.md) and [known issues](project/docs/KNOWN-ISSUES.md). Apply kernel/patches/series to separate Linux v6.6.157 sources; debug additionally applies kernel/debug-patches/series. No device operation or deployment is automatic. Firmware/waveforms/credentials and raw evidence are excluded.

boot1主题见 [barebox boot1](project/docs/BAREBOX-BOOT1.md)。

## 当前状态（2026-10-03，既有实机记录）

boot1 barebox v8，EXT_CSD[179]=0x50，默认 eMMC p1 Alpine 3.24.2；BusyBox 根作为维护/备选。
USB 串口发送 Ctrl-C（0x03）中断 boot/emmc 的 sleep 5 进入 shell，再 YMODEM 加载方案 A RAM 维护包（k4-maint-ram-20261003，900/30 expire-health）；不要复位前按上。5秒从脚本运行计起，Windows枚举可能缩短实际主机窗口，窗口末尾和电池独立冷启动待验。
WDI 原厂方案 A 为 ALT2/0x0c，正常态由 restart pinctrl 持有。Alpine 正常根持续 watchdog 喂狗，无有限 RAM guard；静态 2.12 supplicant 由本地 @k4 APK 提供。
Alpine 首次启动与3轮正常 reboot、两档 RTC STOP/内存保持/醒后刷新、NTP/SRTC正常关机读写和 HTTPS apk update 已有实机记录；长期运行、upgrade、第二台 K4 与物理电源轨仍未验。详 [Alpine 配方](project/docs/ALPINE-ROOT.md) 与 [guard 对照](project/docs/RAM-GUARD-COMPARISON.md)。发布前需用户许可审阅。
本次只离线编辑、构建和扫描，未访问设备、未 push。默认根更新不意味着覆盖所有冷启动/耐久验收。
