<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# RAM 启动与恢复

RAM 系统用于维护存储或运行临时 Alpine。内核和根系统从 RAM 启动，存储更改由维护命令执行。Watchdog 持续运行。

## 生成维护 FIT

安装主机的 U-Boot mkimage 工具后，在仓库根运行。`OUT/images` 是[统一入口](BUILD.md)的输出：

```sh
mkdir -p "$OUT/fit"
cp "$OUT/images/maintenance/arch/arm/boot/zImage" "$OUT/fit/k4-kernel.zImage"
cp "$OUT/images/maintenance/arch/arm/boot/dts/nxp/imx/imx50-kindle-k4.dtb" "$OUT/fit/k4-board.dtb"
cp "$OUT/images/maintenance/ram.cpio.gz" "$OUT/fit/k4-full-ram.cpio.gz"
cp porting/barebox-emmc/maintenance.its "$OUT/fit/maintenance.its"
(cd "$OUT/fit" && SOURCE_DATE_EPOCH=1790956800 mkimage -f maintenance.its maintenance.itb)
mkimage -l "$OUT/fit/maintenance.itb"
sha256sum "$OUT/fit/maintenance.itb"
```

prebuilt 模式的 zImage/DTB 位于 inputs JSON 指定的原输入路径；将前两条 cp 的源路径换成它们。Alpine RAM 使用相同内核/DTB，将第三条 cp 的源换成 `alpine-ram/alpine-ram.cpio.gz`。

## fastboot 主机准备

Linux 安装发行版的 `android-sdk-platform-tools`（fastboot）及 udev 规则；Debian/Ubuntu 示例：

```sh
sudo apt install android-sdk-platform-tools android-sdk-platform-tools-common
fastboot --version
```

部分发行版单独提供 `fastboot` 包。Android udev 规则不一定包含 barebox gadget；切换后用 `lsusb` 核对 VID/PID。本项目 v9 fastboot 默认 `1d6b:0104`。Debian/Ubuntu 可在 `/etc/udev/rules.d/70-k4-fastboot.rules` 添加：

```text
SUBSYSTEM=="usb", ATTR{idVendor}=="1d6b", ATTR{idProduct}=="0104", MODE="0660", GROUP="plugdev"
```

将当前用户加入 `plugdev` 后重新登录，执行 `sudo udevadm control --reload-rules` 并重新插接设备。其它发行版按其 USB 访问组或桌面 `TAG+="uaccess"` 惯例配置。用 `fastboot devices` 确认权限。

