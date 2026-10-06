<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Framebuffer 显示与刷新

K4 的 `/dev/fb0` 是 800×600 RAM framebuffer，支持 8 位灰度、RGB565、
XRGB8888 和四种旋转。默认 AUTOMATIC 模式：write、fbcon 绘制和 mmap
脏页自动汇成整行区域，通过 AUTO/PARTIAL 异步提交；首次画布恢复用 FULL。
只读诊断在 `/sys/class/graphics/fb0/device/state`，完成状态以 ioctl 为准。

Alpine 根和 BusyBox 维护根可安装静态 ARM 工具 `k4-epd-update`。
工具刷新已有画布，不绘图；默认整幅 FULL + GC16，并等待该请求完成。

```sh
k4-epd-update
k4-epd-update --region 20,30,100,80 --waveform auto --wait
k4-epd-update --full --waveform gc16
k4-epd-update --partial --waveform du --no-wait
```

`--region x,y,w,h` 使用当前 framebuffer 旋转后的逻辑坐标，并默认选择
PARTIAL；显式 `--full` 可选择 FULL 算法。FULL 算法与区域大小是独立参数。
波形可选 `du`、`gc16`、`gc16-fast`、`a2`、`gl16`、`gl16-fast`、`auto`。
规范编号依次为 1..6、257；loader 按面板波形版本映射到文件索引。
FAST 是否有独立波形取决于文件版本，不能根据名称推断速度或画质。
默认设备 `/dev/fb0`，可用 `--device` 指定。退出码 0 表示成功，1 表示
打开设备或 ioctl 失败，2 表示参数错误。等待超时为 5 秒，超时不会取消更新。
`--no-wait` 只确认排队成功，后续处理错误需查看诊断状态。

## mxcfb 应用

驱动使用 NXP lf-6.6 的 `linux/mxcfb.h` 布局，`mxcfb_update_data` 为
72 字节，WAIT 使用 8 字节 `mxcfb_update_marker_data`。应用通过
MXCFB_SEND_UPDATE 提交请求，通过非零 update_marker 和
MXCFB_WAIT_FOR_UPDATE_COMPLETE 等待目标完成；marker=0 不跟踪完成。
多个应用须协调画布访问和 marker 编号，排队模式在异步处理时读取画布。

KOReader、FBInk 等自行发送更新的 mxcfb 应用，应先调用
MXCFB_SET_AUTO_UPDATE_MODE，传入 AUTO_UPDATE_MODE_REGION_MODE（0），
否则写屏还会额外触发自动刷新。自动模式为全局设置，应用可传入
AUTO_UPDATE_MODE_AUTOMATIC_MODE（1）恢复通用 fbdev 自动显示。

```c
#include <linux/mxcfb.h>
#include <sys/ioctl.h>

unsigned int mode = AUTO_UPDATE_MODE_REGION_MODE;
ioctl(fd, MXCFB_SET_AUTO_UPDATE_MODE, &mode);
```

每次 SEND_UPDATE 的 temp 必须为 TEMP_USE_AMBIENT，使用驱动自动测温；
MXCFB_SET_TEMPERATURE 同样只接受该值。支持 inversion（flag 1）和
force monochrome（flag 2）及其组合。dither_mode、quant_bit 必须为 0，
其它 flag 返回 EINVAL。collision_test 对支持的普通更新回填 0，
TEST_COLLISION 干跑请求不支持；该字段不统计管线内部的碰撞重试。

MXCFB_SET/GET_PWRDOWN_DELAY 使用有符号毫秒数，-1 禁用自动关电，
0 表示队列及 WB/LUT 空闲后立即关电。正常关电保留面板历史。
MXCFB_SET_UPDATE_SCHEME 接受三种 scheme：

- SNAPSHOT（0）：每次 SEND_UPDATE 和前端自动刷新提交在提交调用返回前，
  按源格式捕获请求区域。应用可在 SEND_UPDATE 成功返回后立即改写画布；
  异步转换、AUTO 判定及碰撞重试使用该更新的私有副本，各更新独立处理。
  分配失败返回 ENOMEM，该请求不进入队列。
- QUEUE（1）：逐项排队，在异步处理及碰撞重试时读取画布。
- QUEUE_AND_MERGE（2，默认）：同样异步读取画布，并合并满足条件的更新。

QUEUE 类的画布须保持有效直到更新完成；需要保留提交时内容的应用使用
SNAPSHOT。scheme 切换立即生效，已排队更新保留各自的副本或画布引用。
SNAPSHOT 下断电后首次更新仅恢复捕获区域的面板历史；需要整屏恢复时，
提交整屏区域。
AUTO 使用 K4 固定直方图映射，无需
MXCFB_SET_WAVEFORM_MODES；该命令及其它未实现的 NXP ioctl 返回 ENOTTY。

工具构建与根配方见[构建指南](BUILD.md)和[维护配方](MAINTENANCE-INPUTS.md)。
波形输入见[显示波形](WAVEFORMS.md)。主机测试与实机缺口见
[移植记录](../../porting/EPDC-MXCFB-20261004.md)。
