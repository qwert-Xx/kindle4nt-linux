<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# eMMC 根构建与部署

本页为操作配方，不会自动访问设备。已验证 BusyBox 直接 ext4 rw 根；不含 Alpine。内核使用 k4_defconfig + k4-production.config，kernel_profile=emmc-root，release=6.6.157-k4-production。MMC_BLOCK/ESDHC/EXT4/DEVTMPFS 为 builtin，无嵌入 initramfs；ATH6KL/ATH6KL_SDIO=m，根挂载后标准 coldplug 加载，固件不嵌入内核。硬件 DTS 与 production 相同。

## 离线构建

在公开补丁应用后的独立 Linux v6.6.157 源码树运行：

```sh
python3 project/build.py --source /absolute/linux --inputs /absolute/emmc-root.json --out /absolute/new-output --jobs 8
python3 project/userspace/e2fsprogs.py --source /absolute/e2fsprogs-1.47.1.tar.xz --out /absolute/new-mke2fs-output
python3 project/userspace/maintenance.py --source /absolute/mmc-utils-1.0.tar.gz --out out/new-mmc-maintenance
```

外部 JSON 选 kernel_profile=emmc-root，inputs.ram_recipe 提供路径与 SHA256；遵循 project/README.md 的逐文件根配方。所有固件、波形、Wi-Fi凭据、密钥和备份由拥有者在仓库外提供，不随公开 tar 发布。rootfs.tar.gz 固定名字排序/uid/gid/mtime/gzip元数据，清单记录模式、链接、文件SHA与特殊设备号。BusyBox watchdog 持续10秒喂30秒硬件狗；eMMC根没有有限 RAM guard。关机 sync/remount ro，重启使用已有生产 restart 路径。

维护工具使用 userspace 下的版本/SHA锁；mke2fs 和 mmc 均静态 ARM hard-float，无 INTERP。mke2fs.conf 显式 ext4 特性，禁用 discard、立即初始化 inode/journal，避免 host 默认新特性影响 barebox。维护工具不装入 production 根。maintenance.py 当前要求输出位于草案 out/；输出不要提交。

## 部署顺序（会覆盖 p1；仅按明确设备授权执行）

先准备完整主机备份和“下+复位→ROM→USB加载Linux RAM”恢复链，确认容量、枚举与剩余 guard 时间。既有 RAM 维护根保持存储只读，部署脚本显式临时解除后恢复。当前布局 p1 起始65536、大小3760128扇区；不改 MBR/前32MiB/boot0。这里 /dev/mmcblk2 是已验证枚举，换设备必须重新确认。root tar 与维护包先在 RAM 校验SHA。

1. `project/tools/deploy-emmc-root`：静态 mke2fs 格式化 p1 → mount → 解包 tar → sync → umount → 只读重挂载，以 /etc/k4-rootfs.sha256 校验全部文件 → 恢复主设备/p1只读。调用 `/bin/busybox sh deploy-emmc-root rootfs.tar.gz <SHA256> maintenance-directory`。挂载点在 /tmp；脚本不写 boot区、不延长有限 guard。
2. 按 [boot1说明](BAREBOX-BOOT1.md) 备份完整 boot1，写入离线核验的 v7 镜像，保留尾部并完整读回比较，恢复 force_ro 与 blockdev RO。不要写 boot0。
3. 最后单独激活：主设备暂时 setrw，`mmc extcsd write 179 0x50 /dev/mmcblk2`，重新 extcsd read 核对0x50，setro。不改 BOOT_BUS_WIDTH、fuse 或永久保护。
4. 正常 reboot 观察 v7 自动读取 /boot/zImage 与 /boot/imx50-kindle-k4.dtb，root=/dev/mmcblk2p1 rw rootwait；核对模块/固件、显示、网络、看门狗与文件SHA。保留已知可用 kernel/DTB 的 .prev；模块也须与 kernel 完整匹配。

## 回退

按住“下”配合复位进入 ROM，再由主机 USB 加载已验证 barebox/Linux RAM；或在 v7 两秒采样窗口按住“上”，进入 USB/YMODEM 主机加载，显式上传 kernel/DTB/RAM根并 bootm。Linux RAM 中用标准 mmc 修改179（0x48选择boot0），核对并恢复RO；p1已被替换时，改179本身不会恢复原厂root，须用备份重写p1或修复新的p1内容。不得把改179当作自动完整回滚。完整 boot1 读回流程见链接，不靠 guard 超时进行部署恢复。

## 验证范围

## 当前状态（2026-10-03，既有实机记录）

boot1 barebox v7 + eMMC p1 ext4 BusyBox 根已部署并读回核验，EXT_CSD[179]=0x50；无需电脑上传内核即可自动启动。按住“上”在两秒采样窗口进入 USB/YMODEM 主机加载；按住“下”配合复位进入 ROM 恢复。ath6kl_core/sdio 为模块，根挂载后由标准 modalias coldplug 加载固件；WDI 原厂方案 A 为 ALT2/0x0c，正常态由 restart pinctrl 持有。

正式 A 的 10 轮 reboot 健康检查全部通过（25.812–26.578 秒到 SSH），800/160MHz 两次 RTC STOP、16MiB 内存保持、4MiB 文件 sync 后 reboot 哈希保持均通过。看门狗停喂方案 A 48.047 秒、旧 DTB 对照 41.156 秒均自行经 v7 回 eMMC；旧对照未复现 ROM，不能认定 A 已唯一修复历史故障。两次采集总长各180秒，停喂后有效窗口仅167/171秒。

USB 物理拔线/电池独立冷启动、长时耐久及电源轨仍未验证；RAM 维护 guard 到期掉 ROM 的历史根因未定。新版模块 RAM 维护根尚未重新实机验证。Alpine feat/alpine-root 仅列路线图，未实机验证，未纳入本草案正式内容。
