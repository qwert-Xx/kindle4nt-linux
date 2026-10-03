<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# D01100 boot1 barebox

这是独立 boot1 主题：上游 barebox v2026.09.0 + Kindle 板级修改。通用 MCI、MMC 与 watchdog 驱动不修改。v8 默认探测 non-removable eMMC，以 ext4 读取 p1 的 /boot/zImage 与 /boot/imx50-kindle-k4.dtb，无 initrd；不读 idme、不加载持久环境。USB串口 Ctrl-C 中断 sleep 5，进入 shell/YMODEM RAM 上传；不要复位前按上。保留 MCI 写入能力，但没有默认存储写入动作。只覆盖 D01100/LPDDR1；不要套用于其它板型。

## 构建配方

使用既有 ARM GCC/binutils、make、Python 3，不装新依赖。上游 Git 必须包含 v2026.09.0。外部 USB 基准镜像须来自已验证的23/8配置；stock-boot0-reference 是用户自己导出的原厂 boot0 二进制，仅用于复制44字节ROM头，不随公共仓库发布。配置见 barebox/boot1/barebox.config。输出为新目录。

```sh
sh barebox/boot1/build.sh /absolute/barebox-git barebox/boot1/barebox.config /absolute/verified-usb.img /absolute/new-boot1-build /absolute/stock-boot0-reference.img
sha256sum /absolute/new-boot1-build/plugin/barebox-boot1-plugin-candidate.img
```

脚本仅解包上游、修改板级源码、交叉编译和包装镜像，不连接设备。记录外部输入SHA、编译器版本和输出 audit.json/SHA256SUMS。可设 KBUILD_BUILD_TIMESTAMP/KBUILD_BUILD_VERSION 固定版本元数据。公共源码保留WDT半字诊断地址修正；v8 环境使用标准 emmc/host-ram boot 顺序，sleep 5 等待 Ctrl-C。挂载、缺文件或 bootm 返回错误时回落主机加载；跳转后崩溃不保证回落。固定元数据可用 KBUILD_BUILD_TIMESTAMP="Fri Oct 2 20:48:05 CST 2026" 与 KBUILD_BUILD_VERSION=1。已部署的本机v8验证不自动覆盖任意外部输入重建候选。

## plugin/OCRAM 初始化

ROM MMC首读2KiB：第一IVT@0x400，加载基址0xf8006000、入口0xf8006004、长度0x800、plugin=1；原厂push/pop与ROM栈保留。135条DCD操作压缩为8字节软件记录，35条在第一IVT之前，100条在0x480..0x79f，地址低两位编码类型；实际访问清低两位，132次32位WRITE和3次CHECK同值同序同宽度，ZQ23/8不变。序列表完全来自外部USB基准。

SI_REV=0x11调用ROM helper 0x2aad，否则0x2a19；恢复ROM寄存器并返回1。ROM搬运完整镜像至0x70020000，第二IVT@0x42c、非plugin入口0x70021000；barebox主体位于文件0x1000。两个DCD指针为0，首段可完整落入ROM窗口。

plugin阶段记录@0xf8008080；barebox记录@0xf8008000，记录SRC及DDR状态。WCR/WSR/WRSR用16位读取0x53f98000/02/04，旧错误GPIO5数据不作WDT证据。主体设置watchdog120秒/autoping，不更改DDR、PLL或充电参数。

## 写入、激活与回退（操作说明，非自动脚本）

先建立可用的“下键+复位→ROM→普通USB barebox→Linux RAM”人工恢复路径，并准备足电、维护工具与主机备份。本主题不承诺自动退回boot0。以下设备名仅是此Linux枚举示例，必须用容量/身份确认；操作不要写用户区或boot0，不挂载eMMC。使用标准 mmc-utils `mmc` 和已有 blockdev/dd/cmp/sync。先保存EXT_CSD文本及完整boot1，复制到主机核验：

```sh
mmc extcsd read /dev/mmcblk2 > /ram/extcsd-before.txt
dd if=/dev/mmcblk2boot1 of=/ram/boot1-before.bin bs=512 count=2048
sha256sum /ram/boot1-before.bin /ram/candidate.img
```

