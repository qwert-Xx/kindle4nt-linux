<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# 已知问题与验证边界

- 3400/3600 mV 软件引导门槛按用户决定不实现；真实完全耗尽电池自救仍未验证。
- ZQ8/4历史失败根因未定；四轮重复队列已关闭。当前boot1保留23/8，不宣称参数等价。
- dtc W=1 与DTB规范化/硬件属性等价已验证；dtschema 2026.9 已在外部环境验证K4 bindings；CCM中断编码已独立修正为TZIC两个一cell，K4正式DTB完整schema可匹配项校验错误清零，待阶段4→5后的独立冷验；make仍提示10条legacy compatible缺YAML覆盖，不宣称所有上游bindings无诊断。
- 诊断入口仅 debug；临时只读审计模块只在功能验收后显式加载。生产恢复机制与STOP OCRAM core不依赖诊断。模块名、release、目录必须匹配包，不能把同release当字节一致。
- 阶段4两项待合并冷回归；无显示消费者profile用于真正panel provider卸载。本次方案A已执行6.6→6.6无initrd kexec，但不覆盖所有交接profile；RAM缺模块测试不等同 fresh-cold缺模块。
- watchdog WDBG被barebox首写锁定为0属加载器差异；正式驱动告警继续注册，不能为对齐项禁用安全watchdog。
- boot1 v8 已有部署记录；原厂boot0完整回退未演练。无触摸型号范围外，WPA2-PSK/CCMP之外认证、长期功耗/电气裕量/其它面板未承诺。
- 公共项目尚为草稿，源码配方的逐字节重建缺口见对应证据，不把同版本或同ELF格式当语义等价证明。固件/波形/设备身份/凭据仅外部私有输入。

- 阶段5 EPDC/PxP/Papyrus provider引用与module owner已离线验证，默认显示链仍内建；EPDC/PxP/fb候选模块无卸载入口（故障DMA/open fb生命周期），阶段5冷验须阶段4先通过。树外构建只证明同一内核ABI可链接，不证明热卸载或跨版本ABI。
- 新诊断早期标记位于OCRAM f8007b00；静态布局与C单测通过，新位置尚待实机确认。不进入production。

- 正式 trace 已清理，debug 必须先应用单独 overlay；源码预处理等价，PxP有一处等值比较寄存器分配交换，不能宣称机器码仅行号变化，见 DEBUG-CLEANUP.md。合并 defconfig 后的回归由主管安排。

## boot1主题接续

上文ZQ四轮与返回原厂boot0的不稳定排查队列已关闭：当前一级引导使用23/8的boot1 barebox，重启目标已变化；保留历史失败，未冒称原根因定位。3400/3600mV软件门槛按用户决定不实现，MC13892硬件在CPU不运行时也能充电；真实耗尽电池行为仍未验证。新构建候选的冷验独立于旧v5证据，详BAREBOX-BOOT1.md。

## 当前状态（2026-10-03，既有实机记录）

boot1 barebox v8，EXT_CSD[179]=0x50，默认 eMMC p1 Alpine 3.24.2；BusyBox 根作为维护/备选。
USB 串口发送 Ctrl-C（0x03）中断 boot/emmc 的 sleep 5 进入 shell，再 YMODEM 加载方案 A RAM 维护包（k4-maint-ram-20261003，900/30 expire-health）；不要复位前按上。5秒从脚本运行计起，Windows枚举可能缩短实际主机窗口，窗口末尾和电池独立冷启动待验。
WDI 原厂方案 A 为 ALT2/0x0c，正常态由 restart pinctrl 持有。Alpine 正常根持续 watchdog 喂狗，无有限 RAM guard；静态 2.12 supplicant 由本地 @k4 APK 提供。
Alpine 首次启动与3轮正常 reboot、两档 RTC STOP/内存保持/醒后刷新、NTP/SRTC正常关机读写和 HTTPS apk update 已有实机记录；长期运行、upgrade、第二台 K4 与物理电源轨仍未验。详 [Alpine 配方](ALPINE-ROOT.md) 与 [guard 对照](RAM-GUARD-COMPARISON.md)。发布前需用户许可审阅。
本次只离线编辑、构建和扫描，未访问设备、未 push。默认根更新不意味着覆盖所有冷启动/耐久验收。
