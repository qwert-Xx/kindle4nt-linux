<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# 当前用户态与维护根行为

硬件时钟、频率、分频、电源参数和设备树未由本文档整理或 applet 修复改变。当前默认 DTB 为 `nxp/imx/imx50-kindle-k4.dtb`。

| 项目 | 原厂/旧移植方式 | 当前实现 | 依据与验证范围 |
|---|---|---|---|
| 用户态 watchdog | 原厂专有服务；旧移植有限 guard/PM-health | Alpine 官方 OpenRC watchdog，维护 BusyBox 持续 watchdog，30 秒 timeout/10 秒喂狗 | `rootfs/alpine/etc/conf.d/watchdog`、维护 rcS；无自动回原厂期限 |
| 块设备访问 | 旧 RAM 试验 setro | 不自动 setro；部署显式指定分区 | 当前启动脚本及 deploy-emmc-root；部署仍会覆盖目标数据 |
| 维护命令安装 | 旧根只有部分 applet 链接 | 用同配置 BusyBox `busybox.links` 安装标准 applet 链接，常规 PATH | 主机清单与 396 个实际 applet 一致；产物新增 389 个链接及 3 个父目录，既有内容不变；cat/uname 主机模拟通过，设备 SSH 待运行新镜像 |

Applet 安装是现代用户态实现，不改变硬件参数或运行二进制。当前用法见[项目入口](../project/README.md)。以下保留各次硬件核对的参考内容，其中历史验证只适用于对应记录的配置。

## 2026-10-03 构建验收清理

删除 reproduce/verify-release、内核与用户态产物锁、参考二进制比较、固定构建时间和 ext3 复现元数据模式。验收使用归档结构、ARM ABI、模块 release 与用户态功能；保留下载输入 SHA256、签名校验和输入输出重叠检查。生效设备树仍为 `nxp/imx/imx50-kindle-k4.dtb`，硬件参数不变。主机验收通过：项目 30 测试、barebox 15 测试、波形 8 测试；默认三根、用户态与 barebox 源码构建成功；Alpine ABI/服务和维护 QEMU 功能检查通过。详见 [构建清理验收](../project/docs/CLEANUP-VALIDATION.md)。不包含设备、RAM/kexec 或冷启动验收。

## 2026-10-03 USB 标识清理

Alpine/eMMC、Alpine RAM 继承的 platform-start 和 BusyBox 维护 rcS 使用 serial/manufacturer `kindle4nt`，product `Kindle 4 Non-Touch`。USB 功能、VID/PID、地址和设备树不变；生效 DTB 为 `nxp/imx/imx50-kindle-k4.dtb`。检查启动脚本和三根归档中的描述符字符串；未连接设备，USB 枚举待硬件验收。

---

# 2026-10-03 Alpine OpenSSH 离线配方

Alpine 使用官方 OpenSSH 10.3_p1-r1 与标准 sshd OpenRC 服务，22 端口、所有 IPv4/IPv6 地址监听，仅 root 公钥认证，启用 internal-sftp。USB 地址 169.254.212.2 和 Wi-Fi 均可连接；USB gadget 仍在 k4-platform，ttyGS0 root shell 保留。RAM 维护根保持 Dropbear/2222。Alpine 不再包含 Dropbear 包、k4-usb-ssh 或 k4-userspace-service。

主机密钥用构建参数 `--ssh-host-key /absolute/ssh_host_ecdsa_key` 提供仓库外 OpenSSH 格式 ECDSA 私钥（600），公钥自动派生（644）；沿用既有身份。未提供时，官方 sshd 首次启动按 `key_types_to_generate="ecdsa"` 生成，不在构建时随机生成。`--authorized-keys /absolute/authorized_keys` 提供 root 公钥授权（600），也可沿用外部 K4 根的 root/.ssh/authorized_keys。私钥和凭据不入库。Alpine 连接：`ssh root@169.254.212.2`；RAM 维护：`ssh -p 2222 root@169.254.212.2`。

依据设备提交 5001e410a；硬件参数、生效方案A DTB、内核、barebox v8 与RAM维护包不变。离线验证见 ALPINE-OPENSSH-OFFLINE-20261003.md，本轮无设备操作。

<!-- SPDX-License-Identifier: CC-BY-4.0 -->
## 2026-10-03 标准网络用户态配方（离线）

原厂硬件参数无变化，生效方案A imx50-kindle-k4.dtb仍8960edb8…cdc、production内核5c666c72…291、barebox v8不变。依据7f106e6c3标准OpenRC/ifupdown-ng的五轮实机证据，将现代用户态接口写入Alpine配方，删除该根的K4 Wi-Fi消费者，不动BusyBox或驱动。77包验签、双根一致、19配置比对、host通过；新根未部署，自然租约T1/T2及长时未验。完整数据ALPINE-STANDARD-NETWORK-OFFLINE-20261003.md。

<!-- SPDX-License-Identifier: CC-BY-4.0 -->
## 2026-10-03 Wi-Fi用户态2.11（离线）

原厂硬件/时钟/供电参数未改；生效设备树仍为方案A imx50-kindle-k4.dtb。当前用户态从补丁2.12改为官方2.11，原因是2.12丢弃aborted结果而2.11无该分支，dc6989aa2五轮中止自动恢复、44挂起0失败。Alpine采用官方main 2.11-r4；BusyBox从原样上游2.11源码构建。删除扫描中止补丁，不新增重试策略。离线复现与检查见 WIFI-211-OFFLINE-20261003.md，新根包未上机，硬件参数无偏离。

## 2026-10-03 同ROM入口WDI对照新增验证（无硬件配置/部署变更）

正式方案A DTB/内核/boot1仍原值。第三轮仅RAM外部DTB换A、保持冻结kernel/root及ROM/YMODEM入口：ALT2/0xc自然guard close自动恢复，对照轮2 ALT1/0x84掉ROM。本次控制支持原厂ALT2/open-drain0xc恢复的效果；单轮30秒不能覆盖900秒/v5或全部历史原因。MMC卡/控制器runtime suspended为新增状态证据，ios逻辑on，不推断真实断电/sleep；第二轮runtime数据缺失，电气/故障后MMC寄存器仍缺。详细RAM-GUARD-ROM-THREE-ROUNDS-20261003.md，未应用策略修复、未新增永久限制。
## 2026-10-03 RAM 维护包同步原厂 WDI 方案 A（离线）

原厂正常态 WDI WDOG ALT2/pad 0x0c；旧冻结维护 DTB 未持有该正常态，冷入口可读 ALT1/0x84。
新维护包的正式 imx50-kindle-k4.dtb 含 46986d082，restart default/watchdog 使用同一 WDI pinctrl 组，reset GPIO态保留。
这次恢复原厂参数，不引入新的硬件偏离或临时策略；内核/DTB 与现有 eMMC 部署 SHA 相同。
主管报告的三轮对照表明 runtime-suspended eMMC 条件下 ALT1 的 SoC-only reset 回落 ROM，ALT2 经 PMIC 冷启动自动恢复（WRSR10）。
第二轮证据 69b5f4bd9；第三轮见第三轮提交 74ff1775e，合并时补号。
两个 clean 构建/host/guard/只读保护/coldplug/模块固件检查通过；新包未上机、电源轨未测、完整900秒退出待现场验证。
细节和逐文件 SHA 见 MAINT-RAM-PLANA-20261003.md，不覆盖第二轮报告当时的因果边界。

## 2026-10-03 RAM guard观察新增实机结论（无正式参数变更）

正式eMMC仍方案A ALT2/open-drain0x0c，DTB SHA8960edb8bdec2d216080b0f6dee682f38fd69b45f663062d539afc4a93bc0cdc，ath6kl=m/持续BusyBox watchdog，无部署变化。临时试验策略：冻结旧DTB/RAM根中的同一guard，由900缩短为30秒，保持timeout30/expire-health。kexec继承ALT2/0xc轮自动恢复；ROM冻结USB裸启动实读ALT1/0x84轮guard自然close后ROM，SRSR10，已取得边沿证据。并非原厂硬件参数新修改，也不表明A已唯一修复根因；入口/继承混杂、900秒/v5未完整重复、电源轨未测。未取得MMC控制器故障后寄存器，脚本地址错误已记录；v7上键入口异常待查。具体边界/时刻/恢复RAM-GUARD-ROM-COMPARISON-20261003.md。

## 2026-10-03 生效eMMC系统实测更新

生效DTB /boot/imx50-kindle-k4.dtb SHA8960edb8bdec2d216080b0f6dee682f38fd69b45f663062d539afc4a93bc0cdc。原厂WDI正常态WDOG ALT2/open-drain pad0x0c恢复，旧现代配置ALT1/0x84撤回；当前实读2/0xc，PC2 WDIRESET/RESTARTEN=1，WCR3b3d/30秒。restart保持单一pinctrl owner，default/watchdog同组，reset GPIO态保留，依据原厂源码见WDOG-STOCK-A-TEST-20261003.md。A停喂和旧对照都自行恢复，不能把参数恢复等同历史ROM问题已修复。未测电源轨。

ATH6KL/SDIO从=y改=m属于现代加载时序实现，硬件SDIO配置未改变；根挂载后常规modalias coldplug解决内建驱动过早取固件，不引入unbind/bind启动脚本或EXTRA_FIRMWARE。维护RAM离线模块/固件验证，eMMC自动启动WiFi已实测。原厂根改为BusyBox ext4 p1为系统策略，前32MiB/boot0/idme/fuse未写，boot1 v7与1790x50读回通过。10轮reboot、两档STOP、显示/网络/内存/存储验证通过；物理拔线冷启动、长期/电气验证仍缺。完整证据和限制EMMC-DEPLOY-STABILITY-20261003.md，优先于下文待验/因果推断历史。

## 2026-10-03 eMMC 根 Wi-Fi 模块修复（离线完成，实机更新待验）

初次 v7 自动启动 ext4 rw 根成功，内建 ath6kl 在 VFS 挂载根前请求固件失败。
用户要求改用常规模块：k4_defconfig 的 ATH6KL/ATH6KL_SDIO y→m；根挂载后
既有通用 modalias coldplug 加载 ath6kl_core/ath6kl_sdio，从 /lib/firmware 读取固件。
不改变 AR6003 时钟/SDIO/电源/时序或 DTB，不使用 SDIO unbind/bind 启动脚本，
EXTRA_FIRMWARE 为空。此前一次 bind 仅临时诊断，不在根中部署启动绕路。

production 完整 ARM/modpost、23 个模块安装、RAM 根构建通过；标准 SDIO alias
sdio:c00v0271d0301 解析到两个 ath6kl 模块，RAM ext3 内的 coldplug/modprobe、
AR6003 固件及 regulatory.db 存在，DTB 与冻结会话4逐字节相同。
4 coldplug tests + 1 emmc-root conversion test 通过，build warning/error 行0。
其他 profile 使用同一 k4_defconfig；本轮未重新构建 debug/lifecycle，不宣称其构建通过。

另修部署脚本挂载点 /mnt/emmc-root→/tmp/k4-emmc-root，适配维护根只读且无 /mnt；
设备 p1 部署已用仅此路径替换的交付脚本完成 mkfs、解包与只读文件读回，未改变写入范围。

待更新新内核/模块、正常 reboot、10轮及两档 STOP/文件持久性。原始日志仅本地，未push。

## 2026-10-03 夜间持久根部署未开始：USB恢复失败

冻结会话4USB barebox主机SHA全部验证，ROM loader一次DCD/下载/跳转成功报告后60.141秒未出现barebox串口，按无人值守规则停止。未进入6.6、未部署rootfs/v7、未改分区/硬件参数/DT/EXT_CSD；既有配置与部署状态本轮未重新读回，不能新增通过结论。自动持久根/10轮/STOP/写回均仍缺。详EMMC-NIGHT-DEPLOY-20261003.md，失败阶段未定位，不归因v7。

## 2026-10-02 boot启动区只读核验完成

冻结CCM 6.6 RAM，标准MMC临时访问切换已获授权；EXT_CSD前后512字节全等，179=48/177=00/178=00/173=00/174=00。boot0当前SHA321f31a0…与备份一致，boot1当前1MiB全零SHA30e14955…；无数据写/启动选择/保护位修改。ROM下载态3a20207c解码BOOT_MODE10/BT_FUSE_SEL0，Table6-2为直接下载，不依赖boot1映像；下键额外BOOT_MODE连线仍无板图实证。详见BOOT1-BAREBOX-PREPARE.md顶节及modularization/boot1-ram-readonly-20261002.json。仅设备取证，X/Y工作树未碰，部署由主管另行安排。最终长按回旧健康2.6.31/kexec0/battery_error0，4164mV/-74mA；已停铃，本轮停止。

## 2026-10-02 boot1引导方案只读准备

仅方案，未部署，原厂boot0及179均不写。缓存boot选择48、总线00；完整EXT_CSD/当前boot哈希/按键额外BOOT_MODE接线仍缺。ZQ23/8保留开发基线，3400/3600mV低电门槛延后风险未关闭；见BOOT1-BAREBOX-PREPARE.md。

## 2026-10-02 R2返回失败，R3暂停

R2 fresh ROM/debug/ZQ23/8，201.42秒未回旧；RAM连续29条CRC有效至WDI写低返回，末态照片保持R2；约36秒出现描述符失败。连续相机时间线缺失，未取得成功屏幕基线。旧系统健康与MEMA恢复通过；正式参数未改。证据RESTART-LOCATION-RESULT-20261002.md及modularization/restart-round2-20261002.json。R3仅准备主机目录，未加载。下一任务只读评估boot1 barebox链式加载boot0原厂U-Boot，不写存储/EXT_CSD。

## 2026-10-02 restart定位：正式参数未改，WDI之后失败已采证

CCM基线ZQ23/8、相同正式DTB/RAM根/barebox，独立debug仅MEMA5–15进程标记/原子CRC记录，正式源码与冻包不改。首轮200秒未恢复；30条双CRC证明guard停止、RTC准备、PC2=400161、最后R34=200400/PWGT00、WCRff3d、SRC521、mux1/pad4及GPIO6_28 DR写低并返回。不能提升为PMIC掉电/原厂启动已完成。约128秒无恢复并不证明计数器坏：ext_reset WDOG_B在GPIO mux下没有独立内部reset保证。原厂BIT1重启标志相同，U-Boot ADC3400/3600分支不见MEMA消费；冷成功/失败前标志同值。原厂硬件策略未新增偏离；恢复稳定性仍未验通过，MEMA/OCRAM跨人工复位失效，主证据为CRC RAM及USB。详RESTART-LOCATION-RESULT-20261002.md。

## 2026-10-02 阶段4第二项：五向键默认m（离线，待合并冷验）

原厂GPIO1_20/19/16/17/18高有效、pad0xc4、现已验KEY_UP/DOWN/LEFT/RIGHT/F24与60ms参数保持；正式imx50-kindle-k4.dts/DTB逐字节不变。上游KEYBOARD_GPIO y→m只延迟接口出现，不改硬件参数；五向键原未声明wake，PMIC电源键/RTC、matrix与恢复依赖内建。production去除历史dmatest/usbtest防通用coldplug加载诊断，正式234模块；不改变电源/充电/时钟。原rcS以base字节保留，新增wrapper在保护/guard/USB之后非致命通用modalias加载，原SPI/BUSYBOX/guard/外层bootstrap哈希不变，无黑名单/-b。y/m/n完整ARM+alias通过、13主机测试、RAM根54非模块文件及外层输入一致；真实coldplug/实体事件/唤醒/卸载重载与两项恢复仍待合并冷验。见MODULARIZATION-STAGE4-FIVEWAY.md、MODULARIZATION-STAGE4-COLD-CHECKLIST.md及modularization/stage4-fiveway.json。

## 2026-10-02 阶段4首项：panel flash模块生命周期（待冷确认）

原厂面板NOR数据/波形/VCOM继续只读、SPI mode0/8bit/原DT频率/片选/pinctrl/布局不变；生效正式imx50-kindle-k4.dts，DTB SHA仍c8bd73fea78e70d2e807385b3208c4c2cd19c1305835a3863254e73cd523e88a。production原有NVMEM_K4_PANEL_FLASH=m保持，不改变充电/PM/时钟/恢复策略；现代NVMEM module owner显式化、禁止绕过消费者引用的bind/unbind。y/m/n完整ARM目标/modpost/alias通过，9388实际C故障测试通过；缺失仅显示消费者defer的源码/链接证据，不提升为实机安全返回。阶段2已验coldplug作为既有依据；本次保护变化的冷加载/拒绝强拆/PM/独立无消费者卸载重载/缺失与延迟加载仍待主管安排。见MODULARIZATION-STAGE4-PANEL-FLASH.md、modularization/stage4-panel-flash.json。无新增硬件参数偏离。

## 2026-10-02 阶段3 DTS结构整理：DTB逐字节不变

正式K4 common + 顶层取代44个板级片段的继承；74份历史DTS移到porting/dts-archive/k4-pre-stage3，旧stock-pxp目标保留等价别名，debug顶层独立。所有原厂已验regulator/clock/GPIO/OPP/pinctrl参数保持：137节点、705属性全部相同，分类90/73/45/5/57项逐一一致，DTB及dtc -s规范化DTS精确一致，SHA c8bd73fea78e70d2e807385b3208c4c2cd19c1305835a3863254e73cd523e88a；W=1编译无dtc警告。无运行参数/驱动变化，故本结构变更无需另冷回归。主管明确schema工具校验延到阶段7，不能称schema已通过。见modularization/stage3-dtb-verification.json。
## 2026-10-02 模块化阶段2：production 正式冷回归通过

硬件参数/DT与阶段0基线保持不变，仅正式core/诊断分离配置已冷验证：DDR2/00800000/2、AMC8/AIPS、PMIC四组/VVIDEO/DRM、CCM/SRPG/USB、GPIO6_16输出低/SRC521/WCR3b3d一致；WDBG0沿用加载器差异且watchdog注册。正式taint0/诊断入口缺席、显示/Wi-Fi/800与160MHzSTOP/RTC/16MiB保持通过，功能后临时只读审计卸载，34.62s自动回旧、旧健康正常。配置没有新增偏离；debug profile本轮未上机、恢复故障注入/电气裕量等边界仍保留。正式CRC关闭，不能用空trace断言末阶段/兜底未触发。详MODULARIZATION-STAGE2-COLD-20261002.md。
## 2026-10-02 阶段2：正式core/诊断分离（离线通过，冷回归待定）

仅源码布局与诊断配置变化。正式 IMX50_OCRAM/PM/charger/restart/health/USB/watchdog 内建；诊断 master 默认n，probe/trace/MMC试验参数在debug profile。原厂硬件参数与当前已验参数未变：同stock-pxp DTS/DTB、同OCRAM汇编/偏移/池大小、同DDR/PLL/电源时序；barebox及上游ZQ23/8沿用。原厂没有本项目诊断接口，去除诊断不改变硬件策略。现代实现的拆分依据用户批准的模块化方案。

两套ARM构建、符号/stub核验、host C测试、DTB/汇编精确对照通过；正式RAM根guard/health/bootstrap/存储只读保护内容保留，自动bootmark改no-op。尚无阶段2设备验证；显示/Wi-Fi/两档STOP/RTC/16MiB/板级返回与后备恢复待主管冷回归，不能引用阶段1元数据等价代替阶段2功能通过。见 MODULARIZATION-EXECUTION.md、modularization/stage2-verification.json。
<!-- 2026-10-02 阶段1闭环：固定构建元数据后vmlinux/zImage/DTB/235模块精确一致，RAM根25/412项语义一致；无硬件参数变化。 -->
<!-- 2026-10-02 模块化阶段1兼容配方：无硬件/DT/驱动参数改动，config/DTB/235模块一致；zImage构建元数据差异见MODULARIZATION-EXECUTION.md。 -->
## 2026-10-02 模块化阶段0

