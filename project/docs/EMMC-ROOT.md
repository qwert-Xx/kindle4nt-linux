<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Alpine eMMC 部署

`alpine/rootfs.tar.gz` 包含 Alpine 根及 `/boot/zImage`、`/boot/imx50-kindle-k4.dtb`。barebox 默认启动用户区第一分区，Linux 参数为 `root=/dev/mmcblk2p1 rw rootwait`，不使用 initrd。根文件系统为 ext4。

## 上传

先[启动 RAM 维护系统](RAM-BOOT.md)，在主机使用自己的 SSH 私钥，上传归档、部署脚本和静态 mke2fs 工具包：

```sh
ssh -p 2222 root@169.254.212.2 'cat > /tmp/rootfs.tar.gz' < "$OUT/images/alpine/rootfs.tar.gz"
ssh -p 2222 root@169.254.212.2 'cat > /tmp/deploy-emmc-root' < project/tools/deploy-emmc-root
ssh -p 2222 root@169.254.212.2 'cat > /tmp/e2fsprogs.tar.gz' < "$OUT/e2fsprogs/maintenance.tar.gz"
sha256sum "$OUT/images/alpine/rootfs.tar.gz"
```

维护根提供 Dropbear 服务，没有默认安装 SCP/SFTP 服务程序，因此用 SSH 标准输入传输。正常 Alpine 可用 scp/SFTP。

## 选择目标与部署

部署会格式化并覆盖显式指定分区，原数据只能从自己的备份恢复。它不创建分区表，不写 boot0/boot1，不改 EXT_CSD。先保存用户区备份；在设备维护 shell 中核对实际容量、分区与挂载状态：

```sh
ls /sys/class/block/mmcblk*
cat /proc/partitions
cat /proc/mounts
mkdir -p /tmp/e2fsprogs
tar -xzpf /tmp/e2fsprogs.tar.gz -C /tmp/e2fsprogs
```

将下例 SHA256 替换为主机输出，目标分区按实际设备选择。默认 barebox 从第一分区启动，因此这个示例使用 `/dev/mmcblk2p1`：

```sh
sh /tmp/deploy-emmc-root /tmp/rootfs.tar.gz SHA256_FROM_HOST /tmp/e2fsprogs/maintenance /dev/mmcblk2p1
```

脚本要求四个参数，验证归档 SHA，拒绝已挂载的目标，使用静态 mke2fs 格式化 ext4，再解包、sync、重新只读挂载并验证 `etc/k4-rootfs.sha256` 中所有普通文件。最后打印 `Partition deployment and file readback verified`。这里的只读挂载是部署后的文件读回步骤，运行时根正常读写。

## 启动与修复

按[boot1 指南](BAREBOX-BOOT1.md)安装并选择 boot1 后，`reboot` 会进入当前 Alpine。USB 地址是 `169.254.212.2`，SSH 为 22 端口，root 公钥登录。

若根文件缺失或损坏，Ctrl-C 进入 barebox，fastboot 启动维护 FIT 后重新执行上述部署；boot1 无法运行时使用 ROM 下载恢复。入口见[恢复指南](RAM-BOOT.md)。部署到其它分区时，也需相应修改 barebox 的读取路径与 Linux root 参数。