本机boot区1MiB；别的容量按实际调整完整备份长度。确认PARTITION_CONFIG=0x48、BOOT_BUS_WIDTH=0x00、boot1硬件未锁写；ACK bit6保留。备份不得省略。构造预期完整读回，保持镜像之外旧尾部；只解除boot1的force_ro与块设备RO：

```sh
cp /ram/boot1-before.bin /ram/expected.bin
dd if=/ram/candidate.img of=/ram/expected.bin bs=512 conv=notrunc
restore_ro() { echo 1 > /sys/class/block/mmcblk2boot1/force_ro; blockdev --setro /dev/mmcblk2boot1; }
trap restore_ro EXIT
trap 'exit 1' HUP INT TERM
set -e
echo 0 > /sys/class/block/mmcblk2boot1/force_ro
blockdev --setrw /dev/mmcblk2boot1
dd if=/ram/candidate.img of=/dev/mmcblk2boot1 bs=512 conv=notrunc
sync
dd if=/dev/mmcblk2boot1 of=/ram/boot1-after.bin bs=512 count=2048
cmp /ram/expected.bin /ram/boot1-after.bin
restore_ro
trap - EXIT HUP INT TERM
mmc extcsd read /dev/mmcblk2
```

读回全部相同且179仍0x48后再独立激活。179命令发送到主设备，标准mmc-utils只写该字节；成功或失败都恢复主设备RO：

```sh
trap 'blockdev --setro /dev/mmcblk2' EXIT
blockdev --setrw /dev/mmcblk2
mmc extcsd write 179 0x50 /dev/mmcblk2
mmc extcsd read /dev/mmcblk2
blockdev --setro /dev/mmcblk2
trap - EXIT
```

必须人工核对PARTITION_CONFIG=0x50，再冷复位观察串口、plugin/SRC/DDR诊断，核验自动加载eMMC根与正式功能及恢复。普通USB镜像启动不能证明MMC plugin/ROM helper运行。

回退：下键+复位进ROM、普通USB恢复到Linux RAM，执行上述179命令组，把0x50改为0x48，确认读回后复位。只改变启动选择，不擦boot1，不改boot0、不改BOOT_BUS_WIDTH，不写永久硬件保护。

低电3400/3600mV软件放行策略按用户决定不实现：MC13892硬件可在CPU不运行时充电；这不等于已验证完全耗尽电池的实际行为。

离线配方已实际完成ARM构建；首段结构、序列表、ROM ABI/执行分支及头/表破坏检查7项通过。公共内容仅含源码/配置/说明，未包含stock镜像、设备身份、原始日志、固件、波形或凭据。构建成功不代替新候选冷验。

## 当前状态（2026-10-03，既有实机记录）

boot1 barebox v8，EXT_CSD[179]=0x50，默认 eMMC p1 Alpine 3.24.2；BusyBox 根作为维护/备选。
USB 串口发送 Ctrl-C（0x03）中断 boot/emmc 的 sleep 5 进入 shell，再 YMODEM 加载方案 A RAM 维护包（k4-maint-ram-20261003，900/30 expire-health）；不要复位前按上。5秒从脚本运行计起，Windows枚举可能缩短实际主机窗口，窗口末尾和电池独立冷启动待验。
WDI 原厂方案 A 为 ALT2/0x0c，正常态由 restart pinctrl 持有。Alpine 正常根持续 watchdog 喂狗，无有限 RAM guard；静态 2.12 supplicant 由本地 @k4 APK 提供。
Alpine 首次启动与3轮正常 reboot、两档 RTC STOP/内存保持/醒后刷新、NTP/SRTC正常关机读写和 HTTPS apk update 已有实机记录；长期运行、upgrade、第二台 K4 与物理电源轨仍未验。详 [Alpine 配方](ALPINE-ROOT.md) 与 [guard 对照](RAM-GUARD-COMPARISON.md)。发布前需用户许可审阅。
本次只离线编辑、构建和扫描，未访问设备、未 push。默认根更新不意味着覆盖所有冷启动/耐久验收。

公开 v8 输出须与已部署镜像逐字节一致，SHA256 `b283f374a5fda6e7ba2c5c3b83ba9f67a569c1e63493d9ab4ea3b79febda0606`。emmc-v8/usbconsole-v8/host-ram-v7 使用 .license 旁注，不向编译环境脚本插入许可注释。plugin/132写+3检查及前4096字节保持v7。
