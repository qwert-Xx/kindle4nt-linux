<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Kindle 4 NT Linux 移植（公共草稿）

范围仅 Kindle 4 无触摸屏 D01100 / Yoshi / LPDDR1，不支持其它 Kindle。基于 Linux v6.6.157，barebox 开发基线使用上游 ZQ PU=23/PD=8。此目录是公开导出项目的文档草稿，完整研究历史、原始日志和私有运行包不公开。

已有 production 冷联合验证包括 USB、Wi-Fi、显示、RTC、两档 STOP、16 MiB 内存保持、存储只读和板级返回。阶段4 panel flash / 五向键模块化及通用 coldplug 已离线构建，合并冷验仍待用户在场；不把旧阶段验收扩大到新候选包。正式恢复、充电、PM、时钟和 USB 基础驱动保持内建。

当前以 ROM 下载到 RAM 验证，不提供已验收的持久安装流程。错误镜像、电源中断、看门狗或 DDR 参数可能导致无 USB、卡住或需要人工恢复。即使只读检查通过也应先保留本人原厂备份，设备需有足够电量且人在旁。

阅读 [构建](BUILD.md)、[RAM 启动与恢复](RAM-BOOT.md)、[zqcal](ZQCAL.md)、[限制](KNOWN-ISSUES.md)。不提供固件、波形、校准数据、Wi-Fi 凭据、SSH 私钥或设备身份信息；从本人合法拥有的原厂只读备份在项目外提供。

Linux/barebox 改动按对应 GPL-2.0 许可与原文件 SPDX；原创工具 GPL-2.0-or-later；原创文档 CC-BY-4.0。第三方组件各自许可独立，见 [用户态配方](../userspace/README.md)。公开发布前仍须阶段7许可、schema及隐私审查。