冻结7dd51e9aa、本地归档与独立工作树完成；硬件配置/DT/驱动/加载策略均不变，无设备测试。执行记录见MODULARIZATION-EXECUTION.md。

## 2026-10-01 纯ZQ实机追加结论

纯六字节DCD8/4包冷功能与配置通过、板级返回121.01s失败。已回旧健康；8192字节CRC仅3条有效，卡点未定位。8/4两次失败、23/8一次成功支持关联，尚不能定唯一根因。暂用23/8 RAM基线，8/4保留对照，不写存储。后续最小4轮ABBA重复方案及每次人工操作见 [ZQ-DCD-ONLY-COLD-20261001.md](ZQ-DCD-ONLY-COLD-20261001.md)。不请求ROM，本轮结束。

## 2026-10-01 ZQ追加结论

B冷功能通过但板级返回失败，回旧健康；CRC trace无有效副本，最后阶段缺证据。原厂与barebox EMR/pad/PHY固定配置未发现耦合差异，完整B运行态CTL/PHY尚未采齐。已冻结基于成功aligned-safe二进制、只改ZQ三值/六字节的单变量包，尚未冷验；不请求ROM。详细证据、哈希、读回方法及WATCHDOG_POLLER边界见 [ZQ-COUPLING-20261001.md](ZQ-COUPLING-20261001.md)。

## 2026-10-01 A实机通过，已回旧待B

A fresh ROM正常stage5/tag5a511708，wd120/autoping1。显式8/4装载：candidate00200000/05090010/408，16MiB逐字校验errors0，status0/done444f4e45/checks7/rollback_stage3；当前完整回滚00200000/09180010/817，USB恢复。原始串口和RAM记录归档diagnostics/zq-apply-ab-20261001/a。它证明当时运行时装载及该项校验通过，不能直接证明冷DCD错误。用户长按回旧，旧健康详见本轮old-health。下一等待用户进入ROM测B，不重复A。

## 2026-10-01 ZQ接续暂停

本机8/4冷DCD启动失败，尚未取得生效读回；编码/七条顺序按实物与上游一致，未确定根因。默认测量无装载；新增显式-a RAM诊断仅离线验证，先上游23/8启动后load/test/rollback，再按机DCD+早期tag，未改变正式内核/DT或通用ZQ默认。SBMR任务关闭于已测路径，不再追fuse。详见RESUME顶部及ZQ-APPLY-DIAGNOSTIC-20261001.md。

## 2026-10-01 按机ZQ冷配置

本机原厂8/4，上游默认23/8；显式设备片段8/4，通用默认不改。初次ROM DCD完成但barebox USB未出现；有效值及显示/WiFi/STOP/内存/返回仍缺冷证据，不发布为通过。见ZQ-LOCAL-COLD-FAILURE-20261001.md。

## 2026-10-01 zqcal最终RAM验收通过

记录版16e75b22c的1+16次全PU8/PD4，16/16；每轮安全恢复、256KiB完整、CTL19/20/73/74/75原值恢复，checks7/status0。匹配原厂CTL75=408、CTL74=5090000/5090010；barebox静态817/9180000即23/8，多15/4个trim码，不能等同电阻比例。未apply，正式静态配置不变；逐机配置/早期ROM plugin动态校准为后续选项。用户长按回旧健康、kexec_loaded/battery_error0。仅本机当前条件测量通过，第二台/温压裕量待验，SBMR具体回ROM分支仍缺证据。见ZQCAL.md。

## 2026-10-01 zqcal诊断工具改进（实机待验）

只改变RAM诊断记录/USB暂停范围/喂狗，不改有效ZQ或存储；单独-r读回每轮PU/PD及C层checks，正常返回auto-poll，危险park仍超时。17492主机例与ARM构建通过；新records包1+16待验。SBMR原厂00/本轮10及回ROM缺口见ZQCAL.md。

## 2026-10-01 zqcal首测

ROM测得PU8/PD4、阶段2/status0，寄存器恢复；C层校验丢输出，16次未测，不判完整通过。wd120无持续喂狗致watchdog复位（WSTR2），非DDR park；用户长按回旧健康。SBMR仅bit25差，10/fuse-only vs00，回ROM具体分支缺证据。见ZQCAL.md；无存储写入/无apply。

## 2026-10-01 ZQ测量工具准备（冷RAM待验证）

原厂旧系统只读ZQ为CTL73=200000/CTL74=05090010/CTL75=408，PU8/PD4；barebox静态PU23/PD8。实物LPDDR1算法与k4-uboot-installer参考不一致，采用实物f80085a4的r0=1分支。新增裸机zqcal overlay（OCRAM/自刷新/不装载/恢复当前配置），gcc寄存器模型438例与v2026.09.0 ARM构建通过；尚未ROM实测，不宣称测得校准值。当前正式DT/内核/加载器静态值未修改，3400/3600门槛按用户决定延后。详见[ZQCAL](ZQCAL.md)。

## 2026-10-01 耗尽电池引导链只读审计（未改配置）

原厂main U-Boot实物确认≤3400mV拦截、3600mV充电循环退出；barebox v2026.09.0 kindle-mx50默认路径无等价等待。6.6现有BPON为内核/用户态接管后的充电策略，不覆盖ROM/DDR/引导负载窗口。MC13892硬件可先80mA无CPU恢复，K4既有single/MODE00读回支持正常USB分支；首次上电失败后继续充电不保证随后自动再次启动。默认barebox替换评为高风险，须补启动门槛/受保护等待/USB额度与所有权交接后再真实低电验收。参考5.1.2电流表与本机boot0 setter不同，不能用参考480mA描述实物或照抄实物880mA请求。见[完整分析](BOOTLOADER-DEADBATTERY-ANALYSIS.md)。正式驱动、DT、镜像与存储保护均未改；本轮未访问设备，物理低电证据仍缺。

## 2026-10-01 最新：aligned-safe 冷功能与自动板级返回通过

5e74ecee3冻结00286包冷验收17项PASS，GPIO6_16输出低/SRC520→521/WDT c735→c73d正式冷路径确认；WDBG被barebox锁0，仅warning，watchdog注册与guard启动通过。返回前探针纯读XOR0/wrote0。34.78秒自动回旧，无人工动作，旧kexec_loaded/battery_error=0、4199mV/+61mA/99%。两端均抢读8192 RAM，CRC24有效/4序号缺口，无冲突；WDI前R34=200400/PWGT00、WCRff3d/SRC521有效。与直接WDI返回相符，未测电气波形；guard/1秒兜底无有效事件但不能证明未触发。GPIO/SRC联合对齐有效，单项根因未二分。见[本轮逐项结论](RESTART-ALIGNED-SAFE-COLD-20261001.md)。当前已回旧，无运行中试验；以下待冷条目为历史状态，以本节为准。

# K4 / Yoshi 原厂配置与移植差异记录

## 维护约定

用户要求（2026-09-30）：每完成一项移植，更新本记录。恢复原厂参数、增加或移除偏离、改变集成设备树、得到新的验证结果时，也更新对应条目。

每项必须记录：原厂参数和源码位置；当前参数和生效路径；是否偏离及必要理由；源码/手册依据；验证方式、结果、包或提交；剩余缺口。现代 Linux 接口替换本身不是更改硬件参数的理由。

区分“沿用原厂”“本机旧系统快照”“硬件参数偏离”“软件策略变化”“临时试验”“未核对”。不把试验 DT 的通过结果当作集成 DT 已启用，不把主机测试或寄存器读回当作实测电压、功耗、冷启动或长期可靠性。原厂与手册冲突应明确列出，不静默替换。

本记录为持续维护的索引，详细证据保留在各功能文档。修正旧结论时保留原因及日期；不覆盖历史失败来宣称一直通过。

## 初次核对范围

2026-09-30 旁支会话只读源码核对，随后按用户要求建立本文。未操作 Kindle、未改内核/DT、未构建。主任务并行推进；保存前复核 HEAD 为 `111e76e114705db09fccf6faeef95e1555d5f94a`，工作树和功能记录可能包含其后未提交更新。

原厂来源：Windows `$BACKUP\k4-custom-kernel-4.1.1\amazon-attributed-source`。
核心板级文件：`arch/arm/mach-mx5/mx50_yoshi.c`、`mx50_yoshi_gpio.c`、`mx50_yoshi_pmic_mc13892.c`、`clock_mx50_yoshi.c`；显示 `drivers/video/mxc/`；充电 `drivers/usb/gadget/arcotg_udc.c`。
当前实现：本仓库 Linux 6.6.157，板级树位于 `arch/arm/boot/dts/nxp/imx/imx50-kindle-k4*.dts`。

下表是重点参数核对，不是全部寄存器逐位一致性证明。验证结果未逐项重新上机；已有结果以链接中的原始记录为准。

## 沿用原厂的重点参数

| 项目 | 原厂基线 / 当前一致内容 | 当前实现与核对范围 | 依据 |
| --- | --- | --- | --- |
| CPU OPP | 800 MHz/1.05 V；160 MHz/0.85 V；PLL1 800 MHz | OPP/cpufreq 与 CPU 分频替换旧框架；SW1 的额外等待另列 | mx50_yoshi.c cpu_wp_auto；CPUFREQ.md |
| eMMC | ESDHC3、8 bit、40 MHz 上限、不可移除、对应 pads | 上游 SDHCI；这里只确认板级参数，不证明全部源时钟初始化一致 | mx50_yoshi.c mmc3_data；EMMC.md；emmc-id.dts |
| Wi-Fi SDIO | ESDHC2、4 bit、50 MHz 上限、SDIO IRQ | ath6kl 替换旧 ar6k；源时钟配置需单独核对 | mx50_yoshi.c mmc2_data；WIFI.md；WIFI-STOCK-COMPARE.md |
| Wi-Fi 使能/RF | GPIO5_28、40 ms；天线参数10000/3/1/36 | pwrseq 以 reset 极性表达同一供电脚；fb.dts 保留 RF 四参数 | mx50_yoshi_gpio.c；wifi-pwrseq-probe.dts；fb.dts |
| I2C | 100 kHz、GPIO6_5 接口使能、等待20 ms、总线 pads | 现代 GPIO descriptor/总线驱动；GPIO 历史命名需注意 | mx50_yoshi_gpio.c gpio_ssi_rxc_enable；i2c2-bus.dts |
| PMIC SPI | MC13892 CSPI/SS0、2 MHz、GPIO6_8 IRQ | MFD/regulator 替换旧 PMIC API | mx50_yoshi_pmic_mc13892.c；pmic-mfd.dts；PMIC.md |
| 面板 Flash | ECSPI2、1 MHz | SPI NOR/NVMEM 替换 panel_flash_spi；当前只读为试验策略 | mx50_yoshi.c panel_flash_device；panel-flash.dts；PANEL-FLASH.md |
| 面板时序 | 800x600、目标32 MHz、对应边界/扫描时序 | 控制器后端移植；实际时钟配置另列 | mx50_yoshi.c E60_V220_WJ；EPDC-HW.md |
| 显示电源接线 | Papyrus WAKEUP/VCOM/PG/IRQ GPIO | regulator/hwmon 现代实现；电压配置与校准另列 | mx50_yoshi_gpio.c；PAPYRUS-POWER.md |
| 按键 | 五向键60 ms去抖；矩阵键10 ms、对应接线/极性/键值 | gpio-keys/矩阵输入替换旧驱动；电源键释放轮询为新实现 | fiveway.c；tequila 键盘源码；fiveway.dts/keypad.dts |
| USB VUSB2 | 首次启用等待10 ms、供电与时钟的基本先后关系 | 交给 USB 控制器按现代生命周期管理 | arcotg_udc.c；USB-SUPPLY.md；USB-SLEEP.md；fb.dts |
| Tequila 待机 SW 电压 | SW1 0.85 V、SW2/3 0.95 V（相应板型） | 标准 suspend bank API；不是轨电压实测证明 | mx50_yoshi_pmic_mc13892.c；PMIC-STANDBY.md |

## 硬件配置、初始化与策略差异

| ID / 项目 | 原厂 | 当前 / 差异性质 | 理由、验证与待办 |
| --- | --- | --- | --- |
| D01 EPDC 像素父源 | PLL1_SW | 曾改 PFD5；现恢复 PLL1_SW，owner 不重设共享 PLL1 | 用户要求恢复原厂；见 EPDC-STOCK-CLOCKS.md。保存前该文档已记录 #224 ROM 首次刷新及相机确认通过；本旁支未重新实测 |
| D02 像素分频/手册冲突 | 800 MHz/pre1/post25=32 MHz | 用户选择原厂方案；K4且PLL1_SW路径采用pre1/post25，其他路径仍保留480 MHz输入上限 | 原厂方案与 IMX50RM 5.4.41 的 PODF 输入上限存在冲突；#224功能通过不证明长期电气裕量。最初审计时待决，保存前依据主任务更新修正，见 EPDC-STOCK-CLOCKS.md |
| D03 EPDC/PxP AXI | PLL1_SW/200MHz，各自ASM/slow5（空闲÷32） | EPDC #227冷基础通过；PxP #247恢复原厂并暖四方向/STOP/显示通过，默认stock-pxp | 共享PLL1不改频；LCDIF相邻字段/活动拒绝；PXP-STOCK-CLOCKS.md、EPDC-STOCK-CLOCKS.md；3e1d3478c集成HVE冷首次显示/PxP已通过 |
| D04 像素门控/握手 | 旧框架回调及原厂启用/改频顺序 | 新增有限busy等待、读回和故障锁存；已允许任一级完全关闭时规范化另一级；两级都开拒绝EBUSY | CCF接管启动遗留状态的实现差异；不是硬件要求“进入时两级必须都关”。见 clk-imx50-pixel.c、EPDC-STOCK-CLOCKS.md |
| D05 充电低电量策略 | 软件BPON：<=3.8 V进入、>3.81 V退出；切换软件控制，含低压周期重启 | 恢复原厂软件BPON：<=3.8 V进入、严格>3.81 V退出；<=3.4 V每10秒CHGRESTART | 原厂模式/阈值/低压周期机制已对齐；119组驱动及ARM策略、高电量暖回归通过；真实低电量过程待现场。CHARGE-BPON.md |
| D06 USB充电额度 | mass-storage HS配置DAC5=480mA，FS DAC1=80mA；未枚举host含80mA分支 | 标准uA预算+DAC上界+可配60mA预留，500mA选400mA | 手册Table63推荐PHY活动400mA；不是原厂所有host均80mA；电气/FS政策差异见CHARGE-STOCK-AUDIT.md |
| D07 充电会话/指示策略 | 硬件120分钟+Tequila1次重启；capacity>95绿锁存 | 累计4h有效时间、精确故障码；原厂绿锁存已恢复 | #242/#246自然99/100%与STOP恢复通过；真实源/故障/长周期见CHARGE-STOCK-AUDIT.md |
| D08 STOP LDO | VDIG/VGEN2/VPLL/VUSB2待机关断 | 默认stock-pxp包含原厂mask92400 | #242/#244/#246联合恢复通过；寄存器恢复不代表轨电压/功耗实测；LDO-STANDBY.md |
| D09 PMIC ready/等待 | CLPCR保留ready旁路位；SW1速度01，25mV/4us | 继承bit2=0；标准6250uV/us取代试验1ms | #244两档STOP和32次DVFS、#246集成通过；非物理slew测量，CPUFREQ.md、PMIC-STANDBY.md |
| D10 PLL/DDR恢复编码 | 原厂PLL/DDR恢复路径与继承参数 | 原厂同样864→800/MFD179/MFN180→60；按实际udelay(10)对齐>=10us；OCRAM私有页表/栈、有限轮询 | clock_mx50_yoshi.c:495–559；60组ARM错误路径及两档STOP联合通过；非活动bank保存是实现差异。DDR-PLL.md；bootloader训练不作已验结论 |
| D11 Papyrus/VCOM | 工厂面板信息转换VCOM，其他轨有板级profile | 默认树用只读factory NVMEM+原厂276项DAC表，VP/VN/序列仍本机profile | #241/#246初始化/显示通过；PANEL-VCOM.md，其他面板与轨电压仍未测 |
| D12 SDIO源时钟 | PLL1来源，根200MHz | 默认restart及stock-pxp已恢复PLL1/200MHz | 3e1d3478c：组HVE原厂遗漏修复后冷50MHz/HS关联DHCP/4ping通过；原厂源200MHz保持 |
| D13 RTC | SRTC/PMIC RTC与跨启动校准 | 两RTC现代接口，4125d21ff修正在#233及后续 | #240暖四阶段差-8365保持；原冷+4秒遗留；本轮一次四阶段差值在1秒内，停止追加调查；RTC-RESET.md |
| D14 电量计型号 | 原厂Yoshi_Battery寄存器接口 | ti,bq27210兼容项为寄存器/接口推断；bq27xxx标准接口 | 功能接口/地址/单位暖冷已验；型号丝印/BOM未确认，留独立识别条件；NVM更新禁用。BATTERY.md |
| D15 附件 | 检测GPIO、GPO3反极性、USB/屏幕/挂起联动 | regulator标准写路径与事件状态机；默认服务根自动加载 | 2a23a0ae6无附件RAM/主机错误通过；#246集成STOP通过。用户无附件，实物单列遗留；ACCESSORY.md |

| D16 板级reboot/PMIC电源循环 | system.c:314/341：PMIC RTC当前+5秒闹钟、MEM_A bit1；gpio_watchdog_reboot：WDIRESET清0，WDOG ALT2→GPIO6_28低；PMIC初始化RESTARTEN=1 | 独立restart DT/驱动按RTC准备/读回、PMIC字段、GPIO终端两阶段接入；默认stock-pxp已继承板级restart，1秒独立紧急兜底已实测 | #233 ROM/RAM一次reboot自动回旧2.6.31/COM7/SSH，kexec_loaded/battery_error0，4185mV/+142mA；旧user_reboot。正常重启不dump并清RAM记录，terminal WDI/物理电源循环未直接观测，三轮暖启动36.95–37.12秒全部自动回旧，证据board-restart-warm-runtime-20260930；默认归档DT已改restart树，随后多轮暖/冷恢复通过；不部署eMMC，也不将早期失败抹除。原厂高总线/CCGR3 CG5未照搬，物理电源时序待测。见K4-RESTART.md及board-restart-cold-runtime-20260930-233 |

## 新的软件实现与试验参数（不混入原厂硬件配置）

- framebuffer 100 ms合并更新、500 ms空闲关电；串行LUT0、DMA故障保留：现代调度/生命周期策略，需记录是否临时和支持范围，不能当作面板波形参数或实测FPS。
- 电源键50 ms释放轮询：新输入实现；原厂长按硬复位等硬件配置需单独核对。
- 看门狗超时、有限喂狗guard、RAM/kexec、RAM标记、eMMC只读/不挂载：验证与恢复策略，不是原厂永久驱动参数。
- wpa_supplicant/nl80211、USB ACM/RNDIS、SSH、RAM根：新服务/接口选择；与硬件参数一致性分别记录。
- VDIG旧请求1.20 V与当前selector读回1.25 V的差异，应区分旧请求、硬件可编码值与继承状态；不能未经证据写成“本次主动升压”。

## 每项更新模板

### ID / 功能名称（日期）

- 原厂：参数、条件、源码文件/函数/行号；板型与适用版本。
- 当前：实际集成DT/配置/驱动、参数与提交/包。
- 分类：沿用 / 本机快照 / 硬件偏离 / 软件策略 / 临时试验 / 未核对。
- 必要性与依据：是否确需改变；源码、手册章节或实测记录。
- 验证：主机/暖启动/ROM冷启动/现场观察各自结果，证据路径；失败也记录。
- 剩余：哪些未验证、未集成或未实现；关闭差异所需工作。

