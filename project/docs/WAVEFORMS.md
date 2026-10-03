<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# 自己设备的显示波形

WBF 是面板原厂 flash 保存的压缩波形，含模式、温度表和 CRC；WRF 是展开后的 EPDC DMA 代理。WRF 复制 WBF 元数据，不能用 WBF filesize/CRC 校验整个 WRF，也不能改后缀代替转换。

默认 `imx50-kindle-k4.dtb` 的 common.dtsi 设置 NVMEM WBF、偏移 `0x886`、窗口 `0x2f77a` 和 `wbf-decode`。`drivers/nvmem/k4-panel-flash.c` 提供只读面板 NOR；`drivers/video/fbdev/imx50-epdc-waveform.c` 读取 WBF、验证格式1/CRC/指针/RLE并生成 WRF。**默认不需要外部 WBF/WRF 文件**，固件文件不会覆盖这个 NVMEM 路径。

没有可用波形时，系统仍可启动、维护和联网，显示不可用。Wi-Fi 仍需要自己的固件、校准和网络配置。

## 从运行中的现代系统获取

设备正常运行且绑定面板 flash 驱动时，先在 root shell 查看路径：

```sh
ls -l /sys/bus/nvmem/devices/k4-panel-flash*/nvmem
```

主机执行以下命令，只读取 flash，不请求显示刷新；多个匹配时先选择对应设备路径：

```sh
mkdir -p "$PRIVATE/firmware/amazon/k4"
ssh root@169.254.212.2 'cat /sys/bus/nvmem/devices/k4-panel-flash*/nvmem' > "$PRIVATE/panel-flash.bin"
python3 - "$PRIVATE/panel-flash.bin" "$PRIVATE/firmware/amazon/k4/panel-stock.wbf" <<'PY'
import pathlib, struct, sys, zlib
flash = pathlib.Path(sys.argv[1]).read_bytes()
start, window = 0x886, 0x2f77a
assert len(flash) >= start + window, 'panel flash backup truncated'
length = struct.unpack_from('<I', flash, start + 4)[0]
assert 48 <= length <= min(window, 256 * 1024), 'invalid WBF length'
wbf = flash[start:start + length]
assert wbf[35] == 1, 'unsupported WBF format'
assert zlib.crc32(b'\0' * 4 + wbf[4:]) == struct.unpack_from('<I', wbf)[0], 'WBF CRC mismatch'
pathlib.Path(sys.argv[2]).write_bytes(wbf)
print('WBF extracted:', length, 'bytes; default kernel generates WRF')
PY
```

维护系统使用 `ssh -p 2222`，Alpine 使用 22 端口。已有自己设备的完整面板 NOR 备份，可直接执行 Python 提取步骤；eMMC 全盘备份不是面板 NOR 备份。该命令按驱动注册名、NVMEM sysfs 接口、设备树偏移和 loader 的长度/CRC 实现核对，**本次未实机验证**。默认内核自动生成 WRF，无需手工转换。

## 从原厂系统或其文件备份获取配对文件

在原厂系统的 root shell 查看当前选择与版本：

```sh
cat /proc/wf/version
grep -H . /sys/module/*/parameters/waveform_to_use
ls -l /var/local/eink/waveforms/
```

`waveform_to_use` 是原厂 `fslepdc_hal.c` 的只读 module parameter；模块名由该内核决定，所以枚举 sysfs 路径。若输出为 `built-in` 或没有文件路径，不能从缓存列表猜测当前面板，使用上面的面板 NOR 路径或自己的已确认文件备份。`/proc/wf/path` 是独立的波形检查接口，不保证等于显示驱动的当前选择。按实际选择的 WBF 路径，核对同名 WRF 存在后，在主机复制：

```sh
WBF='/var/local/eink/waveforms/自己的面板文件.wbf'
WRF="${WBF%.wbf}.wrf"
scp "root@DEVICE:$WBF" "$PRIVATE/firmware/amazon/k4/panel-stock.wbf"
scp "root@DEVICE:$WRF" "$PRIVATE/firmware/amazon/k4/panel-stock.wrf"
python3 porting/inspect-waveform.py --wbf "$PRIVATE/firmware/amazon/k4/panel-stock.wbf" --wrf "$PRIVATE/firmware/amazon/k4/panel-stock.wrf"
```

原厂 SSH 地址、端口与认证使用自己系统的设置。只有文件备份时，从备份的 `var/local/eink/waveforms/` 复制当前选择的同名配对文件，再检查。原厂路径和配对读取依据为 `porting/WAVEFORMS.md` 中已有实机记录及原厂 `eink_panel.c`/`waveform.c`；上述完整命令**本次未实机验证**。缓存没有 WRF 时，默认 NVMEM 内核路径仍能解码支持的 WBF。外部文件加载的设备树才需要配对文件；本任务不修改设备树或驱动。

`/mnt/wfm/waveform_to_use.gz` 可能是压缩代理，不能当作原始 WBF。源码内置 25℃ 回退例子不能替代自己面板的波形。检查器验证格式、CRC 与配对头表，不证明画质或面板匹配。没有固定本机 SHA 限制；可自行记录 SHA256 校验备份传输。波形与面板备份留仓库外。flash 实际读取、面板匹配、刷新和跨温区画质仍需设备验证。
