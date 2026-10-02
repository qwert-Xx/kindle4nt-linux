<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# 已知问题与验证边界

- 3400/3600 mV 引导低电门槛延后；已有充电/BPON实现不能自动保证完全耗尽电池插USB后安全自救。真正低电冷启动与防重启死循环需专门验证，不能删原厂保护后部署。
- ZQ8/4 与板级返回关系未定：两次失败对一次23/8成功，样本少且历史B有其它barebox混杂。最小4轮23/8→8/4→8/4→23/8 fresh ROM对照另排；开发暂用23/8。
- dtc W=1 与DTB规范化/硬件属性等价已验证；dtschema 2026.9 已在外部环境验证K4 bindings；CCM中断编码已独立修正为TZIC两个一cell，K4正式DTB完整schema可匹配项校验错误清零，待阶段4→5后的独立冷验；make仍提示10条legacy compatible缺YAML覆盖，不宣称所有上游bindings无诊断。
- 诊断入口仅 debug；临时只读审计模块只在功能验收后显式加载。生产恢复机制与STOP OCRAM core不依赖诊断。模块名、release、目录必须匹配包，不能把同release当字节一致。
- 阶段4两项待合并冷回归；无显示消费者profile用于真正panel provider卸载。6.6→6.6 kexec交接尚未硬件验，RAM缺模块测试不等同 fresh-cold缺模块。
- watchdog WDBG被barebox首写锁定为0属加载器差异；正式驱动告警继续注册，不能为对齐项禁用安全watchdog。
- 原厂boot0回退、boot1一级barebox部署未执行。无触摸型号范围外，WPA2-PSK/CCMP之外认证、长期功耗/电气裕量/其它面板未承诺。
- 公共项目尚为草稿，源码配方的逐字节重建缺口见对应证据，不把同版本或同ELF格式当语义等价证明。固件/波形/设备身份/凭据仅外部私有输入。

- 阶段5 EPDC/PxP/Papyrus provider引用与module owner已离线验证，默认显示链仍内建；EPDC/PxP/fb候选模块无卸载入口（故障DMA/open fb生命周期），阶段5冷验须阶段4先通过。树外构建只证明同一内核ABI可链接，不证明热卸载或跨版本ABI。
- 新诊断早期标记位于OCRAM f8007b00；静态布局与C单测通过，新位置尚待实机确认。不进入production。

- 正式 trace 已清理，debug 必须先应用单独 overlay；源码预处理等价，PxP有一处等值比较寄存器分配交换，不能宣称机器码仅行号变化，见 DEBUG-CLEANUP.md。合并 defconfig 后的回归由主管安排。