## 主任务接续核对（2026-09-30）

已对照#227冷启动原始证据更新D03，并新增D16。当前HEAD为75022c2e9。
#227已恢复旧2.6.31/COM7/SSH，kexec_loaded/battery_error0；自动reboot
仍失败，未覆盖历史失败。相机/供电/时钟证据在
$BACKUP/epdc-stock-axi-cold-runtime-20260930-227。


## 2026-09-30 软件冷启动入口试验（D17）

- 原厂4.1.1普通arch_reset为PMIC RTC+5秒/MEM_A/GPIO板级循环，无ROM参数分支。
- 临时RAM诊断采用NXP给出的LPGR13000000覆盖；保持SRTC clock后probe与restore成功。
  默认集成树、时钟/电源参数未变；不是正式新设备驱动。外部模块taint4096。
- 内部timeout、SRS、SRC暖复位bit0清零对照未枚举ROM；均自行回旧。bit0先验证
  521→520→521，最后LPGR130→0后板级回旧，健康通过。不据此排除所有ROM变体。
- 固定自动清除包只覆盖外层/init与模块，内层RAM根完全一致；两次kexec清除通过。
  用户已人工进入ROM，当前加载同一清除冷包；结果随后更新。跨PMIC循环保持未实测。
- 同族5.1.2 U-Boot源确认idme/fastboot setvar持久写MMC，未执行；精确4.1.1 U-Boot
  仍需补源码。详见COLD-BOOT-ENTRY.md及私有rom-entry-evidence-20260930。


### D12/D13/D16/D17 23:01 ROM批量补充

固定#233清除包ROM原生启动，LPGR early/runtime/回旧0；外部模块taint4096。
冷Wi-Fi-110，无wlan0/关联；clk_summary证明ESDHC_A_SEL=PLL2_SW400MHz、
root200MHz，当前restart默认树尚未集成原厂PLL1来源。clock_snapshot=N，
只有初始化错误/运行ios/CCF，未采早期CMD缓存。D12下一步集成基线。
RTC清醒双闹钟通过；运行差-8370，板级回旧-8366，本轮4秒变化为D13遗留。
板级返回36.9秒旧SSH，普通健康/LPGR read/COM7通过；不写eMMC、不刷新显示。
清除包ROM路径已验（进入时LPGR0），非零清除证据仍为kexec两次。


### D12 默认restart树恢复原厂SDIO来源（23:12）

默认imx50-kindle-k4-restart.dts新增与既有sdio-pll1-probe一致的4组assigned
clock项：A_SEL=PLL1_SW800MHz，A_PRED/PODF200MHz，C_SEL=A_PODF。
不重设共享PLL1，ESDHC3仍走独立B根；DT反编译差异仅3条assigned属性。
沿用冻结#233 kernel/根/235模块，只改DT。暖kexec实测父源800/根200，
WPA COMPLETED/网关2/2、双RTC清醒闹钟、USB、eMMC全RO未挂载、显示updates0、
taint0通过。板级reboot36.7秒回旧；冷Wi-Fi本轮未验证新默认树，既有#179
独立PLL1冷对照失败，不把本次基线集成当修复，不再重复原时钟模式扫描。
私有default-sdio-pll1-runtime-20260930、包k4-default-sdio-pll1-ram-20260930。

### D15 / 2026-09-30 无附件输出阶段

原厂 GPO3 clear=ON/set=OFF 与 VIOHI 常开已在独立 accessory-policy DT
接入；板级属性只反相GPO3，沿用 regulator POWERMISC/PWGT 写路径。
USB ONLINE/显示blank/PM状态机与原厂条件表见 ACCESSORY.md；58项
主机表/IO故障通过，#240 RAM 四轮通断、非法输入拒绝、两轮模块生命周期、
fb blank/unblank和设备PM恢复通过。输出仅bit10变化、VIOHI配置不变，
未测外部电压/负载；真实附件与实际USB源变化未验，不增加未知附件充电额度。
36.7秒自动回旧、健康通过。默认restart树仍input-only，独立树已经验证。

### D11 / 2026-10-01 工厂 VCOM 消费

panel-vcom独立树按原厂偏移/字符编码/276项DAC表读取只读NVMEM，
Papyrus在GPIO接管前选用工厂值。本机值等于既有cf快照；VP/VN/序列
保持原profile。#241 fixed-layout RAM初始化、图案刷新、blank/unblank、
相机/RO/taint0通过，见PANEL-VCOM.md。首轮ENOENT配置错误保留。
没有声明校准单元的默认树仍使用DT参数；不是默认树部署完成。
完整旧回退、不同面板、冷消费、电压仍需验证，未推导其他轨校准。

### D13 / 2026-10-01 同轮暖路径

D15 #240旧→新→重启前→旧四阶段差均-8365秒，未重现冷轮+4秒。
旧后台同步和SRTC初始化为源码候选；根因未确认，不校时，见RTC-RESET.md。

### D07 / 2026-10-01 原厂绿色UI条件恢复

原厂capacity>95后锁存，断开清除；现代此前reasonfull才绿色的偏离
已修正。共享helper边界/故障/会话测试与122项充电IO回归通过，
#242自然99%/eligible/full0绿63，PMIC RTC STOP恢复绿63、黄0、
显示图案/blank/unblank/相机通过，36.7秒回旧健康。保护条件未改。
黄色净充电语义、有效时间累计、故障精确分类仍非全部原厂等价，
真实物理插拔/完整充电周期及灯色未验；见CHARGE-LEDS.md。

### D08 / 2026-10-01 四路原厂mask联合试验

stock-ldo独立DT启用VDIG/VGEN2/VPLL/VUSB2的0x92400原厂STBY位，
#242一次PMIC RTC STOP、mode读回/完整恢复、GPO3回调、自然full绿灯、
醒后图案/blank/unblank及相机通过，错误0、RO未挂载/taint0。
默认restart仍VUSB2-only；不是轨电压/功耗实测，PMIC ready旁路仍D09。
详见LDO-STANDBY.md；没有改变电压和晶振/待机等待参数。

### D09 / 2026-10-01 ready旁路继承恢复

pm-imx50.c不再强制旁路bit2，按原厂保留CLPCR原值，本机0。#244
800/160MHz两次四路LDO STOP、01000762读回/01000021恢复、双RTC、
GPO3/绿色/醒后显示/相机通过，36.8秒自动回旧健康。主机继承0/1及
既有WAIT/STOP/SRPG/OSC故障回归通过。未改I2C3/RDY mux，物理ready
接线和实际电压恢复未测；SW1 1ms仍另项，详见PMIC-STANDBY.md。

### D09 / 2026-10-01 SW1标准斜率声明

独立stock-sw1-ramp按MC13892 Table50/140速度码01声明6250uV/us，
去掉假设固定1ms；不写速度寄存器。#244 32次DVFS、两档STOP与
醒后显示/原厂四路LDO/ready继承通过，eMMC RO未挂载；见CPUFREQ.md。
名义32us不代表物理电压波形。随后集成包采用此树。

### D08/D09/D11/D15 / 默认归档与自动模块接管

默认归档选stock-sw1-ramp，服务根按controller compatible自动加载附件owner。
#246暖集成WPA/网关4/4、32次DVFS、刷新后两档STOP与醒后累计9次显示
更新/相机/RO/taint0通过。见INTEGRATED-RAM.md；未部署或冷验。

### D03 / 2026-10-01 PxP原厂配置恢复

PxP idle/reset后选PLL1/200MHz，enable设置bit13/slow5；LCDIF共享路径
活动拒绝和相邻字段保留。#247修正版暖四方向、STOP醒后显示累计16/
错误0、CCF与相机/通信/RO/taint0通过，36.8秒回旧。
默认stock-pxp；冷包已准备。见PXP-STOCK-CLOCKS.md。

### D05/D06/D07 / 精确原厂充电差异收束

新增CHARGE-STOCK-AUDIT.md：原厂file_storage向vbus_draw传DAC5/1（HS/FS），
不是标准mA；高电量反复试验不能验收低压/硬件故障/输入总电流。
保留有手册依据的现实现，下一有效门是真实源变化/低电量电气。

### D03/D12/D13 / 2026-10-01 正常集成冷启动实测

基线 d54fd7b13 冷包：PLL1 SDIO 仍在 50MHz CMD52/CCCR07 返回-110，
wlan0不存在，不能计关联通过；PxP冷图像首次 EBUSY，owner未启动/更新0，
相对#227回归。暖#247结果保留。下一步冷暖 IOMUXC/ESDHC/CCM/供电全量
对比和#227以来 PxP/EPDC共享AXI差异诊断。双RTC各5秒闹钟通过，
返回前后相对差-19135→-19131（+4秒）；基础集成读回/RO/taint0通过。
36.953秒自动回旧健康。见INTEGRATED-COLD-20261001.md；今晚按用户要求停止。


### D03/D12 / 冷故障机制对照与诊断（2026-10-01）

生效stock-pxp树。LCDIF原厂CG10=0，新增CCF终端门登记清理未认领继承位，
保留活动拒绝，不改PLL1/EPDC频率。SD2位8是保留位，撤销pad候选，
保留原厂1d6/1e6写入（硬件d6/e6）。旧系统确实HS/50MHz，不增加低速上限。
原厂mx_sdhci改分频保留内部clock enables，现代i.MX50对应路径恢复此顺序。
原厂板级GPIO低→高+40ms、MMC复位不动GPIO，K4 pwrseq显式compatible
对齐；暖冷差异因果尚未证实，不能把它当已定位主修复。来源文件行号、
差异必要性及临时诊断范围见COLD-FIX-20261001.md。最终主机385时钟场景/保电生命周期与ARM构建通过；最终暖四旋转/STOP15秒/
醒后刷新、网关4/4、只读/taint0通过，PxP25/result0，RTC差不变。36.9秒
自动回旧健康4199mV/+87mA/100%。数字快照与镜像SHA已归档，冷验证剩余，不带LPGR。


### D03/D12 / 06a36470d 原生结果与 PMIC 后续

冷显示首次成功updates2/errors0、PxP complete0/fault0，相机完整；冷无线仍
50MHz CCCR07 -110，已逐字段归档冷/暖/旧差异，未把其他CCM字段复制到SDIO。
36.9秒自动回旧健康。详见COLD-FIX-20261001.md。
PMIC历史冷/本轮旧回读确认CLK32KMCUEN=1/驱动强度00两边相同，各候选LDO
清醒使能相同，WiFi实际供电轨尚无电路依据。原厂pmic init:511–521无条件
SW1–4 AUTO8遗漏已通过regulator初始模式对齐；stock-pxp补原厂SW4常开约束，
保留所有电压码/HI/STBY字段。4096实际C与ARM/AUTO暖显示联网/STOP/RO通过，
37.0秒自动回旧；冷结果待一次诊断套件。未改DRM、不强开未知轨。

## 2026-10-01 同会话无线判别诊断（临时策略）

生效树仍正常 stock-pxp 集成树/SW1–4原厂AUTO8，电压/PLL1/50MHz未永久改。
新增显式开启的首次前后64项PMIC及SoC失败缓存；A单次GPIO低1000ms+原厂40ms，
B临时25MHz/禁HS，C provider重施原厂AUTO（pmic init:511–521）。
初始暖显示/WiFi4/4/64项读取/RO/taint0通过；A host解绑遇PID1无线respawn
竞争并阻塞，B/C未测。返回120秒失败，已响铃请求强制回旧。修正版暂停RAM
inittab wifi respawn/保留guard，尚未实机；冷包暂不就绪。
电气放电/回灌及实际AR6003电源轨/32k波形未测，不把GPIO读回当模块断电。
来源、限制与失败证据见COLD-FIX-20261001.md及batch3-warm-result.json。

## 2026-10-01 批量判别暖验证与关机阻塞兜底通过

正常stock-pxp/AUTO8原厂参数不变；实验脚本先关闭网口避免ath6kl注销锁递归，
保留临时暂停respawn。A低保持1.030秒，B25MHz/timing0，C50MHz/AUTO8，
三组各关联/ping2/2，PMIC上电/下电及实时64项error0，SoC缓存、RO/taint0通过。
准备后的显式RAM 1秒hrtimer旁路绕过device_shutdown，不改变原厂RTC +5秒、
GPIO/PMIC参数；guard看到reboot_pending停喂，避免局部阻塞仍因PID1心跳喂狗。
真实解绑超时无人返回成功，另stall4秒时1.391秒断开/37.7秒旧健康恢复。
物理电源/32k波形、极端停钟/STOP可靠性及AUTO冷无线结果未宣称通过。
新正常冷包batch4-ready已静态/SHA/暖配对验证，无LPGR，尚待一次ROM。
来源与异常历史见COLD-FIX-20261001.md、K4-RESTART.md、batch4-warm-result.json。

## 2026-10-01 SD2/NANDF组HVE原厂对齐

生效树imx50-kindle-k4-stock-pxp.dts。原厂mx50_yoshi_gpio.c:1061/1063分别
6c0/69c=2000；旧521字读回确认。此前仅单脚pad，组位继承bootloader；现通过
pinctrl board属性在消费者前仅设置HVE bit13，原厂1.8V输出缓冲范围，保留
所有其他位/PMIC电压/PLL1/单脚pad，不属降频策略。原厂所有组与daisy审计见
COLD-FIX-20261001.md：同类NANDF已补；DDR组由加载器初始化，未用外设不强开。
暖release00253两组2000→2000、521字缓存/显示updates2错误0/WiFi4ping/RO/taint0
通过，36.8秒回旧健康。冷HVE设置前值与修复效果待一次ROM；旧运行全区读回及
冷暖PMIC64对照已归档。batch4冷AUTO仍失败，B25MHz枚举后enable -84，首次显示
正常；不把错误码当物理信号测量证明。RAM-only，无LPGR/eMMC/idme/fuse写入。

## 2026-10-01 SD2 HVE冷启动实测完成

cf0ddb869正常stock-pxp冷包：SD2组69c实测0→2000，NANDF6c0原2000保持；原厂
Yoshi1061/1063机制对齐验证完成。WiFi首次50MHz/HS关联/DHCP/ping4/4，原先
CCCR07超时消失；不需25MHz策略。冷首次显示ret0/updates2/errors0/PxP正常，
相机完整。IOMUX521xfirst/latest与PMIC64xfirst_on/live前后保存，未触发的
失败/first_off缓存明确为空。RO未挂载/taint0、37.0秒板级回旧/健康通过。
完整原厂参数/审计/证据见COLD-FIX-20261001.md及hve-cold-result.json；配置
电压为输出缓冲HVE范围，不修改PMIC供电值/共享PLL1。剩余未启用引脚不盲写。

## 2026-10-01 ath6kl注销锁修复
现代cfg80211 API锁递归，不属原厂硬件差异。RTNL内dev_close后wiphy锁清理，
UP态sdio/core rmmod、SDHCI解绑重绑及UP重启通过，恢复ping2/2/RO/taint0。
正式配置保留builtin，237模块为一次生命周期测试；来源/结果ATH6KL-REMOVAL.md。

## 2026-10-01 D10原厂等待与联合验收
原厂clock_mx50_yoshi.c:559实际udelay(10)，OCRAM循环128→240保证OSC至少
10us。release00257暖800/160MHz STOP两次，PLL/DDR stage4、64KiB完整、
PMIC prepares/restores2/2、显示10次/错误0、WiFi4/4、RO哈希一致、taint0。
37秒板级回旧健康。相机kindle-20261001-112219-540518.jpg完整。
证据build-k4-v6.6.157/joint-warm-20261001/round-1；电源键消抖另行收束。

## 2026-10-01 D04/D06/D07/D13/D14与其余设备收束
逐项原厂文件:行号、接口替代/硬件参数差异/现场条件见REMAINING-ACCEPTANCE.md。
D04按原厂无LCDIF消费者清终端门、CCF有界生命周期保护，配置差异关闭。
D06保留500mA→400mA最坏上界预算保护，60mA为声明未实测；不冒充原厂FS
政策等价。D07精确故障10/一重试/>95绿锁存已实现，4h累积为额外软件边界；
真实电气/长周期条件保留。D13本轮-51172/-51172/-51171/-51172，不复现+4，
仅记录遗留。D14寄存器兼容/标准接口已验，不将包ID当型号证明。
14键冷事件与#130电源STOP唤醒已有，不重新作为未实现；音频SSI等仅非Tequila
分支，K4不适用。PLAN顶部现为当前设备验收索引，历史段保留。

## 电源键完整原厂初始化链与暖读回
板级mx50_yoshi_pmic_mc13892.c:536–547先设置三按钮码1；yoshi_button.c:226
再调用pmic_power_set_conf_button(ON1B,0,2)，pmic_power.c:93–134编码。
因此当前probe只RMW消抖字段mask3f0/value160，读回验证，保留复位字段。
release00258暖读回POWER_CTL2=401161，三个evdev能力、初态释放、RO/taint0
通过，36.8秒自动回旧健康4161mV/98%、kexec_loaded/battery_error0。
此前仅板级码1的401151暖联合结果保留，不将它误称原厂最终配置；未进入冷包。
最终源码等待冷短按/2秒长按事件及STOP唤醒现场复验。旧uevent/长按LED
产品策略与硬件输入分别记录，见REMAINING-ACCEPTANCE.md。

## 2026-10-01 冷联合及现场验收结果

冻结37df98604/d320d902d正常集成包，release00258/235模块，仅RAM。
冷WiFi50MHz/HS关联DHCP、首次/两档STOP后/最终网关分别4/4、4/4、2/2；
冷首次显示通过，最终14次更新/错误0，32/RGB565/Y8竖屏正常；相机
kindle-20261001-114830-144785.jpg完整。800/160MHz STOP两次PLL/DDR stage4、
64KiB数据、PMIC prepare/restore通过，RO采样SHA一致、无MMC挂载、taint0。
IOMUX first/latest各521字（前/后共4组）、PMIC完整64字共7组保留。

现场：第一次短按只收到0.402s事件，旧程序不支持mem-button，未进入STOP，
明确不计为唤醒通过。换当前源码静态ARM工具/tmp后，真实STOP14.651秒
由PMIC父IRQ312唤醒，按钮IRQ2→3、rtc_ready0，备用60s RTC未触发；
释放事件完整、无卡键。用户随后按住约2秒松开，完整KEY_POWER按下/释放；
原始evdev时间戳间隔5.687352秒，不将用户估时冒充精确2秒计时验收，
也不据此宣称原厂uevent/长按UI兼容。

用户目视绿色常亮，对照brightness63/capacity99%、>95原厂锁存。USB底部
现有电脑线拔约5秒再插回：来源预算500000→0→100000→500000uA，online1→0→1；
无源code0/计时389746→0/绿灯63→0，重连故障2清0、绿63恢复。
断开时临时fault2受保护停止，重连采样核验后清除，不把它隐藏成全程fault0。
USB网络/SSH自动恢复，恢复后wlan仍关联、网关2/2。未测墙充分类与总输入电流。

所有诊断保存后板级返回38.3秒自动到旧2.6.31/COM7/SSH，kexec_loaded0/
battery_error0、4196mV/+106mA/99%。原始日志完整保留build-k4-v6.6.157/
stage-joint-cold-runtime-20261001-ready，Git诊断索引含SHA与结构化快照/事件。

RTC STOP内两计数同进15秒、offset不变；板级返回前55432/1021差-54411，
旧健康55543/1136差-54407，跨返回+4秒再次记录为D13遗留；未校时，
不继续展开之前已限一次的复位调查。

