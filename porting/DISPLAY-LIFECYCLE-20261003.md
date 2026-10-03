<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# 显示驱动 bind/unbind 与模块生命周期验收

本次改动恢复五个驱动的标准 sysfs bind/unbind，并为模块提供退出路径。
主机验证在 `drivers/display-lifecycle` 的独立 worktree 完成，未操作设备。
生效设备树为 `nxp/imx/imx50-kindle-k4.dtb` 和
`nxp/imx/k4-debug/imx50-kindle-k4-debug.dtb`。

## 生命周期行为

| 驱动 | remove 的主要顺序 |
|---|---|
| PxP | device link 先解绑消费者；作业 mutex 等待同步转换及其 IRQ/park 结束；释放健康 DMA；devres 释放 IRQ/MMIO 和未保留的时钟引用 |
| EPDC | 消费者解绑；ready=false；注销 regulator notifier；排空 power work；mutex 等待更新；关面板并检查 controller quiet/gate；释放健康波形/DMA；devres 释放 IRQ/MMIO、regulator、GPIO/pinctrl、时钟引用 |
| fbdev | 标记 stopped；排空 deferred/idle work；等待并关闭 EPDC；设置 framebuffer suspended；注销 framebuffer/fbcon；最后一个 fb_info 引用释放 defio、cmap、shadow 和 snapshot |
| Papyrus | 消费者解绑；同步并禁用 threaded IRQ；标记 stopping/ready=false；排空 monitor；关 VCOM/DISPLAY、睡眠；devres 注销 hwmon/regulator 并释放 IRQ/GPIO/pinctrl/nvmem cell |
| panel flash | managed links 解绑 EPDC/Papyrus；读 mutex 等待 spi_sync 完成；标记 stopped；devres 注销 nvmem 后释放传输缓冲区和回调上下文 |

EPDC/Papyrus 的 flash 依赖显式链接到 SPI provider；PxP/EPDC/Papyrus
的既有 helper 同时持有 device/module 引用及 managed device link。
这保证 supplier unbind 先移除消费者。模块卸载遵循正常引用规则：
消费者仍绑定时不能卸载 supplier，已打开的 framebuffer 文件/映射持有
fbops 模块引用。关闭这些引用后即可正常卸载；sysfs unbind 本身不被拒绝。

### DMA 故障时

保留原有隔离策略。PxP 的 fault arena、EPDC 的未确认停稳或已隔离
waveform/DMA 不释放；无法确认 park/stop 时保留必要时钟引用，EPDC 的
既有 exclusive holds 也保留。隔离对象持有 DMA device 引用直到机器复位。
unbind 仍完成，排空并释放软件 work、IRQ 和 CPU MMIO 映射，模块代码可以退出。
重新 bind 不回收上一实例的隔离缓冲区；是否能刷新取决于现有硬件状态检查。
正常 unbind/bind 和模块循环不应产生这条隔离路径。

已有 fbdev 文件/VMAs 在 unbind 后保留旧 shadow 内存。旧实例停止后
不再访问 EPDC；重新 bind 获得新实例。旧文件关闭/映射解除后才最终释放旧内存。

## 主机验证

production、debug 和五驱动全 `=m` 均通过 zImage/DTB/modules、modpost、
modules_install；全 `=m` 的五个 `.ko` 均有 `init_module` 和 `cleanup_module`。
正常 production/debug 配置未改，下载输入 SHA256 校验未改，未比较产物字节一致性。

production 使用项目入口：

```sh
python3 project/build.py --preset production --out "$PWD/.k4-build/production"
```

debug 使用 `project/export.py` 生成的正式及调试 series，在本 worktree 的
ignored 子目录从仓库 `v6.6.157` 标签准备源码；逐项应用
`kernel/patches/series` 和 `kernel/debug-patches/series`，再执行：

```sh
python3 project/build.py --source "$PWD/.k4-build/debug-source-v2" \
  --preset debug --out "$PWD/.k4-build/debug"
```

项目入口默认构建正式 DTB；调试 DTB 另通过内核 make 构建。
`project/debug-patches/02-k4-trace-hooks.patch` 的 Papyrus/EPDC include 上下文
已同步生命周期改动；完整导出 series 重放通过。

全模块覆盖片段只设置以下五项为 `m`，再经项目入口的 `--config` 应用：

```text
CONFIG_IMX50_PXP_KERNEL=m
CONFIG_IMX50_EPDC=m
CONFIG_FB_IMX50_EPDC=m
CONFIG_REGULATOR_K4_PAPYRUS=m
CONFIG_NVMEM_K4_PANEL_FLASH=m
```

主机回归及新增验证：

