<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# 波形与充电额度验收

本次仅做主机构建和测试，不启动或连接设备。功能验收不要求镜像逐字节或
SHA 相同；下载输入的 SHA256 校验保留。所有设备步骤由另一个设备任务执行，
使用其明确授权的 RAM 启动或部署范围，记录真实启动入口，RAM/kexec 不算冷启动。

## 波形

默认 DTB：`nxp/imx/imx50-kindle-k4.dtb`。默认从面板 NVMEM 读取声明长度的
WBF 并解码。测试前记录原内核下屏幕、波形来源、温度和刷新成功/失败计数。
启动新内核，确认 dmesg 的 `WBF decoded` 源、输入与展开长度，无 CRC、分配、
DMA 或格式错误；没有波形时其它系统功能仍应可用，显示失败需明确报告。

用既有显示接口/工具提交白、黑、灰阶和文字画面，分别执行 INIT、GC16 全屏
及局部刷新；检查更新完成、可见画面、残影及错误计数。再执行现有支持的
DU/A2 模式，比较同一内容的更新行为，不改电压、时钟或波形。记录温度及选中
温区，正常使用范围内复测；不得通过注入传感器值或改电气参数制造结果。
波形替换只使用与实际面板匹配的私有输入，不向真实面板发送主机合成测试流。
主机合成流专门覆盖超过旧 256 KiB/2 MiB 上限、错误声明长度、指针校验、
流校验、完整帧对齐、分配失败和尺寸边界。

## 主机命令

在本 worktree 运行并将输出放 ignored `.k4-build/`：

```sh
make O="$PWD/.k4-build/kernel" ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- k4_defconfig
make O="$PWD/.k4-build/kernel" ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- -j8 zImage modules dtbs
python3 porting/test-epdc-waveform.py
python3 porting/test-epdc-buffer.py
python3 porting/test-epdc-hw.py
python3 -m unittest discover -s project -p 'test_*.py'
python3 project/userspace/test_compare.py
```

现有波形回归需要仓库外面板和 builtin 测试输入，命令支持显式输入路径。
这些是解析/解码测试夹具，不是正常驱动的样本大小或 SHA 门槛。

## USB 与真实电流（另派设备任务）

源码映射及证据见 [充电档位](../../porting/CHARGE-SOURCE-MAPPING.md)。
先在正常温度（>=10℃且<45℃）、未满且正常电压的原装电池上确认 eligible；
记录停止原因，不能绕过电池资格、温度、故障或时长保护来获得指定电流。
通过现有 charger power_supply 的 `constant_charge_current_max` 设480000，
再按既有 control 接口接管；初始用户上限仍80mA，未提高上限不能期待480mA。
记录源分类、gadget/detector/合并预算、board/user limit、目标与读回DAC、
电压/温度/容量、当前停止原因及错误计数。结束恢复原来的上限和控制状态。

| 实际连接条件 | 额度/预期目标（正常温度、上限480mA、eligible） |
|---|---|
| SDP 未枚举100mA | DAC1=80mA |
| SDP 高速已配置500mA | DAC5=480mA |
| SDP 全速已配置（真实FS主机/集线器或允许的FS配置） | 与高速相同按配置额度；500mA→DAC5，100mA→DAC1（有意偏离原厂FS策略） |
| 实际CDP/DCP或明确识别墙充 | detector额度有效，DAC5=480mA |
| Unknown且没有有效gadget额度 | DAC0；不靠超时升档 |
| 断开或标准suspend的小额度 | DAC0；重新枚举后按新额度恢复 |

用USB串联电流表/合适仪器测整机VBUS输入电流，同时读取电量计
`current_now` 净电池电流；这两者与DAC标称值分别记录，不能相互替代。
500mA主机、墙充分别记录稳定空闲、刷屏、网络活动期间的范围及VBUS电压，
确认源没有异常掉压/掉线、充电没有意外停止。实际电池电流因系统负载和恒压
阶段可能明显小于480mA，不用固定“净流入480mA”作判定。记录仪器与采样窗口。

实体拔插、额度变化与允许的挂起/恢复后检查新分类、新预算和寄存器档位；
刷屏后复查显示与充电错误计数。不要通过修改传感器、制造故障或主动深度
放电验收。低温、完整充电周期和自然低电量另记录，短时观察不覆盖它们。

## 本次主机结果（2026-10-03）

- ARM `k4_defconfig` 的 zImage、modules/modpost、两个 K4 DTB 完整构建通过；
  日志无 warning/error。输出 `.k4-build/kernel`，不使用发布样本产物SHA门槛。
- 波形 ASan/UBSan：179 个加载/NVMEM/解码场景、51001 个温度输入，包含超过
  旧上限的 WBF、解码与外部WRF；完整帧、校验、尺寸溢出和分配失败检查通过。
- DMA buffer 两种 DEBUG 配置、71 个实际控制器场景通过；独立 image 测试
  7008 个输入通过。image 测试需要从 `project/debug-patches/02-k4-trace-hooks.patch`
  提供 `drivers/misc/k4-debug/k4-epdc-image-test.h`；本次仅临时提取该测试消费者，
  验证后删除，没有将 debug 文件或路径加入生产内核。
- 充电策略及119个实际执行器场景、12个采样失败恢复点与65536个电压字、
  256个检测状态与192个源预算组合、17729个IRQ场景、2048个PM循环、LED回归通过。
  新增实际标准UDC→K4 PHY交接测试覆盖FS/HS相同额度映射、上游composite未配置
  100mA→DAC1、挂起/断开与通知。UDC保持任务基线上游原样，不含板级特例。
- 编译DT拓扑：50个实际注册/供电配置场景、2个DTB/充电profile通过。
- 项目 unittest 32项、userspace/test_compare.py 5项通过。

相关命令另含 `porting/test-k4-usb-charge-mapping.py`、`test-k4-charge-io.py`、
`test-k4-charge-sample.py`、`test-k4-charge-source.py`、`test-k4-charge-current-irq.py`、
`test-k4-charge-pm.py`、`test-k4-charge-leds.py` 及编译运行 `test-k4-charge-policy.c`。
上述为主机/模拟结论，未执行设备刷新、真实输入电流或冷启动验证。

## 验收修正复验

全速不再特殊限到100mA，测试对相同配置额度在全速和高速下使用相同预期。
主机测试编译实际 `ci_udc_vbus_draw()`、`k4_usb_set_power()` 和
`composite_reset()`，检查预算交接与未配置状态，不通过假定PHY有速度关联。
原厂FS差异及理由见 `porting/STOCK-CONFIG-DIFFERENCES.md` 最新修正节。

修正复验通过：ARM `zImage modules dtbs` 与 modpost（日志
`.k4-build/build-review.log`，无 warning/error）；标准UDC→K4 PHY交接、充电
策略/执行器/采样/源检测/IRQ/PM/LED及波形回归均通过；32项项目测试、5项
用户态测试、binding校验、50个注册场景与2个编译DT profile通过。
`git diff 4621fbb46 -- drivers/usb/chipidea/udc.c` 为空，证明通用控制器恢复
任务基线原样。此次仍无设备操作或实机电流结论。