脚本首档cmp误报POWERMISC218000→200000，仅PWGT特殊读/写位18000，
其余17项一致；修正比较保留原值，只规范化PWGT两位，GPO/其他位仍比较。
第一档未重复物理STOP，只补其已执行的结果检查，再完成第二档。
该读回不能证明实际PWGT轨电压/功耗。修复与工具能力门槛提交3297b9ce4。

剩余条件：自然低电量BPON升压/真实低压周期重启、真120分钟故障/长时
充电、墙充/FS政策与总输入电流、电压/功耗测量；用户无附件，附件实物
仍遗留不请求操作。型号丝印/BOM未确认。写eMMC部署另需明确授权。

## D13 2026-10-01关闭约4秒失秒来源：恢复原厂DRM

原厂mx50_yoshi_pmic_mc13892.c:465–469在RTC_DRV_MXC_V2启用时置
POWER_CTL0.DRM bit4；MC13892 p50说明Off仍保持CLK32KMCU，VSRTC
不可禁用。原冷包13=000040/DRM0；暖继承旧c00050/DRM1。
仅清位受控RAM复现差-54408→-54404；旧→旧3次保持-54407。
现K4 compatible的MFD probe按原厂配置条件RMW DRM1并读回，适用全部
该PMIC兼容节点DT（正常生效stock-pxp）；未改硬件参数/RTC时间。
正式00263暖读c00050，新-54403，回旧-54403（整数相位-54404），无4秒增长。
RO/taint0/有限guard/1秒紧急返回、旧健康通过；不通过校时掩盖时钟损失。
原厂30秒PMIC→SRTC裸写同步尝试本机未成功消除绝对偏差，本轮只读不复制
该旧缺陷；既有计数差/UTC同步另列，不算校准。ROM初值0→1正式镜像
读回留下一冷机会，不要求额外人手。详RTC-CLOCK-RETENTION.md与诊断目录。

## 2026-10-01 系统性初始化审计：PMIC首批

新增D17：原厂COINCHEN/VCOIN3.0V、MODE0 standby mask92402、MODE1 mask92080、
VGEN3SETTING0/CONFIG1、POWER_CTL2 RESTARTEN1/STANDBYINV0此前冷初始化缺失，
按DT regulator约束/provider/core拥有者修正，未改无关enable/电压字段。
00264暖读回原厂值、两档STOP success2/fail0、显示14/0、只读hash保持；
最终ROM冷验累积到同一包。原厂行号与安全读回界限见STOCK-AUDIT-20261001.md。

## 2026-10-01 CCM显式初始化审计

D18：UART1/ECSPI2显式LP_APM父源、ANADIG bit16关闭CHGR_DET，按原厂有效机制补齐。
原厂12MHz请求无set_rate回调而EINVAL，不误搬为永久divider。00265仅CCM暖验证：
24MHz父源、显示2/0、WiFi4/4、RO/taint0，34.08秒回旧健康。DDR/QoS候选已撤下，
只累积冷读回；不把warm继承作为冷设置证据。详STOCK-AUDIT-20261001.md。

## 2026-10-01 SRPG初始化审计

D19：原厂cpu.c:143–150 ARM/NEON PUPSCR010f0201/PDNSCR01010101，
由PM provider显式初始化+读回，替代只读继承；不触及EMPGC/AMC/DDR。00266
暖16MiB两个STOP前后SHA一致、内核64KiB/PLL、两档success2/fail0/RO/taint0，
板级自动回旧。暖初值已一致，不声称是冷故障根因。详STOCK-AUDIT-20261001.md。

## 2026-10-01 审计诊断副作用排除

D20（诊断接口）：PMIC启动/实时审计改32项配置白名单，避开ADC2读递增副作用；
CCM39字与AMC由内核owner只读，硬件参数未变。00267暖32项error0、WiFi4/4、
RO/taint0及板级回旧通过。AMC/AIPS/DDR/QoS只有读回候选，未增加写入。

## 2026-10-01 USB原厂初始化遗漏

D21：原先i.MX50 DT无usbmisc；补wrapper OC_DIS、O_PWR_POL=1、OTG AHB gate清位，
K4声明UTMI16。原厂低有效注释与手册相反，按原厂实际写值和旧读回，不改PLLDIV。
00268暖双档STOP/16MiB/USB SSH恢复/RO/taint0/自动回旧通过；冷初值留最终一包。
生效stock-pxp经usb.dts继承，其他未启用host不自动接管。详STOCK-AUDIT-20261001.md。

## 2026-10-01 外设审计隔离诊断

D22（临时诊断）：UART/SPI/I2C正式驱动无诊断补丁；旁置只读模块按绑定owner、
时钟与访问锁读配置白名单。正常stock-pxp硬件参数不变，不自动加载；正式功能
验收先taint0，诊断阶段预期OOT4096。00269两次四个启用控制器读取/卸载/WiFi4/4/
eMMC RO/自动回旧通过；禁用I2C1不访问。PM owner18字共享只读亦暖通过，
没有DDR/QoS/AMC/AIPS候选写入。冷数据及原厂精确U-Boot来源仍依总表边界。

## 2026-10-01 D22 VVIDEO constraint initialization

原厂 mx50_yoshi_pmic_mc13892.c:319–327 的 VVIDEO 2775000/2775000、apply_uV=1
经旧 regulator/core.c:790–802 在注册时调用 set_voltage；reg-mc13892.c:836–860
设 REG_SETTING1[3:2]=1。未启用不等于没有电压初始化。
stock-pxp 新增 vvideo 同值约束，无 boot-on/always-on，无消费者、不打开电源轨。
现代 of_regulator.c:111 设置 apply_uV，core.c:1247 起按实际电压按需设置，
合法已继承值不重复写。00269/DT-only 独立暖测 PMIC31=0001d4（selector1）、
PMIC33=092088（VVIDEOEN bit12=0），WiFi4/4、全eMMC RO/无挂载、taint0，
46.59秒板级自动回旧健康；没有显示或STOP动作。暖态选择码已正确，
本次没有实测错误选择码→正确选择码转换；冷验补同字段，不宣称物理2.775V。
证据 diagnostics/stock-boot-audit-20261001/vvideo-warm；冻结旧冷包未改。

## 2026-10-01 D23 DDR自动低功耗与QoS初始化

原厂postcore init_ddr_settings：QoS CTRL清31:30、CTL22低5位=2→CTL21=00800000→
CTL20低5位=2；Mode4是bit1。现代mach-imx50.c以K4兼容检查在postcore同阶段补齐。
原始冷CTL20/22=0（STAGE-JOINT归档37/42/43），暖2是旧内核初始化继承，不是复位默认。
现代未注册DDR运行时门控，初始化期间内存时钟持续运行；不改父源/分频/训练参数，
不照搬旧框架的enable/disable引用计数。保留CTL20/22其余字段；CTL21按原厂完整写。
00271零起点0/0/0→2/00800000/2、16MiB两次hash、800/160 STOP/64KiB/PLL、
显示请求/WiFi4/4/RO/taint0、50.62秒自动回旧健康通过。测试置零只在RAM暖准备。
冷验要求同路径日志与三字段；实际功耗仍未测，证据见STOCK-AUDIT D23。

## 2026-10-01 D24 AMC/AIPS postcore

原厂cpu.c post_cpu_init顺序为AMC→AIPS→DDR。现代K4-only postcore补AMC
低4位=8（其余保留）、两AIPS MPROT=77777777、OPACR0..3=0、OPACR4高字节清0。
使用标准imx_set_aips，不修改动态IRQ/外设配置；原厂二进制MPROT与参考DCD详
STOCK-BOOT-AUDIT-20261001.md。生效stock-pxp继承树，非新增DT硬件参数。
00272暖AMC8、双AIPS两次内核态读回一致；16MiB SHA、800/160两档STOP、
显示请求成功、WiFi4/4、eMMC RO/no mount、功能taint0。临时模块之后taint4096，
卸载并板级自动回旧健康。未证明冷初值改变，仍列冷必查；诊断不进正式驱动。

## 2026-10-01 包b本轮冷验收结果（当前结论）

冻结00272包、外部DTB、235匹配模块/414服务根，ROM→barebox→6.6 RAM启动。
原始证据：diagnostics/stock-audit-cold-b-20261001；evaluate.py生成result.json，
原运行目录build-k4-v6.6.157/stock-audit-cold-b-20261001-153429-ready。

| 必查项 | 结论 | 冷实测 |
| --- | --- | --- |
| DDR20/21/22、QoS | 通过 | postcore 0/0/0→2/00800000/2，error0；QoS0 |
| AMC/AIPS | 通过 | AMC8；两次MPROT0/1=77777777、OPACR0..4=0 |
| VVIDEO | 通过 | 内核日志2.5→2.775V，SETTING1 bits3:2=1；disabled/users0，不强开 |
| PMIC备用充电 | 通过 | reg13=c00050，COINCHEN/VCOIN=3V；日志2.5→3V |
| PMIC standby两组 | 通过 | reg32=0db60a/33=092088，mask92402/92080完整 |
| PMIC VGEN3 | 通过 | reg30=020fd0，SETTING bit14清0；mode1外部晶体管bit3=1 |
| PMIC reset/极性 | 通过（配置） | reg15=401161，WDIRESET/RESTARTEN=1、STANDBYINV=0；不等于返回机制通过 |
| SW1–4 AUTO | 通过 | reg28=212048/29=000808，各MODE=8 |
| DRM | 通过（配置）；跨返回仍缺证据 | reg13.DRM=1，启动日志确认；本轮自动返回失败，不宣称Off计时验收通过 |
| CCM/ANADIG | 通过 | 39字/clk_summary落盘；UART/ECSPI LP_APM24M、EPDC PLL1/200M/32M、USB OSC24M；MISC0→10000 |
| SRPG | 通过 | ARM/NEON up01020f01→010f0201，down01010101；两档后PSR1 |
| USB wrapper | 通过 | CTRL01000000/PHY080121500/CLKONOFF09800000；PHY100541401继承，与暖不同，不是本批写目标；STOP后USB SSH恢复 |
| 冷WiFi | 通过 | 初次关联/50MHz/网关4/4，双STOP后4/4 |
| 显示 | 通过 | 首次刷新0；最终updates13/error0；冷首次及STOP后相机画面正常 |
| 两档STOP/内存 | 通过 | 800/160两档success2/fail0、DDR/PLL stage4/64KiB；两档后16MiB SHA均OK |
| 临时诊断 | 通过 | 功能先taint0，之后四控制器两次result0，禁用I2C1跳过；卸载成功，最终taint4096 |
| eMMC保护 | 通过 | RAM loop/全部RO/无挂载，首MiB前后SHA相同，无存储写入 |
| 板级自动返回 | **失败** | 请求1000ms兜底+reboot-f，120秒内旧SSH未回；Windows描述符请求失败，需用户长按恢复 |
| 旧系统手动恢复健康 | 通过 | 2.6.31/kexec_loaded0/battery_error0、4199mV/+58mA/99% |

尚缺：AMC/AIPS与部分PMIC写前初值未由冻结代码导出；配置冷结果已通过。
EPDC14项时序在正式init逐项readback比较，成功更新说明检查通过；未额外导出14字raw表。
原始旧RAM区已被旧内核清理；旧dmesg保留STOP尾日志，未出现restart阶段标记，
guard停喂/1秒兜底/WDI实际动作暂缺证据。优先调查返回故障，不用手动恢复替代自动通过。
首次Windows prepare权限失败仅改变包文件owner；冻结内容/哈希未变。
首次15秒USB网络等待未就绪，后续重连取回同一次STOP结果，没有重复发STOP。

## 2026-10-01 冷返回 PWGT 写路径复核

详见 RESTART-COLD-INTERACTION-20261001.md：成功冷返回前34=200000，失败218000；LPC两冷均0。当前唯一POWER MISC写路径为GPO专用provider，最终PWGT来自零初始化软件缓存，非原样回写读值。本轮PMIC/待机/restart/VVIDEO未新增34写。原厂MC13892底层不清PWGT，Yoshi未注册PWGT消费者，尚未找到原厂无条件PWGT00初始化；不得称原厂机制已闭环。未改PWGT策略、未做11模拟、未请求ROM；返回仍FAIL待定位。


## PWGT11单变量暖测结果

同冻结00272镜像，临时模块仅写34:200000→218000，读回严格一致，原始日志set-pwgt11.stdout:1/24。随后33.78s自动返回旧2.6.31，kexec_loaded0/battery_error0、4122mV/-69mA/96%。结果：重启请求前PWGT11不足以复现失败，不据此新增正式PWGT00初始化。注意附件shutdown（k4-accessory-inputs.c:447→267–286）可能经GPO专用ops再次清PWGT；未抓WDI前最后写值，不能宣称保持11至断电的试验已完成。停止该来源假设，回到trace路线。证据diagnostics/restart-pwgt11-warm-20261001；临时模块taint4096为预期。

已离线构建匹配00272的临时restart-trace kprobe模块（源码旁置，未加载/未暖验证），记录mc13xxx_reg_write对34/15/4/18/21/23的实际写值、reg_rmw的mask/value及prepare_notify/1秒timeout/restart_notify/accessory_shutdown/watchdog_shutdown入口；probe不调用SPI、不写PMIC，仅写现有保留RAM trace。下一阶段先在暖态验证probe注册和日志完整性，再用同配置冷复现定位最后阶段；冷复现与依据trace形成的修正版验证合并同一次现场ROM会话。现阶段没有已知正确修正版，不虚构准备完成。必须在返回前重新开启trace，guard状态/硬件timeout也抓取；成功Off可清RAM，缺日志不能算未执行。


## 2026-10-01 冷返回trace包就绪

RESTART-COLD-TRACE-20261001.md：同冻结00272单次暖返回33.61s，立即8192字节RAM读回32连续记录/8阶段PASS。R15=400161；accessory shutdown成功写34=200400，WDI前同值。guard退出/1秒timer本次未触发，条件探针已注册。正式驱动无改动，PWGT因果仍未关闭。冷包k4-stock-audit-cold-20261001-trace与b的内核/DTB/initramfs/barebox/配置/bootargs相同，只旁置trace工具及joint退出保持Y；manifest 2a9e25f176619ae1e141b7b63904f6475bdbeb56b6628ca0c87a71db73e43d50。冷复现待ROM，功能步骤与上轮相同，120秒失败响铃等待人工后立即读RAM。


## 2026-10-01 冷trace复现与三方差分

冷功能/配置再次通过，板级返回120秒FAIL，人工恢复后第一时间8192字节/32连续RAM trace完整读回；旧健康kexec_loaded0/battery_error0。软件完成至WDI_CALL，最后R34=200400/PWGT00、R15=400161、guard退出；未见1秒timer触发，未证明实际断电或上电阶段。上午冷成功对照有8项PMIC配置差异及DDR20/22、SRPG_UP差异；LPC/CBCDR/CLPCR两冷相同。上午WCR/SCR未采，不当作根因。详见RESTART-THREE-WAY-DIFF-20261001.md与diagnostics/restart-cold-trace-20261001；没有正式驱动改动，没有新硬件试验，冻结包不变。


## 2026-10-01 交集更正与WDT冷单变量包（只准备）

候选交集=(冷失败≠上午冷成功)∩(冷失败≠暖成功)。共同静态配置交集为空，PMIC/DDR/SRPG新值均不能单独解释；WCR/SCR/末阶段pad上午未采，不能断言。下一ROM仅WCR.WDT bit3 0→1：3b35→3b3d，其它位不变，trace最终读回；未启动、未请求ROM。新独立包k4-stock-audit-cold-20261001-wdt（manifest 0cf181ee8bff8c59b0aec7d14d309550b7dc5ff6d710188f635a8c7f6614f51f），原00272/DTB/root/barebox/config不变，旁置全量只读诊断及一位临时模块；正式DT fsl,ext-reset-output仅patch/候选DTB未应用，需要验证fallback副作用。细节RESTART-THREE-WAY-DIFF-20261001.md。


## 2026-10-01 新探针暖验通过，CRC双副本包冻结

RESTART-WDT-WARM-CRC-20261001.md：暖单次34.88秒自动回旧，WCR3b3f不写/skipped1/wrote0，WDOG/SRC/GPIO6/IOMUX521及WDI末阶段字段齐全。原RAM7ffff700有64→74单比特旧文本翻转，原始证据保留，主管接受探针通过；CRC/序号双副本7项离线单测（1152bit注入/73部分写边界）及ARM编译通过，不重复上机。新独立包k4-stock-audit-cold-20261001-wdt-crc，manifest f35bb96ff875698782e62903da49afbd2bc924bdae62a7fbd8e8f4116ec4948c，内核/原DTB/root/barebox/config不变；下一ROM仅WDT0→1，未请求。正式ext-reset DT候选未应用。

## 2026-10-01 WDT冷实验仍失败；GPIO/SRC/WDBG分析

1170c7cf6冻结包功能配置17项PASS，WDT3b35→3b3d/XOR8确认，120秒未自动返回、用户长按恢复。8192字节CRC trace 28连续有效，WDI前R34=200400/PWGT00，末阶段WCRff3d；不能证明实际断电或1秒兜底。旧健康正常。剩余候选GPIO6_16原厂非FINKLE输出低（gpio.c:1040–1046）而冷输入；SRC bit0和WDBG机制分别为内部复位类型/DEBUG暂停，均未证明因果。上午缺同阶段GDIR/SRC/WDBG，交集未证实。正式驱动/DT/包不变，仅分析，不请求ROM。详见RESTART-WDT-COLD-RESULT-20261001.md及其原始诊断归档。

## 2026-10-01 GPIO6_16 原厂对齐暖验

原厂mx50_yoshi_gpio.c:1040–1046非FINKLE将UART4_TXD/附件TX改GPIO输出低；DT gpio6 pinctrl+gpio-hog实现mux1/padc4/输出0。旧RAM先清GDIR16（00000020），正式DT初始化恢复00010020、DR16=0；34.91秒自动返回、旧健康通过。其它初始化未改，原00272内核/root；新DT用于本项。跨断电CRC存在缺口，trace完整性不通过，不据此判断新阶段。UART4为附件串口（原厂gpio.c:50；U-Boot board/imx50_yoshi/imx50_yoshi.c:384–393用RX检测串口、986 FINKLE console）；K4实体接线及“为防漏电”的动机无明确源码/原理图证据，仍待证据，不当结论。源与读回见RESTART-ALIGNMENT-20261001.md。

## SRC 原厂依赖的POR默认恢复

原厂U-Boot/内核现有Yoshi路径未发现显式设置SCR bit0；IMX50RM §49.3 p2907 SCR POR=00000d21，bit0默认1。测试barebox arch/arm/mach-imx/src.c:25–31 postcore_platform_driver probe主动清0（匹配imx50.dtsi:331–332兼容imx51-src）；归为加载器策略差异。K4 restart probe在注册handler前通过SRC DT资源仅OR bit0、读回；不改barebox。暖00282 RAM先521→520，正式初始化520→521，34.75秒返回旧系统健康，通过；GPIO已对齐为前批基线，本轮仅新增SRC策略。新包源树含62bfe的等效GPIO改动，构建源标识ee2b dirty如实保留，不冒称clean。

## WDBG/WDT 原厂对齐暖验

原厂drivers/watchdog/mxc_wdt.c:133–140 mxc_wdt_config在probe/启用前写WDBG及WRE(WDT)，头文件mxc_wdt.h:27/29。K4 imx2_wdt probe显式按原厂设置WDBG，并把DT ext-reset-output选定的WDT包含在同一次WCR位更新中，避免write-once位先写造成遗漏；保持timeout/enable/WDA/SRS等其它位，已运行watchdog同样处理。正式watchdog DT纳入fsl,ext-reset-output，原厂配置对齐；该属性同时改变fallback restart选择，不把之前临时OR8实验当属性完整验证。