- `python3 -m unittest discover -s project -p 'test_*.py'`：32 项通过。
- `python3 project/userspace/test_compare.py`：5 项通过。
- `test-epdc-fb.py`：61 项；正常注销、多个旧文件/映射引用、停止后的 deferred/idle/blank、最终 destroy 和 powerdown 错误。
- `test-epdc-owner.py`：51 项；notifier → work → 停稳/释放顺序，未使用实例、排队供电 work、stop 失败和已隔离缓冲区。
- `test-pxp-service.py`：DMA_DEBUG=0/1 均通过；正常及故障 remove、arena/device/clock 引用释放或保留。
- `test-papyrus-power.py`：489 项；IRQ/work/provider 退出顺序和停止后的请求。
- `test-k4-panel-flash.py`：9390 项；停止后的读取不再访问 SPI。
- `test-k4-panel-flash-link.py`：SPI=0/1 各 11 项；直接 provider、cell/layout、defer 与 device/module/OF 引用回收。
- `test-k4-panel-flash-remove.py`：真实 pthread mutex 阻塞 SPI 读取，验证 remove 等待、传输内存寿命及后续读拒绝。
- 既有 provider、EPDC buffer/hw/waveform、像素与 AXI 时钟测试通过。
- debug patch 源码上的既有 PxP reset/DMA、Papyrus monitor 测试通过。
- PLL C-only 测试通过；ARM Unicorn 仿真未跑。WSL 缺少 Unicorn、ensurepip 和 pip，两种隔离安装入口不可用，已停止依赖排查，未改主机环境。

构建日志、配置、产物、测试日志及汇总在本 worktree 的 `.k4-build/`；
`display-lifecycle-build-checks.json` 记录构建/modpost及五模块退出符号。
这些是主机证据，实机生命周期、刷屏和休眠验收仍待执行。

## 实机任务步骤（本线程未执行）

使用待验收内核及匹配模块，保留设备任务既定的恢复方式。通过连接终端执行，
先记录 `uname -r`、`dmesg` 和 framebuffer/EPDC/Papyrus 状态。

### 1. 枚举实际设备

驱动目录固定，设备 ID 从本机 sysfs 读取，不使用历史总线编号：

```sh
for d in \
  /sys/bus/platform/drivers/imx50-pxp-kernel \
  /sys/bus/platform/drivers/imx50-k4-epdc \
  /sys/bus/platform/drivers/k4-epdc-fb \
  /sys/bus/i2c/drivers/k4-papyrus \
  /sys/bus/spi/drivers/k4-panel-flash
 do
  echo "$d"
  ls -l "$d"
 done
```

确认每个目录有 bind/unbind。记录设备 symlink 名称，分别设置
`PXP_ID`、`EPDC_ID`、`FB_ID`、`PAPYRUS_ID`、`FLASH_ID`。

### 2. unbind/bind 循环

先对 fbdev 单独执行以下循环 10 次，每次 bind 后执行原有刷屏命令，
检查整屏/区域、8/16/32 bpp、四个旋转方向和 idle powerdown 功能一致：

```sh
D=/sys/bus/platform/drivers/k4-epdc-fb
printf '%s' "$FB_ID" > "$D/unbind"
printf '%s' "$FB_ID" > "$D/bind"
```

随后分别循环 EPDC、PxP、Papyrus、flash。解绑 supplier 时确认其消费者
自动解绑、fbdev 消失；观察过程中不能有 UAF、IRQ storm、workqueue 错误或 hang。
恢复时按 provider 到 consumer 顺序 bind 尚未绑定的设备：

1. panel flash；
2. Papyrus 和 PxP；
3. EPDC；
4. fbdev。

对每个设备向对应驱动的 `bind` 写入先前记录的 ID；已自动恢复的实例无需重复 bind。
每个循环后记录状态并刷屏。再在持续写入 framebuffer 时 unbind，确认在途刷新结束后
退出，重新 bind 后仍可整屏和区域刷新。

另做一次保持旧 framebuffer 文件和 mmap 的 frontend unbind/bind：
旧 shadow 仍可安全访问，不刷新硬件；旧 FD 的后续设备读写返回移除错误；
新 `/dev/fbN` 可刷新。关闭旧 FD、解除映射后，旧引用应释放。

### 3. rmmod/insmod（五驱动全 =m 内核）

结束显示应用并关闭其文件/映射，然后按消费者到 provider 卸载：

```sh
rmmod imx50_epdc_fb
rmmod imx50_k4_epdc
rmmod imx50_pxp
rmmod k4_papyrus
rmmod k4_panel_flash
```

调试内核若加载其它显示消费者，先按其 device link 依赖卸载。记录实际模块目录：

```sh
M=/lib/modules/$(uname -r)/kernel
insmod "$M/drivers/nvmem/k4-panel-flash.ko"
insmod "$M/drivers/regulator/k4-papyrus.ko"
insmod "$M/drivers/soc/imx/imx50-pxp.ko"
insmod "$M/drivers/video/fbdev/imx50-k4-epdc.ko"
insmod "$M/drivers/video/fbdev/imx50-epdc-fb.ko"
```

循环 10 次，每次确认 sysfs、hwmon、nvmem、fbdev 恢复，并进行刷屏。
同一实例正常循环不应出现 DMA quarantine 日志或持续增长的未释放缓冲区。

### 4. 后续功能

每一类循环完成后执行项目原有的休眠/唤醒流程；唤醒后再次整屏和区域刷新，
检查 Papyrus 温度、VCOM/供电、idle powerdown 及再次休眠。production 与 debug
分别记录功能结果；全 `=m` 另记录模块循环结果。验收比较功能，不要求图像、
内核或归档的哈希与旧产物一致。
