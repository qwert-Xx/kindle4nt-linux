<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# 2026-10-03 ROM → barebox RAM → DFU 整机备份

## 范围与输入

基线主线 refactor/k4-modularization HEAD 4621fbb46；独立 worktree $BACKUP/k4-romtest，分支 docs/rom-backup。用户已手动进入 ROM；不写 boot0/boot1/user/EXT_CSD/fuse，不执行 DFU download，不 push。备份私有数据不入库。此次不是原厂未修改设备样本，但 ROM 加载与 DFU 读取不依赖 eMMC 上的引导/系统。

使用已有主线源码构建输出 out/barebox-v9-clean-env-deploy-20261003：

- plugin/barebox-boot1-plugin-candidate.img SHA256 fbcd7c01a1b4c213a50b4389f35f9c6c0143e976940d5295fd4bc3ee24fe0e40（只核对，不下载到 ROM、不写入 eMMC）。
- build/images/barebox-kindle-d01100.img SHA256 897819e9fa29d9985b7224b44a9c9e19e1ab243a1f46103bec5554627adaa698。
- barebox 2026.09.0 #1 Fri Oct 2 20:48:05 CST 2026，arm-linux-gnueabihf GCC 13.3.0。

主机 apt-get install 提示 dpkg interrupted，没有修复系统包状态。第二种方式在 $HOME/rom-backup-tools-20261003 使用 apt-get download 下载 libusb-1.0-0-dev、libusb-1.0-0、dfu-util、usbutils，并 dpkg-deb -x 解包至 sysroot。最初只解包开发包导致链接静态库缺少 udev 符号；补同版本运行库后正常动态链接。主机工具单独使用 loader-build，复制原 .config，scripts/config -e ARCH_IMX_USBLOADER，make olddefconfig / make scripts；PKG_CONFIG_PATH 指向 sysroot/usr/lib/x86_64-linux-gnu/pkgconfig，PKG_CONFIG_SYSROOT_DIR 指向 sysroot。运行时 LD_LIBRARY_PATH 指向 sysroot/usr/lib/x86_64-linux-gnu。不修改既有板级构建产物。

## ROM 下载与 shell

实际 Windows 命令：

```powershell
usbipd list
usbipd attach --wsl <发行版> --busid 1-7
```

15a2:0052 原已 Shared，无需重新 bind。usbipd 提示指定发行版已不是必需，实际选择 <发行版>。必须等 attach 完成后启动 loader；有一次过早调用返回 no supported device found，未进行传输。

WSL 以 root 使用以下镜像和工具（设置上述 LD_LIBRARY_PATH）：

```sh
$HOME/rom-backup-tools-20261003/loader-build/scripts/imx/imx-usb-loader $BACKUP/k4-modularization/out/barebox-v9-clean-env-deploy-20261003/build/images/barebox-kindle-d01100.img
```

输出：

```text
found i.MX50 USB device [15a2:0052]
DCD check condition 3 on address 0x63f80000
DCD check condition 0 on address 0x53fd408c
DCD check condition 3 on address 0x140000a8
main dcd length 454
DCD write: sub dcd length: 0x0054, flags: 0x04
DCD write: sub dcd length: 0x005c, flags: 0x04
DCD write: sub dcd length: 0x037c, flags: 0x04
loading binary file(...) to 0x70020400, firststage_len=265216 type=170, hdroffset=1024...
binary file successfully loaded
jumping to 0x70020400
```

第一次预先等待 WSL /dev/ttyACM 未成功：ROM 跳转重新枚举为 Windows 0525:a4a7 COM7，未保持转接；Windows 打开 COM7 时已自动进入 Alpine 0525:a4a8 COM10。用户重新 Down→ROM 后，改用预先等待 COM7 的 Windows Python/pyserial 命令持续发送 Ctrl-C，成功取得 barebox@Amazon Kindle D01100:/ shell。监听命令写入 RAM-BOOT.md；进入 shell 后结束主机监听释放串口。

实际 barebox 命令：

```sh
version
ls -l /dev/mmc*
usbserial -d; usbgadget -a -D
```

mmc2 1958739968 字节，mmc2.boot0/boot1 各 1048576 字节。切换导致旧 Windows 串口 read 的 ClearCommError，属于断开预期；新 gadget 为 1d6b:0104 / COM8。重新 attach 后 dfu-util 0.11 -l 列出 alt=0 boot0、alt=1 boot1、alt=2 user，ACM 为 /dev/ttyACM0。

## DFU 读回

主机目录 $HOME/backup-rom-20261003，仓库外；目录 0700、文件 0600，归 kindle:kindle。调用工具的绝对路径为 $HOME/rom-backup-tools-20261003/sysroot/usr/bin/dfu-util，以 root 访问 USB；LD_LIBRARY_PATH 如上。分区描述的 r 为 FILE_LIST_FLAG_READBACK，允许 upload，并不是写保护。此轮只执行 upload；三个实际上传参数分别为：