00283正式包本轮仅新增WDBG/WDT，前两项为已暖验基线。暖态write-once两位已经1，因此probe ff3f→ff3f，运行WCR3b3f/SRC521/GDIR10020/DR08fc1230；34.22秒直接自动返回、旧健康通过。不能宣称暖态覆盖0→1，冷包应检查probe初值→结果及末阶段ff3f。GPIO/SRC/WCR三项都仍需冷联合确认，不把对齐当根因定位。

## 合并冷包已冻结（尚未冷验）

包：$BACKUP/k4-stock-audit-cold-20261001-aligned。manifest SHA256：4052f3d689067d1ddc21711fcd7e7f38ea0b094203a9ba119b3160645471fd13。目录0500/文件0400，全部28个文件哈希通过；zImage/uImage提取一致，三个诊断模块vermagic匹配00283，CRC离线7项复核通过。内核6.6.157-00283-g62bfe028159c-dirty；实际构建source_revision/dirty不重标clean，合并源码提交307963899包括等效正式改动。全部对齐镜像即最后一次34.22秒暖验镜像/root/DTB，不重复构建替换已验证二进制。barebox与旧冻结包字节相同；诊断模块仅旁置，功能后加载。读回helper set_wdt=0、XOR0/wrote0，不再临时写WCR。

下一ROM先用该对齐包冷启动，按原有全部功能/配置门槛验收（DDR三值、AMC/AIPS、VVIDEO、PMIC四组+DRM、CCM/SRPG/USB、显示/Wi-Fi/双档STOP/16MiB/只读存储），随后诊断与CRC arm，再读取WDOG/SRC/IOMUX/GPIO6并板级返回。新增必查：

1. GPIO6_16 mux1/padc4、DR16=0、GDIR16=1；GPIO6全部字段归档。
2. 启动日志stock SRC warm reset记录冷初值→结果，结果bit0=1，其它位不变；返回前SCR bit0仍1，SBMR/SRSR/SISR/SIMR只读保存。
3. stock WDBG/WDT日志初值→结果，WCR bit1/bit3为1，其它位保留；运行WCR通常3b3f，shutdown末阶段通常ff3f。WICR/WMCR/WSR/WRSR全存，不仅核对快照常数。
4. WDI前R34/PWGT、R15及全量末阶段trace；CRC有效副本、序号连续/冲突独立判定。电气Off/On仍没有测量，软件WDI_CALL不等同硬件断电完成。
5. 120秒内回旧为直接路径候选通过，128秒watchdog后备不冒称直接WDI成功；失败按既有人工恢复流程先抢读8192字节。旧健康kexec_loaded0/battery_error0。

当前仅冻结，不请求ROM、不响铃；设备旧系统健康，三次暖测全部结束。若下一冷返回成功，先记“全部对齐冷确认”，是否二分取决于是否需要具体因果。失败保留交互/硬件状态问题，不继续猜PWGT/WDT单因。GPIO实接/拉低防漏电动机仍无原理图证据，不能关闭该物理解释缺口。

## 2026-10-01 aligned冷启动watchdog门槛失败与非致命修正

0227230c9 aligned的ROM/barebox/外部FDT通过，但新USB未出现；并非6.6没运行：旧保存区有INIT_REACHED/COMPOSITE_PROBE_INIT/DIRECT_ROOT_INIT/WATCHDOG_FAILED，USB前rcS已退出。冷功能/配置与返回都未执行，不沿用上一00272冷通过作为本包结论。8192字节已抢读、CRC probe未加载无有效记录；旧健康正常，用户手动恢复。

最可能是307963899 strict WDBG读回：barebox WCR首写将WDBG锁0，内核不能改1，strict mask检查阻止watchdog注册。此推导有手册与源码+实际失败标记，但没有本轮probe原始stderr/寄存器读回，不冒称实测-EIO。WDBG（首次写锁定）和WDT（write-one-once）不可混同。WDBG0正式归引导链差异；新policy仅观察/告警，不写WDBG；WDT仅0→1，读写/读回错误都warning且继续注册。安全兜底优先于对齐。

266实际C函数故障注入/ASan/UBSan通过；新00286暖正常guard+USB、WCR3b3f/SRC521/GDIR10020/DR bit16=0、34.66秒自动回旧/健康。WDBG冷锁0与真实冷WDT转换仍未上机，只以故障模型覆盖，不改barebox、不请求ROM。详细RESTART-ALIGNED-COLD-BOOT-FAILURE-20261001.md。所有新源码/文档LF；原始串口/RAM证据字节不改。

## 2026-10-01 新aligned-safe冷包冻结（替代失败aligned）

正式修正859c0d972，暖34.66秒自动回旧及guard/USB/只读根检查通过，actual C 266个故障场景通过。新包$BACKUP/k4-stock-audit-cold-20261001-aligned-safe；manifest SHA256 5f0d2bfb67ba6df892223f03e5abd4d0929e42643a132904ef26f45234d7ae3f。00286-g0227230c91d8-dirty，保留实际暖验dirty来源、不重新标clean；source policy revision859c0d972。28文件全部hash复核，uImage提取=zImage，三个旁置诊断模块vermagic匹配；CRC7项离线通过。目录0500/文件0400。失败aligned保持冻结为历史，不再用于下一验收。

新增状态：GPIO6_16和SRC bit0=已修已暖验待冷确认；WDBG0=引导链差异（barebox首次WCR写锁0），不强求1；WDT=正式0→1与错误非致命处理已修已暖验/故障注入待冷确认。前版strict读回导致watchdog缺失的推断证据与缺口详见RESTART-ALIGNED-COLD-BOOT-FAILURE-20261001.md。

下一ROM先用新包，必须先看到watchdog0正常注册、900/30 guard与USB就绪：允许cold WDBG0 warning，WCR运行通常3b3d/末阶段ff3d；WDT bit3=1读回记对齐结果，失败必须只warning且watchdog/guard仍存在，不把对齐失败升级为安全兜底缺失。严禁沿用旧清单要求cold WDBG=1/ff3f。GPIO6_16输出低/mux1/padc4及SRC bit0=1仍必查。随后同套DDR/AMC/AIPS/VVIDEO/PMIC四组+DRM/CCM/SRPG/USB、显示/Wi-Fi、两档STOP/16MiB、只读保护，再加载诊断、CRC arm、纯读回/XOR0/wrote0、板级返回及120秒观察/抢读RAM。

本轮cold功能、对齐读回和返回均未执行，结论=尚缺本包冷证据；不把初始化watchdog门槛失败当板级返回失败。新包尚未冷启动，不请求ROM、不响铃、设备旧系统健康，没有运行中测试/监听。所有仓库新源码/文档LF，原始RAM/串口证据字节保留。

## 2026-10-02 离线封包/用户态源码核验/公共文档

正式内核配置、DTS与硬件参数不变；阶段4 production冷包及无显示消费者额外测试profile已冻结（dee55f9e3），后者不替代正式显示配置、仍待硬件验。用户态配方b897cae90仅在仓库外重建：3个ELF exact、4个仅build-id不同，regdb2项exact；未替换任何原RAM根二进制/guard/health/bootstrap/存储保护。公共草稿project/docs记录原厂参数基线与既有验证边界；schema、ZQ重复、低电门槛与boot1仍另排。本轮没有设备操作，不增加冷验证结论。

## 阶段5（2026-10-02）显示内部边界

db1912a52/e8df39fb5仅组合EPDC后端与provider module/device引用；正式Papyrus/PxP/EPDC/fb仍y，全部硬件/波形/电源/时钟参数不变，DTB精确同阶段2/4。y/m/n及实际C故障模型通过，56根非模块文件同阶段4；显示冷包独立冻结，需stage4先通过再验。m服务无exit，故障DMA不释放；诊断温度仍仅debug。未增加设备验证结论。

## 2026-10-02 阶段6/7离线结论（无新增硬件偏离）

阶段6六项真实树外构建/modpost通过，仅源码ABI评估，不安装/改变正式默认；charger/restart/PM/基础clock/恢复USB内建。阶段7纯binding类型描述修正，正式DTS数值未改，137节点705属性/五类硬件项与原冷验精确一致，DTB SHA c8bd73f...；K4专项schema通过，全量尚缺上游CCM IRQ编码对TZIC一cell的校正证据，不以放宽schema掩盖。两次clean公共patch production的zImage与stage5冻结同e554228c...，234模块及内外RAM逐字节复现；新外部recipe仅opt-in ext3元数据固定，旧冻结包不动，56内层非模块+24外层保护项字节不变。默认显示y，stage5生命周期变化仍待依赖stage4的冷联合；树外/m/新诊断标记仅离线证据，不扩大硬件接受范围。见STAGE6、STAGE7与COLD-QUEUE。

## 2026-10-02 CCM IRQ编码独立修正（a339290ae）

原厂CCM物理请求71/72；上游imx50.dtsi误用GIC三元组，在TZIC一cell父控制器下声明为六个请求。正式K4外部DTB仅此属性改为71/72两cell，非频率/供电/时序策略变更；clock驱动不申请CCM IRQ。其它137节点705属性及五类硬件参数全等、zImage精确不变，完整K4 schema可匹配项错误0。阶段4/5原包不动，独立CCM包排第三轮冷验：IRQ无新handler、clock/cpufreq/显示/Wi-Fi/STOP/板级返回仍待确认。完整证据CCM-INTERRUPTS-FIX-20261002.md；legacy YAML未覆盖提示及其它上游binding元诊断不隐去。

## 2026-10-02 A 正式 trace 清理（22bf2b583 / 870945c35）

硬件参数与正式 DTS/config 无变化；现代实现将纯 debug hook 移入 overlay。生产 ARM/host/预处理等价通过；debug 恢复40个文件精确原字节。PxP存在单个比较寄存器分配差异，严格仅行号门槛未通过，不据此宣布免冷；见 MODULARIZATION-DEBUG-CLEANUP.md。原厂审计读回结论及冻结包保持原状。

## 2026-10-02 阶段4冷功能证据与返回缺口

未改硬件参数/正式DTS/冻结载荷。fresh production DDR初始化2/00800000/2、SRC521、WDT置1与SRPG等读回/两档STOP/显示/Wi-Fi通过；完整PMIC/AIPS快照在kexec lifecycle功能后取得，非冷启动即时/WDI前快照。panel与五向模块生命周期、电源键STOP通过。最终kexec后第二6.6板级返回120秒未回旧，USB描述符失败；用户操作造成一次旧启动覆盖残留，不算延迟自动恢复。原厂对齐结论不因此回退；恢复路径/kexec交互缺口仍待debug证据。EVBUG自动coldplug违反正式诊断隔离，未来配置清理解决，不改已冻结包。详MODULARIZATION-STAGE4-COLD-RESULT-20261002.md。

阶段5会话2补充：fresh ROM原23/8包，冷功能/原厂参数与两档STOP通过；不经kexec直接板级返回35.72秒回旧、旧健康通过。diag audit功能后卸载，EVBUG仍为正式隔离缺口。硬件参数无改，阶段4kexec返回失败保留，不能仅凭不同profile对照定因果。详MODULARIZATION-STAGE5-COLD-RESULT-20261002.md。

CCM会话3补充：仅IRQ属性6cell→2cell，冷IRQ/clock/CPU/显示/Wi-Fi/两档STOP与原厂参数读回通过；fresh直接板级返回121.91s未恢复，不判总体冷通过。stage5与本轮功能后106字段除禁用RTC闹钟值全等，PWGT00/WCR3b3d/SRC521/GPIO-pad相同；缺prepare/WDI阶段trace。人工旧健康通过，无持久写入。kexec不构成所有失败必要条件，未执行后续因果对照，不改原厂参数。详CCM-INTERRUPTS-COLD-RESULT-20261002.md。


## 2026-10-02 boot1 barebox 离线候选（尚未完成移植）

原厂：boot0 SPL/main U-Boot、动态ZQ、主U-Boot 3400/3600mV门槛，当前179=48/177=00。候选：独立D01100 barebox内置DT，USB主机RAM加载，DDR/DCD与已验USB 23/8逐字节一致；CTL20/21/22仍由后续6.6设置mode4，不添加DCD写。SRC清bit0/WMCR处理沿用USB上游，新增120秒watchdog poller、关闭存储自动探测/idme读取、只允许显式179→48救援，均属接口/引导策略差异，不调整DDR硬件参数。

ARM构建/结构比对及host测试通过；但DCD1108字节违反IMX50RM Table6-22的eMMC1024字节限制，尾0x880超过按文件基址的2KiB初始窗口，阻断部署。不是已验eMMC一级引导，屏幕标记未实现，USB/OCRAM/poller/卡探测/冷启动/返回/低电均未设备验证。本轮无设备访问、无存储写；写入草案以ROM门槛拒绝此候选。详情与后续风险见 [barebox-emmc/README.md](barebox-emmc/README.md)。

## 2026-10-02 boot1 barebox OCRAM plugin 离线候选

原厂双IVT/DCD0/ROM copy helper作为入口基线；现代实现为OCRAM软件表解释器再进入独立barebox PBL，无设备树参数变化。全部132条写入及3个CHECK与冻结USB DCD同值同序，ZQ23/8，PLL1/DDR pad/时钟不改。原DCD1108超限，即使乐观移出9条仍1036，因此没有实际移动任何写入；软件轮询有界及额外DSB是实现变化。6组plugin主机检查、7组草案及boot0命令1802场景通过，未执行ARM/设备。低电门槛绕过、reset返回barebox、ROM helper/双IVT冷启动/新主体位置/WDT/CTL20..22 mode4/屏幕均待验；详见barebox-emmc/OCRAM-PLUGIN.md。

## 2026-10-02 boot1 barebox 去除额外存储限制

本条替代前轮救援白名单/双记录策略。删除k4_boot0、boot0-policy和相关测试，所有上游非Kindle板级代码原样（包括MCI）；恢复冻结USB配置的MCI_WRITE/ERASE/BOOT_PARTITIONS能力。默认MCI_STARTUP_NONE=y（真实Kconfig choice）、STARTUP/NONREMOVABLE=n，ENV_HANDLING=n，移除板级自动探卡/idme及原厂mmc启动脚本。6.6外部DTB静态板型不依赖原厂自定义ATAG；Wi-Fi MAC来自AR6003 WMI READY，固件最终种子OTP/board data仍待冷验证。OCRAM只留一份12字记录，无CRC/反码/副本。备份精简为单份完整EXT_CSD/boot1并校验，写后全区域比对，最后用标准mmc命令只改179；回退亦只改179。DDR/ZQ23/8/时钟pad原值原序不变，板级及DT硬件参数不变。产物out/boot1-plugin-v4/barebox-boot1-plugin-candidate.img，258048字节，SHA256 68e70fa2213cfe22ddd2ee7d6556d2c076632e39c6bafa4964bac4a62b401321。12组主机检查、通用代码全文件比对与ARM构建通过，无设备操作；ROM helper/双IVT/冷DDR/WDT/CTL20..22/USB等待/冷Wi-Fi MAC/低电/屏幕待验。详见barebox-emmc/README.md和DEPLOYMENT-DRAFT.md。

## 2026-10-02 boot1草案验收小修：设备名、维护工具与软件RO

依据设备侧78c241362，6.6 eMMC为mmcblk2/boot0/boot1（旧内核mmcblk0不适用）。正式RAM块根bootstrap对所有MMC节点BLKROSET；force_ro只改GD_READ_ONLY，不能清bd_read_only。镜像写入草案只对mmcblk2boot1临时解除/恢复两层RO；boot0不解锁。标准mmc-utils v1.0静态armhf独立维护包构建完成，不进入production RAM根，不改工具源码。按用户最终决定，179操作采用主设备标准流程：blockdev --setrw mmcblk2 → mmc extcsd write 179 50/48 mmcblk2 → mmc extcsd read核对 → blockdev --setro mmcblk2；仅CMD6配置写，不发扇区写。不通过boot1发179 ioctl。写后179=48读回足够，不额外重启boot0。14组主机测试通过（含标准命令成功/写失败/读回错误均恢复RO）；本轮无设备操作，barebox镜像/硬件参数均未变。维护包SHA256 9964c865829a55bc4c192f12099bb6099986fda29b1fb9e364491439742a9ef4；详情project/userspace/MAINTENANCE.md、porting/barebox-emmc/DEPLOYMENT-DRAFT.md。

## 2026-10-02 boot1最终交付路径统一v4

仅从clean-v3主体重新生成out/boot1-plugin-v4/barebox-boot1-plugin-candidate.img，DCD0，258048字节，SHA256 68e70fa2213cfe22ddd2ee7d6556d2c076632e39c6bafa4964bac4a62b401321。clean主体0x1000起与v4的0x4000起240836字节逐字节一致，SHA均0c6247f7e1e8839d1bb6e093ec0ac7dcb3852b08e181b8fd4ed2e2e834327762。MCI为上游原样，镜像字串/主体ELF无k4_boot0；132 WRITE+3 CHECK与USB同值同序，2KiB头窗口与1MiB尺寸检查通过，14组host测试通过。v1–v3及clean中间candidate/旧SHA清单改名.OBSOLETE防误用。硬件/DDR/DT参数未变，未执行设备操作；设备验证缺口不变。

## 2026-10-02 boot1部署检查点A：新增只读结论

v4候选尚未写入或激活，原厂/当前PARTITION_CONFIG仍48、BOOT_BUS_WIDTH00，硬件写保护173/174与BOOT_CONFIG_PROT178均00。会话4production外部DTB与DDR/时钟参数原字节未改。完整1MiB boot1全零、512B EXT_CSD读boot1前后全等，三方本地备份SHA一致；所有软件RO仍1。独立维护包只使用CMD8只读工具。步骤3–5与eMMC冷启动仍未验证，按用户检查点A停止等待确认。详barebox-emmc/CHECKPOINT-A-20261002.md与脱敏JSON；原始备份不入Git。

## 2026-10-02 boot1 部署检查点 B：EXT_CSD 比较异常停止

用户确认 A 后单次写入 v4 到 boot1，完整1MiB读回匹配，force_ro/BLKROGET 恢复1/1。原厂与当前 PARTITION_CONFIG 仍48、BOOT_BUS_WIDTH00，硬件保护参数未改；唯一 EXT_CSD 差异为 [245:242] 编程扇区计数0→504（实际变化字节242/243）。按用户任何不符停止，未激活179，未重试。冻结会话4 production DTB/DDR/时钟参数不变。eMMC冷启动仍未验证，详 barebox-emmc/CHECKPOINT-B-20261002.md；原始数据仅本地。

## 2026-10-02 boot1部署更正：B通过，冷启动尚未测试

主管确认计数器[245:242]0→504属预期，B通过。获授权后仅EXT_CSD179从原48改50，标准工具读回与所有软件RO恢复通过，除179/计数器外完整EXT_CSD不变；177/硬件保护与冻结production DTB/DDR/时钟参数未改。用户未执行21:37冷复位，原60秒COM10不消失的记录为NOT_TESTED，不能记boot1启动失败。当前按用户确认保持ROM、17950，未回退；USB恢复镜像尝试不算boot1验收。只准备离线脚本与ROM前置取证顺序，冷启动/DDR/plugin/MAC仍待实测，详barebox-emmc/NEXT-COLD-RUN-20261002.md。

## 2026-10-02 boot1冷启动未见USB，179已回退

