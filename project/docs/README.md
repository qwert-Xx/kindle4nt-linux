<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Kindle 4 NT Linux 移植（公共草稿）

范围仅 Kindle 4 无触摸屏 D01100 / Yoshi / LPDDR1，不支持其它 Kindle。基于 Linux v6.6.157，barebox 开发基线使用上游 ZQ PU=23/PD=8。此目录是公开导出项目的文档草稿，完整研究历史、原始日志和私有运行包不公开。

已有 production 冷联合验证包括 USB、Wi-Fi、显示、RTC、两档 STOP、16 MiB 内存保持、存储只读和板级返回。阶段4 panel flash / 五向键模块化及通用 coldplug 已离线构建，合并冷验仍待用户在场；不把旧阶段验收扩大到新候选包。正式恢复、充电、PM、时钟和 USB 基础驱动保持内建。

当前以 ROM 下载到 RAM 验证，不提供已验收的持久安装流程。错误镜像、电源中断、看门狗或 DDR 参数可能导致无 USB、卡住或需要人工恢复。即使只读检查通过也应先保留本人原厂备份，设备需有足够电量且人在旁。

阅读 [构建](BUILD.md)、[RAM 启动与恢复](RAM-BOOT.md)、[zqcal](ZQCAL.md)、[限制](KNOWN-ISSUES.md)。不提供固件、波形、校准数据、Wi-Fi 凭据、SSH 私钥或设备身份信息；从本人合法拥有的原厂只读备份在项目外提供。

Linux/barebox 改动按对应 GPL-2.0 许可与原文件 SPDX；原创工具 GPL-2.0-or-later；原创文档 CC-BY-4.0。第三方组件各自许可独立，见 [用户态配方](../userspace/README.md)。公开发布前仍须阶段7许可、schema及隐私审查。

## 当前状态（2026-10-03，既有实机记录）

boot1 barebox v8，EXT_CSD[179]=0x50，默认 eMMC p1 Alpine 3.24.2；BusyBox 根作为维护/备选。
USB 串口发送 Ctrl-C（0x03）中断 boot/emmc 的 sleep 5 进入 shell，再 YMODEM 加载方案 A RAM 维护包（k4-maint-ram-20261003，900/30 expire-health）；不要复位前按上。5秒从脚本运行计起，Windows枚举可能缩短实际主机窗口，窗口末尾和电池独立冷启动待验。
WDI 原厂方案 A 为 ALT2/0x0c，正常态由 restart pinctrl 持有。Alpine 正常根持续 watchdog 喂狗，无有限 RAM guard；静态 2.12 supplicant 由本地 @k4 APK 提供。
Alpine 首次启动与3轮正常 reboot、两档 RTC STOP/内存保持/醒后刷新、NTP/SRTC正常关机读写和 HTTPS apk update 已有实机记录；长期运行、upgrade、第二台 K4 与物理电源轨仍未验。详 [Alpine 配方](ALPINE-ROOT.md) 与 [guard 对照](RAM-GUARD-COMPARISON.md)。发布前需用户许可审阅。
本次只离线编辑、构建和扫描，未访问设备、未 push。默认根更新不意味着覆盖所有冷启动/耐久验收。
