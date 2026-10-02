<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Kindle 4 NT D01100

Local public-history draft, not a hardware-accepted release. Read [scope and status](project/docs/README.md), [build](project/docs/BUILD.md), [RAM recovery](project/docs/RAM-BOOT.md), [ZQ](project/docs/ZQCAL.md) and [known issues](project/docs/KNOWN-ISSUES.md). Apply kernel/patches/series to separate Linux v6.6.157 sources; debug additionally applies kernel/debug-patches/series. No device operation or deployment is automatic. Firmware/waveforms/credentials and raw evidence are excluded.

boot1主题见 [barebox boot1](project/docs/BAREBOX-BOOT1.md)。

## 当前状态（2026-10-03，既有实机记录）

boot1 barebox v7 + eMMC p1 ext4 BusyBox 根已部署并读回核验，EXT_CSD[179]=0x50；无需电脑上传内核即可自动启动。按住“上”在两秒采样窗口进入 USB/YMODEM 主机加载；按住“下”配合复位进入 ROM 恢复。ath6kl_core/sdio 为模块，根挂载后由标准 modalias coldplug 加载固件；WDI 原厂方案 A 为 ALT2/0x0c，正常态由 restart pinctrl 持有。

正式 A 的 10 轮 reboot 健康检查全部通过（25.812–26.578 秒到 SSH），800/160MHz 两次 RTC STOP、16MiB 内存保持、4MiB 文件 sync 后 reboot 哈希保持均通过。看门狗停喂方案 A 48.047 秒、旧 DTB 对照 41.156 秒均自行经 v7 回 eMMC；旧对照未复现 ROM，不能认定 A 已唯一修复历史故障。两次采集总长各180秒，停喂后有效窗口仅167/171秒。

USB 物理拔线/电池独立冷启动、长时耐久及电源轨仍未验证；RAM 维护 guard 到期掉 ROM 的历史根因未定。新版模块 RAM 维护根尚未重新实机验证。Alpine feat/alpine-root 仅列路线图，未实机验证，未纳入本草案正式内容。

构建与部署见 [eMMC 根](project/docs/EMMC-ROOT.md) 与 [barebox v7](project/docs/BAREBOX-BOOT1.md)。上述是既有实机结果整理，本次仅离线编辑与构建，不操作设备。

离线补丁构建与隐私/许可检查见 [复现记录](project/docs/REPRO-20261003.md)。
