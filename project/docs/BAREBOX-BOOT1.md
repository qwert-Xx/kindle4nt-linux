<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# boot1 引导程序

barebox v9 从 eMMC boot1 启动，默认启用 USB 串口。上游 autoboot 倒计时 5 秒，Ctrl-C 进入 shell；否则读取用户区第一分区的 `/boot/zImage` 与 `/boot/imx50-kindle-k4.dtb`，直接启动 Alpine。

## 构建

在仓库根：

```sh
python3 porting/barebox-emmc/build.py --cache "$PRIVATE/barebox-cache" --output "$OUT/barebox-v9"
sha256sum "$OUT/barebox-v9/plugin/barebox-boot1-plugin-candidate.img"
```

上游为锁定的 2026.09.0 tarball，板级改动在 `board.patch`，默认配置和环境在 `v9_defconfig`、`defaultenv-v9/`。已有缓存可追加 `--offline`。输出需为新目录；`--config` 选择其它 barebox 配置。当前设备记录的源码构建 v9 为 266240 字节，SHA256 `fbcd7c01a1b4c213a50b4389f35f9c6c0143e976940d5295fd4bc3ee24fe0e40`；自己的构建以实际输出 SHA 为准。

## 备份和写入

先准备[RAM 维护与 ROM 恢复](RAM-BOOT.md)。以下命令在设备上已有 Alpine 或 RAM 维护 shell 中运行。设备号示例为当前 6.6 的 `mmcblk2`，先用 `ls /sys/class/block` 确认。原厂内核可能使用不同编号。

完整备份用户区、boot0、boot1 与 EXT_CSD，并复制到主机保存。先在主机上传构建镜像和[维护工具](../userspace/MAINTENANCE.md)：

```sh
ssh -p 2222 root@169.254.212.2 'mkdir -p /tmp/boot1'
ssh -p 2222 root@169.254.212.2 'cat > /tmp/boot1/barebox.img' < "$OUT/barebox-v9/plugin/barebox-boot1-plugin-candidate.img"
ssh -p 2222 root@169.254.212.2 'cat > /tmp/boot1/mmc-tools.tar.gz' < "$OUT/mmc-tools/maintenance.tar.gz"
```

下列命令在设备维护 shell 执行，备份 boot1 和 EXT_CSD：

```sh
mkdir -p /tmp/boot1
cd /tmp/boot1
tar -xzpf mmc-tools.tar.gz
export PATH="$PWD/maintenance:$PATH"
extcsd-read /dev/mmcblk2 > extcsd.before.bin
dd if=/dev/mmcblk2boot1 of=boot1.before.bin bs=512
sha256sum boot1.before.bin barebox.img
```

通过主机复制这两个备份，例如维护系统：

```sh
ssh -p 2222 root@169.254.212.2 'cat /tmp/boot1/boot1.before.bin' > "$PRIVATE/boot1.before.bin"
ssh -p 2222 root@169.254.212.2 'cat /tmp/boot1/extcsd.before.bin' > "$PRIVATE/extcsd.before.bin"
```

继续在设备 shell 写入，并比较完整分区（镜像后的尾部保持原内容）：

```sh
cd /tmp/boot1
cp boot1.before.bin expected.bin
dd if=barebox.img of=expected.bin bs=512 conv=notrunc
trap 'echo 1 > /sys/class/block/mmcblk2boot1/force_ro; blockdev --setro /dev/mmcblk2boot1' EXIT
echo 0 > /sys/class/block/mmcblk2boot1/force_ro
blockdev --setrw /dev/mmcblk2boot1
dd if=barebox.img of=/dev/mmcblk2boot1 bs=512 conv=notrunc
sync
dd if=/dev/mmcblk2boot1 of=readback.bin bs=512
cmp expected.bin readback.bin
sha256sum readback.bin
echo 1 > /sys/class/block/mmcblk2boot1/force_ro
blockdev --setro /dev/mmcblk2boot1
trap - EXIT
```

这会替换 boot1；断电或错误镜像可能导致引导失败，需要 ROM 下载恢复。boot0 是原厂启动内容；覆盖 boot0 会失去原厂引导路径。这里的 boot 分区 force_ro 与 blockdev 操作是写入时的局部操作，不是系统启动的全盘只读策略。

## 选择启动分区

读取当前 EXT_CSD[179]：

```sh
extcsd-read /dev/mmcblk2 > /tmp/extcsd.bin
od -An -tx1 -j179 -N1 /tmp/extcsd.bin
```

当前部署值为 `0x50`（BOOT_ACK 与 boot1）。已经为 0x50 时更新镜像无需更改它。首次由原厂 `0x48`（boot0）切换时，使用维护工具 mmc-utils：

```sh
mmc extcsd write 179 0x50 /dev/mmcblk2
mmc extcsd read /dev/mmcblk2
```

更改 179 会改变下次启动来源；错误值可能使设备无法正常引导。它不是熔丝，可在可用维护系统中恢复备份中的值。恢复原厂 boot0 启动时，先确认自己的 boot0 备份和内容可用，再恢复原来 179 的值；不能靠选择 boot0 恢复已被覆盖的用户区。

## shell、bootargs 和 USB

默认环境不保存到 eMMC。当前 bootargs 为 `linux.bootargs.k4` 与 `nv/linux.bootargs.console` 等命名空间的组合。`nv/linux.bootargs.console` 默认含 `fbcon=map:1 logo.nologo`。在 shell 可查看和改变变量，例如：

```sh
printenv global.linux.bootargs.k4
nv linux.bootargs.console="fbcon=map:1 logo.nologo"
```

这里的更改只影响当前会话；要改变镜像默认值，修改 `defaultenv-v9/nv/linux.bootargs.console` 后重建。

统一分区表：

```sh
global.system.partitions="/dev/mmc2.boot0(boot0)r,/dev/mmc2.boot1(boot1)r,/dev/mmc2(user)r"
```

`r` 为 DFU Readback 标志，表中三块区域可被 USB 存储功能访问，写入会改变设备数据。按需一次启用一种功能：

```sh
usbgadget -a -A
```

上例为 fastboot；DFU 使用 `usbgadget -a -D`，UMS 使用 `usbgadget -a -S`。组合 DFU/fastboot 存在[枚举问题](KNOWN-ISSUES.md)。维护 FIT 与恢复 boot1 备份的流程见[恢复指南](RAM-BOOT.md)。