用户在场本轮180秒未见boot1 barebox；人工下键ROM后先SDP只读取证，再普通USB冻结包恢复6.6 RAM。未见有效barebox/plugin magic，失败阶段仍未定，不能宣称DDR/ROM helper原生验收通过。仅单次CMD6恢复17950→48，回退完整512B EXT_CSD与A原备份SHA完全一致；177/硬件保护未变，boot1仍是原批准v4，完整1MiB SHA与B一致。所有mmc节点RO1、boot1两层RO1/1，恢复系统MAC与A一致。原生CTL20/21/22/ZQ/SRC/WDT验收未完成；冻结production DTB/硬件参数无修改。详barebox-emmc/COLD-BOOT-RESULT-20261002.md与脱敏JSON，原始日志/备份只在本地，不push。


## 2026-10-02 boot1 v5离线修正

v4实机失败，179回退48、EXT_CSD原样、boot1仍v4。v5恢复原厂首头44字节/2KiB/plugin入口f8006004及ROM栈返回协议；第二段直接进入DDR barebox而非原厂OCRAM SPL，是独立一级引导必要差异。完整132写/3检查仍与USB同值同序同宽度、ZQ23/8；主体SRC/WDT原样，CTL20/21/22无新增写，硬件DT/时钟/电源参数不变。21组host检查通过，含实际ARM指令的模拟控制流/寄存器恢复；未设备/RAM测试，不证明真实ROM helper或冷启动。取证在人工ROM复位后，无magic不能证明之前未执行。详见porting/barebox-emmc/V5-QUICK-REPORT.md；v4停止部署，无新防御或总线参数变更。

## 2026-10-02 boot1 v5原生冷启动通过（单次）

原启动选择48经用户授权改50，177/硬件保护不变，仅boot1前480扇区单次覆盖v5、保留旧尾部。完整读回SHA8d3f26a1…63c2匹配。真实电源长按复位后约2.374秒出现barebox，OCRAM barebox2/plugin4、CTL20/21/22=0/0/0、ZQ817、SRC520/3820207c/0。进入冻结production后既有DDR策略2/00800000/2、ZQ817、SRC521/3820207c/0、MAC一致、17950、全部RO与guard/health/taint0通过；没有修改production DTB/硬件参数。

候选OCRAM所谓WDT字段实际读GPIO5，不能算WDT；正确WDOG1地址53f98000，Linux只读WCR3b3d/WRSR0010/WMCR0及active/timeout30/nowayout1通过。原生启动前真正WDT未抓，保留缺口、不修改冻结候选，纠正前轮按错误源地址得出的WDT结论。仅一个冷样本，重复/长期/完整断电与自动Linux加载未验。详barebox-emmc/V5-COLD-RESULT-20261002.md与脱敏JSON。

## 2026-10-02 v5重复正常板级restart：5/5

五轮kernel reboot经既有板级restart返回boot1 barebox，再YMODEM外部DTB启动同一冻结production。耗时5.640/6.140/6.750/5.610/6.265秒；OCRAM2/plugin4、正确地址实际WDOG1前置读数、每轮DDR2/00800000/2/ZQ817、MAC、guard/health/taint0、存储RO与17950通过。没有修改原厂硬件参数、177/硬件保护/DTB、没有存储或EXT_CSD写入。候选WDT字段误采GPIO5仍保留缺陷，用另行真实WDOG1读数验收；主机串口就绪竞态第2轮同启动恢复，无额外reboot。只验五个正常restart样本，长期/完全掉电未验。详barebox-emmc/V5-REPEAT-RESULT-20261002.md与脱敏JSON。

## 2026-10-02 boot1 v6 离线诊断地址修正

原厂 i.MX50 WDT1 基址 0x53f98000，WCR/WSR/WRSR 为16位、偏移0/2/4；当前 v6 候选恢复此读取，v5 的 GPIO5 读取不可作为WDT证据。生效 Linux DTS 不变；没有硬件配置偏离，仅诊断接口修正，WDT策略和132/3初始化序列不变。源码/配置/运行对象与7项plugin离线核验通过，见 barebox-emmc/V6-OFFLINE.md；未部署、未做v6冷启动，设备仍为v5。

## 2026-10-02 关闭历史试验策略待办

ZQ8/4四轮、返回旧boot0不稳定排查、3400/3600mV软件放行门槛按当前用户任务关闭，原因与证据见RESUME/队列最新关闭表。当前boot1仍v5、ZQ23/8，Linux生效DTS和硬件参数无变化。低电软件策略不实现，依据用户决定及MC13892硬件充电不依赖CPU运行；不是新增低电实测结论。历史返回失败不宣称已定位，保留ROM/179回退说明。

## 2026-10-02 offline emmc-root profile

- Original/current RAM maintenance: ext3 nested RAM root, all eMMC RO, finite test guard. New opt-in emmc-root: unchanged p1 boundary, ext4 rw kernel root, /boot files on p1, BusyBox continuous watchdog (30s/10s), ordinary sync/remount-ro shutdown. User explicitly selected removal of old p1 system; USB ROM recovery remains.
- Hardware clock/power/timing parameters and effective production imx50-kindle-k4.dtb unchanged. Modern filesystem/init policy only; add CONFIG_EXT4_FS=y to k4_defconfig because ext4 was absent, retain builtin MMC/eSDHC/devtmpfs. No display clock/PLL or watchdog hardware change.
- Basis: survey commit 4b90d5c65, Linux init/do_mounts.c, hashed accepted RAM recipe, source-built static maintenance mke2fs. No device, frozen-package or barebox worktree modifications. Host build/results tracked in EMMC-ROOT.md and EMMC-ROOT-RESULT.json; cold RW root, ARM mkfs, reboot/recovery and service hardware verification remain pending.

- 本轮按用户CPU占用要求暂停：production/21模块/modpost通过；debug overlay与emmc-root构建未完成，不判三profile通过。15host测试、真实RAM配方tar复现与文件SHA、host普通文件mkfs/e2fsck通过。静态ARM mke2fs仅ELF验证，未运行设备。接续见RESUME顶节/EMMC-ROOT-RESULT.json。

## 2026-10-03 eMMC-root resume correction

- Correct prior statement that ext4 was absent: Linux 6.6 fs/ext4/Kconfig EXT3_FS selects EXT4_FS. The original defconfig already resolved EXT4_FS=y; remove the redundant explicit line added in f4356e164. No effective config or hardware parameter change.
- Align payload DTB path to barebox v7 /boot/imx50-kindle-k4.dtb (previous candidate /boot/k4.dtb superseded). emmc-root uses production release/config/DTB; root rw/user watchdog policy remains separate from unchanged RAM RO maintenance. Read-only v7 contract inspection at 5811e0f4d; final host results recorded below when complete.

- 2026-10-03 完成：production两次clean共63项逐字节一致；debug/emmc-root及modpost、15host tests、最终tar复现/校验/模板权限/v7路径通过。production/emmc内核/DTB/模块字节相同，有效原defconfig及RAM只读流程不变。来源与结果见EMMC-ROOT-RESULT.json。ARM mkfs、rw冷根/服务/reboot/ROM恢复和保留区未动仍待设备验证；无设备操作。
## barebox v7 离线自动启动（2026-10-02）

原厂通过其启动布局加载旧内核；v6 barebox 不探卡、只等待 USB 上传。v7 保持 v5/v6 DDR plugin、频率/分频/电源/初始化表和 v6 WDT 读址，只恢复上游 MCI_STARTUP_NONREMOVABLE 正常 eMMC 探测（接受 HS/总线宽度切换），保留 ext4=y、持久环境=n，新增两秒“上”键采样及 /dev/mmc2.0 /boot/zImage + 可变量 DTB 的标准 boot 脚本。生效 barebox DT 仍为上游 imx50-kindle-d01100.dts，Linux 外部 DTB 默认 /boot/imx50-kindle-k4.dtb，最终名称由根文件系统任务确定。命令行 console=ttymxc0,115200 root=/dev/mmcblk2p1 rw rootwait watchdog.open_timeout=120 imx2_wdt.nowayout=1 ath6kl_sdio.force_virtual_scatter=0 fbcon=map:1 logo.nologo。布局/参数偏离属于用户选择的现代 Linux ext4 根与文件启动实现，不改变 DDR 硬件参数；CMD_SLEEP=y 仅为按键窗口提供 msleep，不是永久硬件限制。

v6 SHA 完全重现；v7 首44字节、第一IVT44字节及4KiB前缀与v5/v6相同，132 WRITE/3 CHECK同值同序；全源码树仅3个默认环境脚本变化，上游通用代码不变。7项plugin及7个命令桩脚本场景通过，未执行设备验证、写入或push。eMMC冷探测/实际ext4读取/按键/USB回落/6.6 rw根启动待验。细节与产物SHA见 porting/barebox-emmc/V7-OFFLINE.md。

主管验收修正：v7 恢复 production 的 watchdog.open_timeout=120、imx2_wdt.nowayout=1、ath6kl_sdio.force_virtual_scatter=0、fbcon=map:1、logo.nologo，仅去掉 RAM 专用参数并使用 eMMC rw 根。参数源为用户提供的会话4 boot-ram.barebox；未改变硬件/DT配置。增量重建后新旧v7的4KiB前缀一致，plugin序列与v5/v6一致，7项plugin和7个脚本分支通过，完整bootargs已核对；设备效果待验。

## 2026-10-03 看门狗ROM回落离线调查（未应用/未实机）

最后一轮guard900/timeout30，WCR3b3d已经WDT=1；23:10:14仍Linux，00:25已ROM，中间没有连续观测，停喂/ROM首次出现不可精确确认，eMMC残留HS/宽总线为待验假说。原厂WDOG pad ALT2/open-drain0x0c，正常WDIRESET=1走Cold Start不经过Off；主动reboot另走RTC+5秒/WDIRESET0/GPIO低。当前common.dtsi ext-reset-output已开，restart watchdog state ALT2/pad4但无default，仅继承loader，最后一轮实际mux未采。

本分支仅porting草案：A默认接管ALT2/pad0x0c恢复原厂；B默认ALT0 WDOG1_WDOG_B/pad0x0c，用RM定义的超时保持到POR输出，是需验证的路由偏离。两者二选一，未改生效DT/驱动/设备；git apply --check各自通过，无构建/上机。既有restart同一pinctrl owner在prepare切GPIO，rollback回watchdog，默认接管改变probe前保持loader的策略；GPIO接管后硬件外部输出被屏蔽的窗口仍存在。Cold Start不证明eMMC实际断电。boot1 barebox无法修复发生在ROM读镜像之前的失败，不新增防御性eMMC reset。完整证据/时间范围/现场验证步骤见WDOG-RESET-RESEARCH-20261003.md。

## 2026-10-03 方案A已实现/production离线构建通过，实机待验

生效候选DT：imx50-kindle-k4.dtb的common fragment；正常WDI明确default/watchdog ALT2 WDOG1_WDOG_RST_B_DEB，pad由原0x04恢复原厂open-drain0x0c；reset GPIO ALT1/pad0x04保持。原厂mc13892_regulator_init由pmic_core_spi probe的plat_data->init调用，设置PC2.WDIRESET=1/RESTARTEN=1后注册子设备；当前MFD common_init已在父probe/子设备之前设置，本次仅补源码出处注释，没有新增写入或防御逻辑。restart SYS_RESTART且非kexec才写WDIRESET0/改GPIO，既有restart/watchdog源码逐字节未变。

production k4_defconfig .config SHA7660ae45…db07与当前eMMC production逐字节相同；184.546秒构建成功，zImage SHA c9ffb8e8…00e83也与现有production逐字节相同。候选DTB SHA8960edb8…c0cdc仅4项WDI pinctrl属性变化，其余节点/保留内存不变；binding文档及restart节点schema通过。无设备操作/实拍/USB观察/实机结论，不将构建作为超时PMIC或eMMC验收。步骤按v7同bootargs直接root=/dev/mmcblk2p1 rw rootwait，kexec候选后确认mux2/padc/WDT/PC2，SIGSTOP唯一BusyBox watchdog，观察20–30秒超时后经boot1/v7回eMMC。详WDOG-STOCK-A-TEST-20261003.md与WDOG-STOCK-A-BUILD-20261003.json。

## 2026-10-03 公开草案离线同步

同步既有403751dd9验收：生效production common DTS WDI正常/watchdog ALT2/0x0c（原厂方案A），reset保持GPIO；ATH6KL/SDIO=m是根挂载后加载固件的现代接口变化，不改变无线硬件参数；boot1 v7 ext4自动启动和持续watchdog eMMC根为启动/用户态策略。依据46986d082、492abb090及EMMC-DEPLOY-STABILITY-20261003.md。既有10轮reboot、两档STOP、文件读回通过；拔线启动/长时/电源轨与历史ROM根因仍缺。本次只文档与公开配方同步，无新增设备验证。

## 2026-10-03 barebox v8 USB逃生候选（离线）

原厂/ROM：EIM_EB1同时是BOOT_CFG3[4]；eSDHC3端口选择10在复位时按上可能变成11/eSDHC4。v7 boot/emmc以GPIO1_20高有效20次×100ms采样作逃生入口；barebox生效DTS为imx50-kindle-d01100.dts，pad0xc0（100kΩ下拉），Linux原厂对应换算0xc4仅DSE不同。

v8不再采样方向键，在USB serial注册后用已有sleep命令等待5秒，主机可在设备重启前启动循环，在CDC ACM重枚举后反复发送0x03，命中后停止发送；Ctrl-C转既有host-ram/shell；默认启动增加5秒。属于启动入口策略变化，不是硬件配置或现代内核接口变更。没有修改DTS、pad、PMIC、电源、时钟、DDR、plugin或内核；不是恢复原厂产品UI。偏离必要性与RM/代码证据、替代按键评估见barebox-emmc/V8-OFFLINE.md。

离线验证：v7重建SHA吻合，v8整个4KiB首段与v7字节一致，config不变、仅两环境脚本变化；7个ARM plugin检查和5个shell分支通过。无设备操作/部署；USB枚举延迟、真实Ctrl-C/回落、YMODEM和冷/暖启动待验。v7前两次精确根因未定位；第三次strap解释有手册依据但缺现场ROM快照，不写成已证明根因。

## 2026-10-03 barebox v8 Ctrl-C入口实机验证

原厂硬件/DDR/plugin与既有barebox配置无变化；用户授权启动策略将v7复位方向键两秒采样替换为USB控制台sleep5/Ctrl-C中断，避免在ROM采样前要求操作strap。依据本地源码与V8-OFFLINE.md；这是现代boot脚本入口策略，不是硬件参数修改。有效LinuxDTB仍方案A8960edb8bdec2d216080b0f6dee682f38fd69b45f663062d539afc4a93bc0cdc，WDI原厂ALT2/pad0xc读回通过。boot1写前备份/写后全块比对、只读恢复、179=0x50及其他非计数器EXT_CSD字节不变；正常启动、Ctrl-C/YMODEM维护RAM/guard前主动退出、三轮回归健康通过。v8到SSH28.219–28.781秒，净等待相对v7可能约+3秒（sleep5替换旧2秒）。未测冷启动、窗口边缘、回滚、长时；未写boot0/idme/fuse或部署p1。详barebox-emmc/V8-DEVICE-RESULT-20261003.md。
## 2026-10-03 Alpine armv7 offline userspace

- 原厂用户态/当前已选 BusyBox 根与新 Alpine3.24.2 候选的差异是 musl、apk、OpenRC和标准软件包接口；不是硬件参数变更。有效 production imx50-kindle-k4.dtb SHA e0aa481e1c857441a62578b5c5570bd95fca08d23254f53949c7554377b67486，内核/21模块/所有时钟、分频、电源和初始化硬件参数保持已有 production 值；采用Alpine依据为用户明确选择。
- 持久候选保持 root=/dev/mmcblk2p1 ext4 rw、原USB RNDIS/ACM配置、480000uA充电用户态请求及连续30s/10s watchdog。OpenRC监督服务，关机停止充电后sync/remount-ro；包自带fsck/networking/wpa/dropbear服务未重复启用。保留K4修复版wpa2.12及现有coldplug/显示/按键工具。
- RAM候选是临时试验策略：无p1挂载、原setro/readback入口、既有有限guard600s/30s；不新增硬件限制或调频/显示时钟策略。
- 74包签名/APKINDEX、314ELF/203动态依赖、21模块release/字节、服务声明图、tar/newc归档与双次复现离线通过；regdb CMS通过。未访问设备、未实测PID1/USB/Wi-Fi/显示/按键/关机/p1冷启动。证据与剩余缺口见ALPINE-ROOT.md、ALPINE-ROOT-RESULT.json。

## 2026-10-03 Alpine supplicant来源整改（最终方向）


## 2026-10-03 Alpine RAM 实机验证

仅用户态RAM试验，无新硬件参数偏离。有效外部DTB为已部署方案A（8960edb8bdec2d216080b0f6dee682f38fd69b45f663062d539afc4a93bc0cdc），沿用原厂WDI ALT2/open-drain0x0c；内核为当前ath6kl=m版5c666c72ad08914c1883b76d03bd5e1bcf40046f1a5155ee58229b1575419291，匹配23模块。600秒/30秒guard属于临时RAM策略，119.75秒主动退出，未到期。OpenRC/USB/无线/显示/本地APK来源查询通过；RAM中eMMC全只读未挂载，没有p1/boot区/EXT_CSD部署。结束eMMC读回WDI2/0xc，持续watchdog正常；Alpine内MMIO读回有缺口。持久Alpine根仍旧21模块交付，冷启动/长时/休眠待验，暂不建议替换p1。详见ALPINE-RAM-TRIAL-20261003.md。

## 2026-10-03 Alpine 持久根离线修正

| 范畴 | 原厂/现有 | Alpine当前交付 | 必要性、依据和验证 |
| --- | --- | --- | --- |
| 时间用户态策略 | 原厂system hwclock -u -s、halt/reboot -u -w；BusyBox eMMC未显式读写 | 官方OpenRC hwclock UTC、rtc0显式启动读/正常关机写；adjfile关闭 | 恢复原厂；原厂镜像debugfs只读脚本证据、RTC文档与当前DT aliases；脚本/依赖/帮助离线通过，RTC ioctl/关机回写待实机 |
| RTC硬件参数 | SRTC rtc0，PMIC rtc1，DRM=1保持CKIL | 不变，方案A production DTB | 不写PMIC RTC、不改DRM/时钟/闹钟；DRM不保证正确日历 |
| 网络校时策略 | 原厂闭源服务未作穷尽断言；现BusyBox无ntpd | 可选BusyBox ntpd默认启用，pool.ntp.org | RAM日历1970会妨碍TLS，RTC源不能凭空纠正；同一已有applet，无额外包/日期兜底/TLS放宽；用户态help/服务图通过，实际NTP/TLS待验 |
| 模块/交付接口 | 原Alpine 21模块、旧内核DTB；当前eMMC ath6kl=m/23模块 | 当前5c666c...内核、8960ed...DTB、23模块SHA锁 | 对齐11184ce40部署记录和RAM逐模块证据；全部SHA/vermagic与两次构建通过，冷启动待验 |
| watchdog/存储策略 | BusyBox eMMC常规30秒/10秒、p1 ext4 rw | 相同，无RAM guard/probe；mmcblk2p1 | 现代OpenRC接口，不是新硬件配置；tar/脚本离线通过，实际部署/回退待验 |
| coldplug诊断 | generic alias扫描有无匹配告警 | 保持扫描/日志，10类归因见交付文档 | 未发现必须补的模块，不增假alias/永久限制；必要无线/显示为原RAM实测，新持久镜像未上机 |

生效DTB：/boot/imx50-kindle-k4.dtb，SHA256
8960edb8bdec2d216080b0f6dee682f38fd69b45f663062d539afc4a93bc0cdc；
从11184ce40源码离线重建同字节。没有设备或另一会话目录访问。
完整来源、原厂与BusyBox差异、精确交付SHA/回退和剩余缺口：
[ALPINE-PREDEPLOY-20261003.md](ALPINE-PREDEPLOY-20261003.md)。