```sh
dfu-util -d 1d6b:0104 -a boot0 -U $HOME/backup-rom-20261003/boot0.bin
dfu-util -d 1d6b:0104 -a boot1 -U $HOME/backup-rom-20261003/boot1.bin
dfu-util -d 1d6b:0104 -a user -U $HOME/backup-rom-20261003/user.bin
```

/usr/bin/time -f elapsed=%e 记录各自耗时。boot0 使用 Bash 命令重定向到 boot0.log；两次后续 bash -lc 的 WSL 启动失败 Wsl/Service/0x8007274c，未产生 boot1 文件、未执行传输。改为 wsl.exe --exec env ... /usr/bin/time ... dfu-util 直接调用成功。boot1/user 输出由本次会话保存。

设备返回 transfer size 4096，上传进度长期显示 99%，必须看实际字节数和最终 Received 总量。boot0/boot1 均 Upload done、Received a total of 1048576 bytes，boot1 SHA 与部署整块读回一致。

三份结果（路径 $HOME/backup-rom-20261003/，SHA256SUMS 校验均 OK）：

| 文件 | 字节数 | 上传耗时 | SHA256 |
|---|---:|---:|---|
| boot0.bin | 1048576 | 0.54 s | 321f31a0f2555a9cb102c38d61244bc2d0ec0bd69bfb802356ab01bef9d4700f |
| boot1.bin | 1048576 | 0.48 s | a5309d6bfe53afe57b54faacf18cab922b37f2944e8bf5398c8480ac8023e5a3 |
| user.bin | 1958739968 | 711.85 s | f40cb2831d4a3a6d427064ff161ff5a09f725f6a7a0a81bd39dad0c85a1b9107 |

user 最终输出 Upload done. / Received a total of 1958739968 bytes，退出码 0。主机 stat 与 barebox 容量完全吻合。Windows 可经 $BACKUP\backup-rom-20261003 访问；供另一线程提取固件使用，未复制到 Git。

## 退出与恢复

读回完成后通过 WSL /dev/ttyACM0 运行 version，确认仍为 RAM barebox 2026.09.0，再发送同一行 usbgadget -d; reset。随后 Windows 枚举 15a2:0052，SSH22 Network is unreachable，软件复位未返回 eMMC。没有重试 loader 或存储操作；醒目请求用户长按电源复位后松开，不按 Down，从 eMMC 正常启动。此轮不能将软件 reset 写成正常回 Alpine 的已验证步骤。

等待用户正常复位后，轮询观察到 0525:a4a8 / COM10，USB SSH22 健康检查返回0：

```text
6.6.157-k4-production
/dev/root / ext4 rw,relatime 0 0
watchdog: status started
sshd: status started
WATCHDOG_OPTS="-T 30 -t 10"
WATCHDOG_DEV="/dev/watchdog"
wlan0: UP,LOWER_UP，已有IPv4地址
operstate: up
wpa_state=COMPLETED
网关 ping: 2 packets transmitted, 2 packets received, 0% packet loss
```

复位后新 boot ID 已记录于主机私有健康日志；未公开设备地址/身份。设备恢复到原 eMMC Alpine。用户手动复位后未截取 barebox 倒计时完整串口日志，不新增独立电池冷启动/电源轨/长期运行验证。

主机健康检查使用已有 modularization-cold-20261002/ssh-run.py，输入为仓库外 backup-20261003/health.sh，输出为 modularization-cold-20261002/rom-backup-20261003/rom-final-health.stdout/stderr。第一次健康脚本 PowerShell 写入 CRLF 导致最后 sysfs 路径带 CR，后续改为 LF；最终所有检查返回0。

## 文档问题清单

1. 缺少主机依赖包名、scripts/config 与具体 make 命令，补齐。
2. loader 不在 PATH，原命令不可直接照做，改为构建输出绝对/变量路径。
3. 缺少 ROM→barebox 重新枚举回 Windows 和提前监听倒计时说明，补入实测命令。
4. attach 必须完成后才能运行 loader；每次 gadget 改变重新查 BUSID/attach。
5. 原 ROM 组合未经实机验证标注已由 RAM shell 证据替换。
6. 缺少首次安装的三硬件区域完整备份流程，补入只读 DFU upload、大小/耗时/校验/私有数据说明；区分 dfu-util -D 与 usbgadget -D。
7. 原厂样本、不同容量、其它主机驱动与 dd 完整备份仍未实测，不扩张验收。
8. ROM 启动的 RAM barebox 执行 usbgadget -d; reset 后本次仍回 ROM；补入长按电源正常复位动作，不声称软件复位成功。


## 文档验证

project/README.md 链接整机备份，RAM-BOOT.md 补具体 loader 构建、文件路径、usbipd/预监听、三分区 upload 与实际退出限制；STOCK-CONFIG-DIFFERENCES.md 同步范围。四个文件确认 LF、kindle 所有者，git diff --check 通过；无代码/内核/设备树修改，不跑与文档无关的构建回归。本次没有新增保护或包装脚本，也没有固件提取文档。