Windows 可从 [Google SDK Platform-Tools](https://developer.android.com/tools/releases/platform-tools) 下载、解压并直接使用 `fastboot.exe`，无需 WSL。设备管理器中的 fastboot 接口需要 WinUSB；ACM/RNDIS 驱动不能替代它。若未自动绑定，可使用 [Zadig](https://zadig.akeo.ie/) 为核对 VID/PID 后选中的 **fastboot 接口** 安装 WinUSB，不替换 ROM、串口或网络接口。Google USB Driver 面向 Google 设备，不应假定包含 Kindle/barebox 的 VID/PID。

在 Platform-Tools 目录打开 PowerShell，FIT 使用自己的 Windows 路径：

```powershell
.\fastboot.exe devices
.\fastboot.exe boot "$env:OUT\fit\maintenance.itb"
```

若在 WSL 中运行 Linux fastboot，按 [Microsoft USB/IP 指南](https://learn.microsoft.com/en-us/windows/wsl/connect-usb)，保持 WSL 发行版运行。首次 bind 使用管理员 PowerShell：

```powershell
usbipd list
usbipd bind --busid BUSID
usbipd attach --wsl --busid BUSID
```

用实际 BUSID 替换占位符。attach 期间 Windows 不能同时使用该设备。ROM、barebox 控制台、fastboot、Linux gadget 切换会重新枚举，设备号可能变化；每次重新 `usbipd list` 查找当前 BUSID，必要时重新 bind/attach。Linux USB 网络也需重新转接，或 detach 后由 Windows 使用。工具来源与权限依据见 [Ubuntu 包说明](https://packages.ubuntu.com/noble/android-sdk-platform-tools-common)。

## 从 barebox fastboot 启动

重启设备，在 5 秒倒计时中 Ctrl-C 进入 barebox USB shell。设置 RAM 参数：

```sh
global linux.bootargs.maintenance="console=ttymxc0,115200 rdinit=/init root=/dev/ram0 watchdog.open_timeout=120 imx2_wdt.nowayout=1 ath6kl_sdio.force_virtual_scatter=0 fbcon=map:1 logo.nologo"
global.bootm.boot_atag=false
usbserial -d
usbgadget -a -A
```

`emmc-v9` 只在自动启动选择 emmc 条目后执行，才设置 `linux.bootargs.k4`；`usbconsole-v9` 在倒计时前仅设置入口、路径和控制台。倒计时中 Ctrl-C 不执行 emmc 脚本，无需删除这些命名空间。依据为编译环境脚本和上游 autoboot 调用路径；新命令序列未实机验证。

切换 gadget 时原 USB 控制台会断开。准备主机后运行：

```sh
fastboot boot "$OUT/fit/maintenance.itb"
ssh -p 2222 root@169.254.212.2
```

维护根需要预先安装 Dropbear 主机密钥与授权公钥；示例配方见[维护输入](MAINTENANCE-INPUTS.md)。主机 USB 网络枚举可能稍晚于 ACM。主机也可能报告 `Status read failed` 而 Linux 已成功启动，详见[已知问题](KNOWN-ISSUES.md)。Alpine RAM 使用 SSH 22 端口。

维护系统中可[重新部署 Alpine](EMMC-ROOT.md)或[恢复 boot1](BAREBOX-BOOT1.md)：将自己的完整 boot1 备份作为写入镜像，以相同写入/完整读回流程恢复。恢复 boot1 不等于恢复用户区；后者需自己的完整备份。正常退出执行 `reboot`，进入当前选择的启动分区。

## i.MX50 ROM USB 下载

barebox 无法启动时，长按电源键强制复位，松开电源键时按住方向键“下”。ROM USB 设备为 `15a2:0052`。

Windows/WSL 主机可先查看 BUSID，再将该设备接入 WSL（将 BUSID 替换为 `usbipd list` 的结果）：

```powershell
usbipd list
usbipd bind --busid BUSID
usbipd attach --wsl --busid BUSID
```

ROM 下载使用上游 barebox 的主机 `scripts/imx/imx-usb-loader`（依赖 libusb），工具内置 `15a2:0052` 的 i.MX50 支持，不需要另写 K4 USB 配置。构建 v9 时也生成标准带 DCD 的 USB 镜像，路径与 boot1 plugin 不同：

```sh
imx-usb-loader -h
imx-usb-loader "$OUT/barebox-v9/build/images/barebox-kindle-d01100.img"
```

USB 下载使用 `build/images/barebox-kindle-d01100.img`；eMMC boot1 写入使用 `plugin/barebox-boot1-plugin-candidate.img`。上游 loader 执行 USB 镜像中的 DCD 初始化 DDR，再启动 barebox；boot1 plugin 自己按 ROM eMMC ABI 搬运主体，两个布局不能互换。

该 ROM 镜像与下载命令组合未经实机验证。文件布局及上游工具用法已按源码核对。

barebox 源码中的 `Documentation/boards/imx/amazon-kindle-4-5.rst` 和 `scripts/imx/imx-usb-loader.c` 说明该 ROM 路径。主机工具可从相同上游源码构建；安装 libusb 开发依赖后在 barebox 配置中启用 `CONFIG_ARCH_IMX_USBLOADER` 并 make，输出在 `build/scripts/imx/imx-usb-loader`。这是主机工具选项，不改变板级 DDR 参数。

ROM 下载后，Ctrl-C 进入 barebox，再按本页 FIT/fastboot 流程启动维护系统，恢复自己的 boot1 或重新部署 Alpine。ROM 入口本身不会恢复存储。首次安装前保留 USB 镜像、loader 和维护 FIT；这些文件在 boot1 损坏时也能由主机使用。