部署脚本现代接口修正：维护挂载点/tmp、mountinfo检查/dev/root别名、显式拒绝已挂载eMMC，
修复 ! grep 与 set -e 组合不退出；3项临时目录mock检查通过，未实际格式化或访问块设备。

## 2026-10-03 Alpine eMMC 持久根实机验收


## 2026-10-03 部署脚本离线收尾

见 [K 交付修正](EMMC-DEPLOY-OFFLINE-FIX-20261003.md)。原厂无此部署脚本；当前明确拒绝已挂载 eMMC，旧取反检查被替代。设备树、硬件参数与设备均未改变；只验证主机命令桩和包复现，实际回退未演练。

## 2026-10-03 官方 wpa_supplicant 2.11-r4 实机对照

硬件原厂基线、生效方案A DTB、内核ath6kl=m、Wi-Fi供电/总线/固件、WDI ALT2/0x0c均未改；只将Alpine用户态@k4补丁2.12换为官方固定2.11-r4，@k4包/仓库保留。必要性为用户要求核实普通上游版本能否避免中止扫描停滞。没有新增扫描重试/钩子/看护；原K4服务和DHCP策略保持。正常reboot自动联网36.203秒，五轮原devices/devices/s2idle/STOP组合均确认SCAN_ABORTED并自动恢复、wpa/DHCP PID不变，最终watchdog30/10、根rw和无线正常。扫描中直接s2idle/STOP的额外轮次没有产生中止，不混计；结论不覆盖所有无线模式/长期稳定性。配方默认改为官方包仅建议，尚待用户确认，未改配方。详[WIFI-OFFICIAL-211-20261003.md](WIFI-OFFICIAL-211-20261003.md)。

## 2026-10-03 设备正式采用官方2.11并删除@k4

用户决定无观察期采用官方包。Alpine设备world保留wpa_supplicant=2.11-r4，删除@k4仓库行、/var/lib/apk/k4和本地签名公钥；官方公钥/K4服务SHA不变，apk update/fix --simulate通过，仅一个supplicant，发行版OpenRC子服务未加入runlevel。正常reboot自动联网39.735秒，固定5轮devices/devices/s2idle/STOP及每轮20秒清醒通过，success20/fail0，最终官方Wi-Fi连接/watchdog30/10/根rw/显示正常。硬件原厂基线与生效方案A DTB、内核、时钟/电源/总线未改；临时测试策略退出恢复。只记录设备，不改另一Codex的源码/配方；详[WIFI-OFFICIAL-CLEANUP-20261003.md](WIFI-OFFICIAL-CLEANUP-20261003.md)。此前保留@k4是历史状态。

## 2026-10-03 Alpine 标准网络设备原型

硬件原厂基线、当前production内核及方案A DTB8960edb8…bc0cdc保持，WDI ALT2/open-drain0x0c、Wi-Fi固件/总线/电源/时钟、RTC/watchdog参数未改。仅用户态由K4 Wi-Fi/DHCP supervisor改为官方OpenRC wpa_supplicant/wpa_cli + ifupdown-ng networking，coldplug/hostname等标准依赖足够；私有配置迁至默认600路径，USB静态地址由interfaces管理。没有新增重扫/看护/等待循环。首次/最终正常reboot37.437/38.593秒，5轮devices/devices/s2idle/STOP success20/fail0、各一scan aborted后自动恢复，标准wpa_cli通知与udhcpc10次释放/获取租约有日志，最终USB/Wi-Fi/watchdog30/10/根rw/显示正常。临时DHCP syslog选项已撤掉并再次正常启动验证。既存regulatory/SDMA固件告警、自然租约T1/T2/长时/其它AP与认证、回退实操仍有缺口。只提交设备记录，不改另一Codex的离线源码/配方；详[ALPINE-STANDARD-NETWORK-DEVICE-20261003.md](ALPINE-STANDARD-NETWORK-DEVICE-20261003.md)。

## 2026-10-03 Alpine 官方 OpenSSH 设备原型

原厂硬件基线及当前production内核/方案A DTB8960edb8…bc0cdc、WDI ALT2/0x0c、时钟/电源/无线/RTC配置保持。本轮仅把Alpine用户态Dropbear2222/k4-usb-ssh换为官方OpenSSH10.3_p1-r1的sshd default/22，networking标准依赖在先；gadget原已独立在k4-platform，configfs RNDIS+ACM保留。ECDSA转换前后指纹相同、authorized_keys不变；双接口密钥/严格known_hosts/密码拒绝/SFTP通过，2222不监听。正常reboot38.766秒，2轮devices/devices/s2idle/STOP success8/fail0，四次真实醒后USB/Wi-Fi SSH通过；最终watchdog30/10/根rw/显示正常。RAM维护Dropbear2222与镜像不改，主机工具区分profile；不改离线配方。长期连接/其它用户与完整回退未验。详[ALPINE-OPENSSH-DEVICE-20261003.md](ALPINE-OPENSSH-DEVICE-20261003.md)。

## 2026-10-03 barebox v9 标准USB gadget候选（离线）

基线为主分支617f97692中的v8；生效barebox DTS仍为imx50-kindle-d01100.dts，原厂/现有DDR、时钟、电源、pad与132 WRITE/3 CHECK初始化序列不变。v9仅启用上游DFU/Fastboot/UMS与依赖，并在板级init/usbconsole设置标准global.system.partitions，按上游语法列出boot0、boot1、user（r允许DFU读回）。不用自定义包装命令；默认仍只开串口，5秒Ctrl-C窗口及eMMC启动不变。

这是引导器构建与环境策略变化，不是硬件参数变化或新增内核接口。需要支持按需USB维护，使用上游原样usbgadget -A/-D/-S与-a串口；BOOTM_AIMAGE支持Fastboot kernel+initrd。证据和完整实机清单见barebox-emmc/V9-OFFLINE.md。

kindle用户两次独立构建最终镜像逐字节一致：262144字节、SHA f4150964673fe78dc8a4aa2fdf6fc6002787c145cf9a388e57b4df0c2ca0efd8；v8重建SHA吻合。7项plugin检查、5个默认启动分支与标准变量展开/源码核验通过。没有设备操作或部署；RAM Fastboot启动、DFU哈希/速度、UMS WSL/Windows与历史CRC、DFU+Fastboot和dfu-util版本兼容性待实测。

## 2026-10-03 barebox v9 RAM协议实测

原厂eMMC/DDR/时钟/电源参数未改；当前boot1仍v8、Linux方案A WDI DTB未替换。v9 DFU/Fastboot/UMS是现代恢复接口实现，三分区发布变量原样使用，r仅DFU读回标志，UMS非写保护。Windows三个LUN全区与DFU全区哈希一致、无历史CRC；WSL UMS透传扫描reset未读回、DFU+Fastboot组合描述符错误、Fastboot RAM实际启动失败。最终回到Alpine p1 rw、watchdog/Wi-Fi/USB SSH/显示初始化正常；暖RAM链启动不证明v9 ROM/boot1冷启动。详见[实机记录](barebox-emmc/V9-DEVICE-20261003.md)。

## 2026-10-03 v9 FIT 维护启动验收

上游 BOOTM_FITIMAGE/FITIMAGE/DIGEST/SHA256 配置支持现代多组件格式，不改变原厂硬件参数；DDR/plugin序列不变，镜像增长仅更新加载长度。生效Linux DTB为维护包方案A（WDI ALT2/0x0c），原字节打入FIT；本轮未另读WDI MMIO，不新增该项硬件验证。Fastboot标准boot命令实际进入6.6维护RAM，SSH2222、公钥身份、RAM只读loop根、正确cmdline、initrd解包、eMMC只读未挂载通过。guard900/30在约86秒主动reboot，35.06秒恢复v8→Alpine，boot1哈希不变。组合描述符问题仅上游调研未修；v9独立ROM/plugin冷启动仍未验。详见[FIT实机记录](barebox-emmc/V9-FIT-DEVICE-20261003.md)。

## 2026-10-03 FIT v9 部署boot1与冷启动验收

boot1从v8更新为FIT v9（SHA924db6da…44109d47，266240B），完整1MiB读回cdb60499…67e6586c与备份覆盖期望逐字节相同，782336B尾部不变；只解除boot1两层RO后恢复，179保持50。原厂DDR/plugin初始化参数/序列不改，Linux仍方案A DTB（源SHA8960edb8…bc0cdc）。正常reboot、SIGSTOP停喂的方案A PMIC冷启动、用户长按电源整机复位均自动经ROM/boot1进入Alpine；WDI2/0xc、WCR3b3d、WRSR10读回及根rw/USB SSH/Wi-Fi通过。未测电源轨，WRSR不是单独的断电证明。boot1 v9按需单独Fastboot/FIT实际RAM SSH2222通过，WDI2/0xc/eMMC只读未挂载确认后主动回Alpine；DFU全boot1读回与期望一致。显示初始化正常但本轮未新增刷新。最终boot0哈希保持原厂备份值，无ext4错误。组合模式仍未修，回退v8未执行。详见[部署实测](barebox-emmc/V9-BOOT1-DEVICE-20261003.md)与[当前部署/回退](../project/docs/BAREBOX-BOOT1.md)。

## 2026-10-03 主线普通维护与 Alpine 标准 watchdog 实机验收

构建基线 e8ceb7d40；方案 A DTB SHA8960edb8…bc0cdc、原厂 WDI ALT2/open-drain pad 0x0c、DDR/时钟/电源参数不变，boot1仍FIT v9。本次变化属于用户态生命周期和现代接口策略：删除有限guard/heartbeat/PM-health/块设备强制RO，维护根持续BusyBox watchdog 30s/10s，Alpine采用官方OpenRC watchdog boot服务与conf.d配置；不改变硬件watchdog timeout或WDI电气参数。维护fastboot/FIT实启动SSH2222，mmcblk2/p1 ro0/0、boot0/1默认force_ro1/1、用户区未挂载；25次采样跨度1205.96s、同boot ID、同watchdog PID，无复位。显式p1部署及762文件只读重挂载哈希通过，普通mount写/读/删除通过，无需setrw。新Alpine正常启动33.969s，停喂后53.469s自行经v9恢复，WRSR10/WCR3b3d/WDI2/0xc、根rw/标准watchdog/USB与Wi-Fi SSH/关联DHCP/ping通过，boot0/boot1整块哈希不变。WRSR停喂前也为10，结合时间线与boot ID判断，不作为单独电源轨测量。显示注册无自动首次刷新与上一版一致，额外一次标准sysfs刷新成功，未改启动策略。非正常关机后ext4 journal正常recovery，无ext4错误。剩余：长时/物理拔线/功耗未新增验证，旧文档和Alpine RAM入口问题见[本轮记录](MAINLINE-NORMAL-DEPLOY-20261003.md)；未修、未扩大范围。

## 2026-10-03 v9 上游 countdown 环境 boot1 验收

本轮只更新 barebox 环境实现：nv/autoboot=countdown、timeout=5、Ctrl-C中断，console默认值与linux.bootargs.k4独立；原厂DDR/plugin序列、时钟/电源/WDI硬件参数不变。主线c22712758两次新构建一致，镜像68cb670a…597ebe03/266240B，plugin.bin与旧FIT v9一致。仅写boot1，完整读回64da719c…73b40c8c等于新镜像+旧备份尾部，两层RO恢复1，EXT_CSD512字节完全相同、179=50，boot0哈希未变。正常倒计时自动启动36.672s，Ctrl-C与临时nv console加loglevel=5实际生效且下一次启动恢复默认，无持久环境写入；独立Fastboot/FIT实际RAM SSH2222、DFU三alt枚举通过，组合模式未测/未修。停喂50.797s自行经v9回Alpine，WDI2/0xc、WCR3b3d/WRSR10、根rw/watchdog/Wi-Fi/DHCP/ping/SSH正常；未测电源轨，停喂前WRSR也为10，不以单值证明断电。显示仍不主动首次刷新，与上一版一致。保留的consoleblank=0、fslepdc/video旧参数来源为冻结defaultenv两个nv文件；旧脚本清空bootargs时被掩盖。它们是继承的软件启动参数，不是本轮硬件参数更改；用户决定源头离线重建后删除，本轮未删、未改构建入口、未二次部署。文件与行号、前后cmdline和回退924db6da FIT v9详见[实机记录](barebox-emmc/V9-UPSTREAM-ENV-DEVICE-20261003.md)。剩余长时/物理拔线/功耗未新增验收，不push。

## 2026-10-03 v9 清除遗留启动参数与源码入口 boot1 验收

原厂2.6.31板级环境consoleblank=0、fslepdc/video=mxcepdcfb默认值已从新barebox输入移除；现代6.6沿用fbcon=map:1/logo.nologo和标准console/root/watchdog/ath6kl参数。属于软件启动接口清理，不改变原厂DDR/plugin序列、时钟、电源或WDI硬件配置；生效方案A源DTB SHA8960edb8…bc0cdc未替换。主线2f0c3475d新入口构建266240B/SHAfbcd7c01…fe0e40，与预期一致，boot1完整读回a5309d6b…23e5a3/尾部不变/两层RO1/179=50/boot0不变。正常倒计时36.265s、Ctrl-C/Fastboot维护FIT实际SSH2222与reboot、SIGSTOP停喂48.407s新boot ID恢复通过，根rw/watchdog/SSH22/Wi-Fi/ping2/2，无ext4错误。维护根普通watchdog、mmcblk2/p1 ro0/0且用户区未挂载，与当前普通维护合同一致。未新增显示刷新、物理拔线/电源轨/长时/组合接口验证；回退68cb670a未执行。详见[实机记录](barebox-emmc/V9-CLEAN-ENV-BOOT1-20261003.md)。

## 2026-10-03 主线最终文档新用户部署与停喂恢复

基线d257c155b，按project/README.md链接的生产源码入口重新构建。barebox v9 SHAfbcd7c01…fe0e40与设备相同，不写boot1；内核SHA50939951…7709896、源DTB SHA8960edb8…bc0cdc与既有正式版一致，不改变原厂DDR/共享时钟/电源/WDI硬件配置。仅将新Alpine根SHAdc011ac5…ea53ed部署到显式/dev/mmcblk2p1，格式化/解包/只读文件读回通过；这是用户态最终组织/诊断过滤更新，不新增硬件参数偏离。维护新FIT实际SSH2222直接cat/uname/ls可用；新Alpine根rw、官方watchdog/sshd、Wi-Fi/DHCP/ping/USB与Wi-Fi SSH22通过，/usr/bin探针0。一次SIGSTOP停止唯一官方watchdog，53.828秒后自动经v9进入新boot ID，根rw/watchdog active30/Wi-Fi/ping/SSH恢复；ext4仅正常journal recovery，boot0/boot1完整SHA及force_ro1不变。mmc-utils仅单项止损；/tmp size32m限制导致文档原上传流程容量不足，本轮用户许可临时/run工具包，不写成指南策略。维护/Alpine tmpfs采用内核默认大小的联合评估交用户决定；当前配置未改。原私有固件集合无WBF/WRF，未刷新显示，不新增显示/电源轨/功耗/长期验收；不将启动通过提升为这些结论。详见[流程与文档问题](NEW-USER-FLOW-20261003.md)。

## 新用户流程：标准 tmpfs 策略

维护 rcS 的 /tmp 原为 mode=1777,size=32m，RAM bootstrap 的 /run 原为 mode=0755,size=16m；现在仅删除 size，使用内核默认上限。Alpine eMMC/RAM fstab 的 /tmp 原为 mode=1777,size=32m，现在为 mode=1777；mount-early 不再重复挂 /tmp 或 /run，分别由 OpenRC localmount 按 fstab 和 OpenRC init.sh 挂载。依据为锁定 Alpine 根的 /usr/libexec/rc/sh/init.sh 与 /etc/init.d/localmount。该变化是用户态临时文件系统策略，不改变硬件配置或生效 imx50-kindle-k4.dtb。主机 shell 语法检查通过；三根构建与逐文件对比见 project/docs/NEW-USER-VALIDATION.md。默认 tmpfs 上限不是预留内存；实际容量、OpenRC 启动和原单一 /tmp 部署流程未在设备验证。

新用户待决项主机验收：默认 source 三根 IMAGES_OK，内核/DTB与基线逐字节相同；tar/cpio/内嵌ext3确认仅tmpfs相关运行文件变化，另外记录模块build链接的输出路径和独立BusyBox build-id差异。32+5+8主机测试通过；波形提取文档fixture通过，但本次没有设备操作。默认DT仍从面板NVMEM读取WBF并解码，不要求外部WBF/WRF；不新增硬件参数偏离或显示验收结论。详见 project/docs/NEW-USER-VALIDATION.md；原 tmpfs 文档待决已有用户决定并实施，历史日期报告不修改。

## 2026-10-03 新主线发布锁

基线b4821f0e8默认源码入口及独立空目录reproduce通过，23模块与kernel.lock.json一致；内核SHA50939951…7709896，生效imx50-kindle-k4.dtb SHA8960edb8…bc0cdc。发布锁替换旧PM-health时期的产物引用，不改变本次源码或原厂DDR/共享时钟/电源/WDI参数。32+5主机测试通过；设备部署与默认tmpfs验收在本轮后续步骤完成后另记。见[发布记录](RELEASE-DEPLOY-PUBLIC-20261003.md)。

## 2026-10-03 新发布最终部署与默认tmpfs设备验收

生效imx50-kindle-k4.dtb SHA8960edb8…bc0cdc，内核SHA50939951…7709896；原厂DDR、显示PLL1_SW、共享时钟、电源与WDI ALT2/0x0c不变。仅部署新Alpine根SHA30f9cb1b…94a3ff2到/dev/mmcblk2p1，完整p1备份校验和格式化/文件只读读回通过。维护FIT实启动SSH2222，/tmp与/run均118.9M，归档与工具完全按指南在/tmp操作；Alpine/tmp与/run同为默认118.9M、根rw、官方watchdog active30/10、Wi-Fi/DHCP/ping及USB/Wi-Fi SSH22通过。一次SIGSTOP停喂51.531秒内自行经v9返回新boot ID；串口明确观察emmc条目读取zImage，ext4仅正常journal recovery。boot0/boot1整块SHA未变，不写idme/fuse/EXT_CSD。未新增物理拔线电池启动、电源轨、长时、显示验收；Alpine RAM默认挂载仍仅主机构建。详见[发布实机记录](RELEASE-DEPLOY-PUBLIC-20261003.md)。

## 2026-10-03 当前公开源码与配方验收

公开导出改为当前rootfs/diagnostics/sources及porting/barebox-emmc v9配方；只发布生产/调试补丁，不携带完整上游树、旧barebox实验overlay、设备私有数据。独立Linux v6.6.157应用生产series后reproduce内核/生效imx50-kindle-k4.dtb/23模块与本次发布锁完全一致，维护cpio也一致；公开v9配方使用REUSE.toml给defaultenv声明许可，目录中无.license，build.py保持上游式目录复制，源码重建SHAfbcd7c01…fe0e40与现有设备boot1一致。REUSE6.2.0规范3.3检查通过。此为公开源码/配方主机验收，不改变原厂硬件参数或扩大设备验收范围；真实设备范围仍见[本轮记录](RELEASE-DEPLOY-PUBLIC-20261003.md)。

## 2026-10-03 公开导出最终来源与隐私审查

