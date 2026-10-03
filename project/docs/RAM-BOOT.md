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
(cd "$OUT/fit" && mkimage -f maintenance.its maintenance.itb)
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
usbipd attach --wsl --busid <BUSID>
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

`emmc-v9` 只在自动启动选择 emmc 条目后执行，才设置 `linux.bootargs.k4`；`usbconsole-v9` 在倒计时前仅设置入口、路径和控制台。倒计时中 Ctrl-C 不执行 emmc 脚本，无需删除这些命名空间。依据为编译环境脚本和上游 autoboot 调用路径；本命令序列已在本轮发布中通过维护 FIT 实机启动，见[发布验证](../../porting/RELEASE-DEPLOY-PUBLIC-20261003.md)。

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
usbipd attach --wsl --busid <BUSID>
```

先安装主机工具依赖并构建 loader；先按 [boot1 构建](BAREBOX-BOOT1.md#构建)生成 v9，再运行：

```sh
sudo apt install libusb-1.0-0-dev dfu-util usbutils
SRC="$OUT/barebox-v9/source/barebox-2026.09.0"
BUILD="$OUT/barebox-v9/build"
"$SRC/scripts/config" --file "$BUILD/.config" -e ARCH_IMX_USBLOADER
make -C "$SRC" O="$BUILD" ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- olddefconfig
make -C "$SRC" O="$BUILD" ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- scripts
```

**下载前先准备 Windows 串口监听。** ROM 跳转后会重新枚举，原 WSL 转接不会保持；本次 barebox 回到 Windows 为 `0525:a4a7 / COM7`。终端应等待实际串口出现，立即持续发送 Ctrl-C，截住 5 秒倒计时。已有 Python/pyserial 的主机可在独立 PowerShell 窗口预先运行以下命令，进入 shell 后在主机按 Ctrl-C 结束监听，释放串口给终端：

```powershell
python -u -c "import serial,time; end=time.monotonic()+180; s=None
while time.monotonic()<end:
 try: s=serial.Serial('COM7',115200,timeout=0.1); break
 except serial.SerialException: time.sleep(0.05)
if s:
 print('OPEN COM7',flush=True)
 while time.monotonic()<end:
  s.write(b'\x03'); d=s.read(8192)
  if d: print(d.decode(errors='replace'),end='',flush=True)
  time.sleep(0.05)"
