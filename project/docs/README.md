<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Kindle 4 NT Linux 移植（公共草稿）

范围仅 Kindle 4 无触摸屏 D01100 / Yoshi / LPDDR1，不支持其它 Kindle。基于 Linux v6.6.157，barebox 开发基线使用上游 ZQ PU=23/PD=8。此目录是公开导出项目的文档草稿，完整研究历史、原始日志和私有运行包不公开。

已有 production 冷联合验证包括 USB、Wi-Fi、显示、RTC、两档 STOP、16 MiB 内存保持、存储只读和板级返回。阶段4 panel flash / 五向键模块化及通用 coldplug 已离线构建，合并冷验仍待用户在场；不把旧阶段验收扩大到新候选包。正式恢复、充电、PM、时钟和 USB 基础驱动保持内建。

当前以 ROM 下载到 RAM 验证，不提供已验收的持久安装流程。错误镜像、电源中断、看门狗或 DDR 参数可能导致无 USB、卡住或需要人工恢复。即使只读检查通过也应先保留本人原厂备份，设备需有足够电量且人在旁。

阅读 [构建](BUILD.md)、[RAM 启动与恢复](RAM-BOOT.md)、[zqcal](ZQCAL.md)、[限制](KNOWN-ISSUES.md)。不提供固件、波形、校准数据、Wi-Fi 凭据、SSH 私钥或设备身份信息；从本人合法拥有的原厂只读备份在项目外提供。

Linux/barebox 改动按对应 GPL-2.0 许可与原文件 SPDX；原创工具 GPL-2.0-or-later；原创文档 CC-BY-4.0。第三方组件各自许可独立，见 [用户态配方](../userspace/README.md)。公开发布前仍须阶段7许可、schema及隐私审查。

## 当前状态（2026-10-03，既有实机记录）

boot1 barebox v7 + eMMC p1 ext4 BusyBox 根已部署并读回核验，EXT_CSD[179]=0x50；无需电脑上传内核即可自动启动。按住“上”在两秒采样窗口进入 USB/YMODEM 主机加载；按住“下”配合复位进入 ROM 恢复。ath6kl_core/sdio 为模块，根挂载后由标准 modalias coldplug 加载固件；WDI 原厂方案 A 为 ALT2/0x0c，正常态由 restart pinctrl 持有。

正式 A 的 10 轮 reboot 健康检查全部通过（25.812–26.578 秒到 SSH），800/160MHz 两次 RTC STOP、16MiB 内存保持、4MiB 文件 sync 后 reboot 哈希保持均通过。看门狗停喂方案 A 48.047 秒、旧 DTB 对照 41.156 秒均自行经 v7 回 eMMC；旧对照未复现 ROM，不能认定 A 已唯一修复历史故障。两次采集总长各180秒，停喂后有效窗口仅167/171秒。

USB 物理拔线/电池独立冷启动、长时耐久及电源轨仍未验证；RAM 维护 guard 到期掉 ROM 的历史根因未定。新版模块 RAM 维护根尚未重新实机验证。Alpine feat/alpine-root 仅列路线图，未实机验证，未纳入本草案正式内容。