公开HEAD43b1d21，370受控文件与导出index一致、out受控0；177/177通过REUSE3.3，补齐OpenRC rc.conf的原作者/BSD声明和barebox board.c作者，defaultenv用annotations且构建配方无排除包装。可达495blob无私钥、凭据或私有二进制；宽泛MAC/路径命中分别为USB常量和审查正则。公开生产补丁与v9配方的主机构建结论不变，不改变生效imx50-kindle-k4.dtb或硬件参数，也不扩大冷启动/显示/电源轨验收范围。完整结果、临时误暂存的撤销与不可达对象范围见[公开导出审查](PUBLIC-EXPORT-AUDIT-20261003.md)。

## 2026-10-03 原厂备份私有输入提取（主机）

新增 project/extract-firmware.py 与 project/docs/FIRMWARE-EXTRACTION.md，按原厂 user 区分区表只读挂载 p1，提取 AR6003 hw2.1.1 API 1 四文件，bdata 跟随原厂 active_calibration；regulatory.db/p7s 使用公开用户态配方。未改变硬件参数，生效设备树仍为 arch/arm/boot/dts/nxp/imx/imx50-kindle-k4.dts。真实 DFU 备份提取、手工复制、Alpine 主机组装与维护配方检查通过，详见 project/docs/FIRMWARE-EXTRACTION-VALIDATION.md。范围仅为主机文件处理；本次不操作设备，不增加无线、RAM 或冷启动验收结论。

## 2026-10-03 ROM RAM 启动与 DFU 三区域完整备份

生效 RAM barebox DTS 为 imx50-kindle-d01100.dts，使用主线既有 v9 USB/DCD 镜像 SHA897819e9…adaa698；原厂 DDR、时钟、电源、pad 初始化参数不改。用户 Down→ROM 15a2:0052 后，经上游 imx-usb-loader 实际进入 RAM barebox shell，Windows COM7 预监听 Ctrl-C 截住倒计时。ACM+DFU 三 alt 只执行 upload，全读回 boot0/boot1 各1048576B、user1958739968B，耗时0.54/0.48/711.85s，SHA清单校验通过；boot1整块a5309d6b…8023e5a3与部署一致。不写eMMC/EXT_CSD/fuse。r为允许读回而非写保护。usbgadget -d; reset 后仍枚举ROM，由用户长按电源正常复位后恢复Alpine，SSH22/根rw/watchdog30/10/sshd/Wi-Fi COMPLETED及网关ping通过；不称软件复位恢复Alpine已通过。不是原厂未修改样本，不新增其它容量/主机、独立电池冷启动、电源轨、dd三分区验收。详见[实机记录](ROM-BACKUP-20261003.md)。

### Display lifecycle: PxP (2026-10-03)

- Applies to `imx50-kindle-k4.dtb` and the debug DTB using `fsl,imx50-pxp`.
- Standard bind/unbind and module exit replace the hidden permanent binding.
  Managed device links unbind consumers first; the job mutex drains conversion.
  Healthy jobs already prove park/idle and disable their IRQ before unlocking;
  remove frees the healthy arena and devres releases IRQ/MMIO/clocks.
- Existing fault quarantine stays: a faulted arena is not freed; an uncertain
  park retains its non-devm clock references and DMA device until machine reset.
  Unbind completes and releases software callbacks; retained allocations do not
  contain work/IRQ callbacks into an unloaded module. Hardware settings unchanged.
- Source review only at this commit; production/debug/module builds and host
  regression results are recorded after the full display lifecycle change.
  Real unbind/rebind, module reload, refresh and suspend/resume remain pending.

- Follow-up host validation: actual remove and clock cleanup passed with DMA_DEBUG=0/1, including retained arenas/device references. No device operations.

### Display lifecycle: EPDC (2026-10-03)

- Applies to the production/debug K4 DTBs (`amazon,k4-imx50-epdc`).
- Remove first detaches the regulator notifier, drains power work and the
  serialized synchronous update, shuts down the panel and verifies controller
  stop using the existing hardware quiet/gate checks. Healthy waveform/DMA
  storage is freed; devres tears down IRQ/MMIO, supplies, pins and clock handles.
- Standard bind/unbind/module exit replace permanent binding. Existing DMA
  quarantine remains: an unproven stop keeps DMA, its device reference and
  clock handles (including existing exclusive holds) until reset. Unbind completes;
  callbacks/IRQ/MMIO mappings are released after synchronization, so module code
  can unload. Rebind does not reclaim old quarantined memory. No clock/panel
  parameters changed; hardware lifecycle validation remains pending.

- Follow-up host validation: 51 actual owner cases passed, including notifier/work/stop/free ordering and fault quarantine; EPDC debug patch context synchronized. No device operations.

### Display lifecycle: fbdev (2026-10-03)

- Applies to production/debug K4 DTBs (`amazon,k4-epdc-fb`).
- Standard unbind stops damage scheduling, drains refresh/idle work and powers
  down the EPDC before releasing the supplier link. Unregister detaches fbcon
  and `/dev/fbN`; `fb_destroy` owns final defio/cmap/shadow/snapshot release.
- Existing open files and VMAs keep fb_info/shadow memory and the normal fbops
  module reference until close. Their stopped callbacks cannot access the old
  EPDC; blank/mode calls reject a removed instance. New binding creates a new
  framebuffer instance. This uses normal lifetime references, not an unbind veto.
- No image/timing policy changes; host builds/tests and hardware cycles pending.

- Follow-up host validation: 61 actual framebuffer cases passed, including retained old files/VMAs, stopped callbacks and final destruction. No device operations.

### Display lifecycle: Papyrus (2026-10-03)

- Applies to production/debug K4 DTBs (`amazon,k4-papyrus`).
- Restores standard bind/unbind. Existing stop marks the provider unavailable,
  drains the monitor and switches VCOM/DISPLAY off before sleeping Papyrus.
  Remove now synchronizes/disables the threaded IRQ before that stop and before
  devres unregisters hwmon/regulators and releases IRQ/GPIO/pinctrl/calibration.
  Managed EPDC links remove display consumers first. Module exit already existed.
- Stock power sequencing and electrical protections unchanged; real shutdown,
  rebind, refresh and suspend/resume validation remains pending.

- Follow-up host validation: 489 actual power/profile/recovery cases passed, including IRQ/work/provider removal; Papyrus debug patch context synchronized. No device operations.

### Display lifecycle: panel flash (2026-10-03)

- Applies to production/debug K4 DTBs (`amazon,kindle-panel-flash`).
- Both EPDC's direct `nvmem` waveform reference and Papyrus's fixed-layout
  `nvmem-cells` calibration reference now create managed links to the SPI driver.
  This also works without fw_devlink inference; supplier unbind detaches fbdev,
  EPDC and Papyrus before releasing nvmem callback storage. Consumer module/device
  references are released by devres; re-probes defer until suppliers return.
- Remove takes the read mutex, drains the current synchronous SPI read and marks
  the context stopped. Devres unregisters nvmem before freeing transfer buffers
  and context. Standard bind/unbind and the existing SPI module exit are enabled.
  No NOR write commands or geometry changes. Hardware verification pending.

- Follow-up host validation: 9390 NOR cases, 22 actual dependency-helper paths, and a real-mutex blocked SPI/remove test passed. No device operations.

### Display lifecycle: combined offline acceptance (2026-10-03)

- Effective DTBs: `nxp/imx/imx50-kindle-k4.dtb` and
  `nxp/imx/k4-debug/imx50-kindle-k4-debug.dtb`. Both DTBs built.
- Production/debug/five-driver-all-m builds passed zImage, modules, modpost
  and modules_install via `project/build.py`; all five modular drivers have
  init/exit symbols. Normal production/debug configuration and all factory
  display clock/power/timing settings are unchanged. Input SHA256 checks stay;
  artifact byte/hash identity was not an acceptance criterion.
- Project 32 tests and userspace comparison 5 tests passed. Display/DMA/power
  regressions and the new per-driver lifetime/order tests passed; pixel/AXI
  clock and PLL C-only regressions passed. PxP reset/DMA and Papyrus monitor
  tests ran on the debug-patched source. Optional Unicorn ARM PLL simulation
  was not run: Unicorn/ensurepip/pip are absent, and two local isolated install
  approaches failed; no further dependency changes were attempted.
- Debug series was applied after exported production patches in a private
  ignored source directory derived from this repository's `v6.6.157` tag.
  The maintained Papyrus/EPDC trace patch context was updated and full series
  reapplication passed; no files were copied from another worktree.
- No physical device operations. Unbind/bind, rmmod/insmod, subsequent refresh
  and suspend/resume remain hardware acceptance gates. Steps and fault-unbind
  semantics: [DISPLAY-LIFECYCLE-20261003.md](DISPLAY-LIFECYCLE-20261003.md).

## 2026-10-03 APBH consumer dependencies (host work, drivers/clock-deps)

Effective DT: `nxp/imx/imx50-kindle-k4.dtb` and its shared K4 dtsi.
APBH CCGR7 CG10 remains sourced from AHB, matching Yoshi
`clock_mx50_yoshi.c:apbh_dma_clk`. EPDC AXI/pixel and DISPLAY_AXI used
APBH secondary references in stock. In 6.6 the EPDC and PxP drivers already
hold their explicit `apbh` bulk clock during register/DMA activity. ANATOP
now uses provider runtime PM for the same access dependency, including
probe, CCF callbacks and sysfs reads; it releases APBH when idle. The
bridge no longer has `CLK_IS_CRITICAL`. ARM critical and shared PLL/rate
gating constraints remain unchanged.

A disabled APBH-DMA node supplies the bridge clock to the existing
`mxs-dma` driver, whose probe/reset and allocated-channel lifetimes already
balance prepare/enable. Its i.MX28 register-layout fallback agrees with
Yoshi `regs-apbh.h`; register range and IRQs come from `devices.c` and
`mx5x.h` (110..125). K4 does not enable this controller or GPMI NAND.
GPMI/BCH, OCOTP, DIGCTL, LCDIF, DCP, QoSC and PERFMON have no active
consumers in this DT; this change does not introduce NAND or other
peripheral support. Memory map: i.MX50 RM Rev.2 Table 2-3 and chapter 11.
Full source evidence and device acceptance steps: `CLOCK-DEPENDENCIES-20261003.md`.
Host validation and hardware gaps will be recorded after the build. No device access.

## 2026-10-03 shared APLL bandgap startup (host work, drivers/clock-deps)

Effective DT remains `nxp/imx/imx50-kindle-k4.dtb`; display remains
PLL1_SW at AXI 200 MHz/pixel 32 MHz. The previous bandgap-off
`EOPNOTSUPP` is replaced by a CCF shared parent, provider index 2.
RM 5.5.3 requires clearing REF_PWD, waiting at least 10 us, then setting
REF_SELFBIAS_OFF; before powerdown clear REF_SELFBIAS_OFF. Implementation
uses 15..30 us and SET/CLR aliases. APLL's 480 MHz output, HOLD/POWERUP
sequence and LOCK check are unchanged. Unlike the old Yoshi enable
callback (firmware reference prerequisite), this supports an initially
powered-down reference. CCF reference counts include APLL, direct analog
consumers and an enabled analog charger detector. K4 retains Yoshi's
CHGR_DET_DISABLE and therefore has no detector vote.

The last user restores the first user's reference entry state, preserving
an inherited powered reference alongside the unchanged inherited-APLL
ownership policy; an initially off reference is powered down. Analog
CLK_IGNORE_UNUSED remains, without an APBH vote when unprepared. Required
runtime-PM infrastructure is expressed by Kconfig PM dependency; no no-PM
always-on fallback is added. CPU critical, enabled-clock rate rejection
and shared PLL constraints remain. Actual-C MMIO fault/shared-vote tests
pass; physical startup timing, LOCK, cold boot and power remain device gates.
See `CLOCK-DEPENDENCIES-20261003.md` for evidence and acceptance steps.

### APBH runtime-PM lock ordering refinement

APBH is now obtained with `devm_clk_get_prepared`; provider runtime PM
only enables/disables it. This leaves a normal prepare vote while the
provider exists, but no enable vote while idle. It follows the PM-clock
prepare/enable split and avoids CCF prepare mutex / runtime-transition
lock inversion with simultaneous sysfs and CCF operations. Gate frequency,
register parameters and effective DT are unchanged; host callback and
compile checks are repeated for this refinement. Concurrent runtime PM
and sysfs on hardware remains part of the device checklist.

### Final host validation and separate hardware gate

Code `8eaf8711a`, production `imx50-kindle-k4.dtb`: full zImage/modules
build and modpost PASS, 23 modules with matching
`6.6.157-k4-clock-deps` vermagic, final compiler/modpost log without
warnings/errors. Project 32 tests, userspace 5 tests and 10 affected
clock/display/PxP/idle/standby host suites PASS. Both changed binding schemas
and examples PASS; production DTB targeted checks against six clock/DMA/
EPDC/PxP schemas PASS. Optional yamllint is absent; unrelated existing
maxim,max6625 duplicate schema warning is not a changed-binding failure.
No device was used. RAM/cold bandgap startup, physical LOCK, bridge
release/re-acquire, concurrent sysfs/CCF access, display/DMA, suspend/wake
and paired power measurements remain hardware gates. The separate-device
checklist and exact host commands are in `CLOCK-DEPENDENCIES-20261003.md`.
Generated artifact byte/hash identity is not an acceptance requirement;
source/download input SHA256 verification remains intact.

## 2026-10-03 波形格式与分配边界

生效设备树：`nxp/imx/imx50-kindle-k4.dtb`（公共 K4 common 的所有入口）。
删除 WBF 256 KiB / WRF 2 MiB 样本上限：WBF 以头部声明长度和实际文件/面板
NVMEM 窗口为边界；WRF 解码按模式数、温区数、LE64 表及每个展开流两遍计算，
检查 size_t 乘加溢出并按实际分配长度写入。已有 CRC、指针校验、完整帧对齐、
DMA 分配与地址范围检查保留。不改变原厂波形或电气参数。
主机验收与设备刷屏步骤见 `project/docs/DRIVER-LIMITS-VALIDATION.md`；未碰设备，
新内核刷新、温区及冷启动仍待设备任务验证。

## 2026-10-03 恢复原厂标称充电档位

生效设备树：`nxp/imx/imx50-kindle-k4.dtb`，所有 common DTS 入口。
原厂高速 file_storage 配置直接传 DAC5=480mA，全速 DAC1=80mA；未枚举主机
DAC1，墙充/第三方 DAC5。原厂无60mA预留或公差扣减，本次删除相关属性/成员
与最坏上界选择器，标准预算按标称档位量化；K4 UDC 全速交接至多100mA预算。
480mA 板级 DT 属性保留，binding/DTS 引用源码。CDP/DCP 继续 MAX14656 分类，
源与板级限制共同选 DAC5。Unknown 维持现有分类，原厂 J/K+超时列为后续项。
原厂温度、电压、时长等策略保留。依据 `CHARGE-SOURCE-MAPPING.md`；主机验证
与真实电流验收见 `project/docs/DRIVER-LIMITS-VALIDATION.md`。未碰设备，真实
SDP/全速/CDP/DCP 输入与净电池电流、冷启动和完整充电周期仍待设备任务。

## 2026-10-03 充电验收修正：采用上游配置额度，无速度特例

本节取代上文“恢复原厂标称充电档位”中的 K4 UDC 全速100mA交接结论。
生效设备树仍为 `nxp/imx/imx50-kindle-k4.dtb` 及 common DTS 入口，480mA
板级上限与其原厂出处不变；温度、电压、时长及源分类策略不变。
`drivers/usb/chipidea/udc.c` 撤回板级分支，恢复任务基线的上游原样，不新增
UDC↔PHY gadget关联。K4 PHY 保留标准 set_power 毫安额度接口，不读取速度。
上游 composite 的已配置 bMaxPower 对全速/高速采用相同 USB2 额度语义；
500mA→DAC5=480mA，100mA→DAC1=80mA，已连接但未配置时 composite 给100mA→DAC1。
实际断开0、挂起2mA仍→DAC0，不把它们当作未配置提高额度。

原厂 file_storage.c 全速配置直接选DAC1；本次全速已配置500mA选DAC5是明确的
有意偏离。理由：USB规范允许已配置的全速设备取500mA，上游 Linux
`composite.c:encode_bMaxPower()` / `set_config()` 对全速、高速均使用500mA
上限；采用标准配置额度避免把原厂 mass-storage 的速度策略带进所有现代
gadget。用户决定中的使用背景是现代主机基本为高速，选择仍以配置额度为准。

修正后的 ARM 构建/modpost、配置额度及相关主机测试结果见
`project/docs/DRIVER-LIMITS-VALIDATION.md`。未碰设备，真实全速主机电流、
SDP/CDP/DCP充电、冷启动及刷屏仍由设备任务验收，不能用主机模拟代替。

## 2026-10-03 主线 F1/F2/F3 实机验收

源码基线 `f8c933705`，生效 DTB `nxp/imx/imx50-kindle-k4.dtb`。
默认 `make -C project images` 源码构建正式 `6.6.157-k4-production`，
经 v9 barebox fastboot 维护 FIT 部署 `/dev/mmcblk2p1`，741 个文件读回通过。
boot0/boot1/idme/fuse/EXT_CSD 不写。新 Alpine 根 rw、OpenRC watchdog、
USB/Wi-Fi SSH22 及 Wi-Fi 实测正常。

五显示驱动各3轮 sysfs unbind/bind 后刷新通过；独立五驱动全=m RAM FIT
3轮卸载/加载通过。Papyrus VCOM→DISPLAY 内部 regulator 持有本模块引用，
先 sysfs unbind Papyrus、释放内部供电关系后再 rmmod；不强制卸载或绕过引用。
旧FD/mmap、在途写入中unbind通过；无oops/WARN/DMA quarantine或持续大幅内存增长。
flash快速连续bind首次未稳定恢复前端，独立provider顺序等待3轮通过；
快速恢复时序仍未完全归因，未给驱动加延时或保护。

APBH单计数证据为闲置enable0/prepare1，显示活动enable1，blank/idle回0；
ANATOP无用户时runtime suspended。临时CCF消费者共享bandgap两引用及APLL
3轮480MHz/LOCK与入口状态恢复通过，并发显示/寄存器读取无挂起或PM警告。
覆盖继承reference-on/APLL-off；未构造reference-off或PFD5调频。
默认Alpine s2idle3轮/STOP3轮、模块RAM各1轮均由PMIC RTC唤醒，后备RTC未触发，
唤醒后显示与网络恢复。显示仍PLL1_SW、AXI200MHz、pixel32MHz。

面板NVMEM WBF 111001→1175215字节，格式/旋转及GC16/DU/A2刷新成功；
相机确认白、黑、灰阶、棋盘、局部与文字画面，无大片缺块/花屏或棋盘残留。
电脑USB高速configured500mA额度读回PMIC DAC5/480mA（charger0=0x81022b），
自然full保护降DAC0正常，没有绕过电池保护。实际输入电流、墙充/全速主机、
低温和完整充电周期未测，不能以DAC标称值代替净电池电流或VBUS总电流。

一次SIGSTOP官方watchdog后，经boot1 emmc完整启动恢复，USB确认窗口90.250秒，
新boot ID、根rw、watchdog与网络/显示再验证通过；不是kexec，也不是断电冷启动。
未测外部成对功耗、debug配置或长期压力。详细实际命令、输出、问题和照片位置见
[DRIVER-ACCEPTANCE-20261003.md](DRIVER-ACCEPTANCE-20261003.md)。

## 2026-10-03 公开源文件环境清理

仅清理项目工具、文档与证据记录的本机环境标识，修正公开审查并取消导出文本改写。
硬件参数与驱动无改动；生效设备树仍为 `nxp/imx/imx50-kindle-k4.dtb`。
验证仅为主机回归、公开审查、复制一致性与许可检查，设备及冷启动不新增结论。
详见 [公开源文件清理](PUBLIC-SOURCE-CLEANUP-20261003.md)。