```

确认 `usbipd attach` 已完成后，才执行下载。错过倒计时会进入默认 eMMC 启动流程；需要重新进入 ROM 再试。

ROM 下载使用上游 barebox 的主机 `scripts/imx/imx-usb-loader`（依赖 libusb），工具内置 `15a2:0052` 的 i.MX50 支持，不需要另写 K4 USB 配置。构建 v9 时也生成标准带 DCD 的 USB 镜像，路径与 boot1 plugin 不同：

```sh
"$BUILD/scripts/imx/imx-usb-loader" -h
sudo "$BUILD/scripts/imx/imx-usb-loader" "$BUILD/images/barebox-kindle-d01100.img"
```

预期输出为 `found i.MX50 USB device [15a2:0052]`、DCD 检查/写入、`binary file successfully loaded`、`jumping to 0x70020400`，随后串口出现 `barebox@Amazon Kindle D01100:/` shell。

USB 下载使用 `build/images/barebox-kindle-d01100.img`；eMMC boot1 写入使用 `plugin/barebox-boot1-plugin-candidate.img`。上游 loader 执行 USB 镜像中的 DCD 初始化 DDR，再启动 barebox；boot1 plugin 自己按 ROM eMMC ABI 搬运主体，两个布局不能互换。

2026-10-03 已实测 v9 USB 镜像从 ROM 下载并运行至 RAM 中 barebox shell，见[实机记录](../../porting/ROM-BACKUP-20261003.md)。loader 的跳转成功信息本身不足以证明 barebox 已运行，必须确认串口和 shell。

barebox 源码中的 `Documentation/boards/imx/amazon-kindle-4-5.rst` 和 `scripts/imx/imx-usb-loader.c` 说明该 ROM 路径。主机工具可从相同上游源码构建；安装 libusb 开发依赖后在 barebox 配置中启用 `CONFIG_ARCH_IMX_USBLOADER` 并 make，输出在 `build/scripts/imx/imx-usb-loader`。这是主机工具选项，不改变板级 DDR 参数。

ROM 下载后，Ctrl-C 进入 barebox，再按本页 FIT/fastboot 流程启动维护系统，恢复自己的 boot1 或重新部署 Alpine。ROM 入口本身不会恢复存储。首次安装前保留 USB 镜像、loader 和维护 FIT；这些文件在 boot1 损坏时也能由主机使用。

## 整机 eMMC 备份

安装前，从上面的 ROM 流程将 barebox 加载到 RAM 并进入 shell，即可完整读回 user、boot0、boot1 三个 eMMC 硬件区域。此流程不依赖 eMMC 系统，不写存储；不包含 EXT_CSD、fuse、面板 flash 或其它芯片数据。安装前另存 EXT_CSD，见 [boot1 指南](BAREBOX-BOOT1.md)。

在 barebox shell 核对容量，退出原 USB 串口并开启 ACM+DFU。两个切换命令在同一行执行，避免断开后无法输入：

```sh
ls -l /dev/mmc*
usbserial -d; usbgadget -a -D
```

`-a` 保留 ACM 控制台，`-D` 开启 DFU，不启用 fastboot/UMS。v9 用 `/dev/mmc2.boot0(boot0)r,/dev/mmc2.boot1(boot1)r,/dev/mmc2(user)r` 导出三个区域；`r` 表示允许 DFU 读回，并非写保护。本流程只使用 upload，不发送任何 download。切换后为 `1d6b:0104`，本次 Windows 标签为“USB 大容量存储设备”、串口 COM8；接口功能以 `dfu-util -l` 为准。

Windows 重新 `usbipd list`，必要时 bind，再 attach 当前 BUSID 到 WSL。主机运行：

```sh
sudo dfu-util -l
```

预期 `[1d6b:0104]` 的 alt 0/1/2 分别为 `boot0`、`boot1`、`user`。在主机仓库外的新私有目录预留至少 2 GB，逐个 upload（设备到主机）：

```sh
BACKUP="$HOME/k4-backup-$(date +%Y%m%d-%H%M%S)"
umask 077
mkdir "$BACKUP"
sudo /usr/bin/time -f 'elapsed=%e seconds' -o "$BACKUP/boot0.time" dfu-util -d 1d6b:0104 -a boot0 -U "$BACKUP/boot0.bin"
sudo /usr/bin/time -f 'elapsed=%e seconds' -o "$BACKUP/boot1.time" dfu-util -d 1d6b:0104 -a boot1 -U "$BACKUP/boot1.bin"
sudo /usr/bin/time -f 'elapsed=%e seconds' -o "$BACKUP/user.time" dfu-util -d 1d6b:0104 -a user -U "$BACKUP/user.bin"
sudo chown -R "$(id -u):$(id -g)" "$BACKUP"
chmod 700 "$BACKUP"
chmod 600 "$BACKUP"/*
stat -c '%n %s' "$BACKUP"/*.bin
(cd "$BACKUP" && sha256sum boot0.bin boot1.bin user.bin > SHA256SUMS && sha256sum -c SHA256SUMS)
```

**不要使用 dfu-util 的 `-D`（download，主机到设备）**；它与 barebox `usbgadget -D` 的含义不同。每个上传应报告 `Upload done.` 和完整 `Received a total of ... bytes`。dfu-util 0.11 可能长期显示 99%，以已传字节数、最终大小和 SHA 判断完成。

本次 D01100 样本 boot0/boot1 各 1,048,576 字节，耗时 0.54/0.48 秒；user 为 1,958,739,968 字节，耗时 711.85 秒（约 11 分 52 秒）；速度与主机/USB 转接有关，详见实机记录。其它设备以实际容量为准。备份含固件、设备身份、凭据和用户数据，不入 Git，不公开分发。

完成并校验后，在当前 ACM shell 执行：

```sh
usbgadget -d; reset
```

两条命令同一行发送，gadget 退出会断开控制台。本次这条命令使设备重新枚举为 ROM `15a2:0052`，**未自行回到 eMMC**。此时长按电源键复位后松开，不按方向键“下”，让设备从 eMMC 正常启动；不要把软件 reset 返回 ROM 当作 eMMC 已损坏。正常启动使用 EXT_CSD 当前选定分区；备份不安装 v9、不改变选择。本次正常电源复位后已恢复 eMMC Alpine，SSH22、根 rw、watchdog 和 Wi-Fi 健康检查通过，详见实机记录。

已有 Alpine/维护 shell 时，也可以直接 `dd` 读取 `/dev/mmcblk2`、`/dev/mmcblk2boot0`、`/dev/mmcblk2boot1`，通过 SSH 流式传到主机。先用 `ls /sys/class/block/mmcblk*` 核对实际设备号；本次未实测这条路径的三分区完整备份。运行中的 rw Alpine 会更改 user 区，不能保证文件系统一致性，需要一致性时使用不挂载 eMMC 的 RAM 系统。不要将约 1.9 GB 镜像保存在设备 `/tmp`。
