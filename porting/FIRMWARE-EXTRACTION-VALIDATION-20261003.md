<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# 私有输入提取主机实测（2026-10-03）

基线 4621fbb46，独立 worktree $BACKUP/k4-fwdoc。备份为 2026-09-23 的 DFU 用户区文件；只处理主机文件，没有连接或操作设备。未提交备份、固件、校准、配置、密钥或构建包。

## 实际命令

在该 worktree 的 Linux shell 执行；此主机 kindle 用户没有免密 sudo，提取命令通过 Windows 的 `wsl.exe -d <发行版> -u root --exec bash` 执行，其余构建使用 kindle：

```sh
IMAGE=$BACKUP/kindle-k4-backup-2026-09-23/offline/mmcblk0-user-dfu-offline.img
P=$BACKUP/k4-fwdoc-private-20261003
python3 project/extract-firmware.py "$IMAGE" "$P"
chown -R kindle:kindle "$P"
```

实际输出：

```text
otp.bin: 2977 bytes
athwlan.bin: 53236 bytes
data.patch.bin: 140 bytes
bdata.bin: 1792 bytes
EXTRACT_OK firmware/ath6k/AR6003/hw2.1.1 (4 files)
```

另外按用户指南的手工命令执行一次（root shell 去掉 sudo，输出为 `$P/manual`），cmp 确认源与复制结果，随后比较脚本与手工提取的文件：

```text
COPY_OK (4 files)
MANUAL_SCRIPT_EQUIVALENT (4 files)
```

四个分区均只读检查过。p1/p2/p3 为 ext3；p4 首次直接挂载失败，读取其内部 MBR 得到起始扇区 16 后成功只读挂载 FAT32。提取流程仅挂载 p1；所有本次创建的挂载与 loop 均已释放。

公开 regdb 归档复制到本次自己的缓存，再运行项目现有配方，保留归档 SHA256 校验与 CMS 签名验证：

```sh
P=$BACKUP/k4-fwdoc-private-20261003
mkdir -p "$P/source-cache"
cp $BACKUP/tool-sources/wireless-regdb-2026.09.03.tar.xz "$P/source-cache/"
python3 project/userspace/rebuild.py --cache "$P/source-cache" \
    --out "$P/regdb-build-complete" --components regdb --offline \
    > "$P/regdb-build-complete.log" 2>&1
cp "$P/regdb-build-complete/bin/regulatory.db" \
    "$P/regdb-build-complete/bin/regulatory.db.p7s" "$P/firmware/"
```

使用主机已有的用户自备 Wi-Fi 配置、公钥及维护 Dropbear 主机密钥，复制到本次输入目录；这些文件不来自原厂固件提取，内容不展示：

```sh
cp $BACKUP/k4-new-user-inputs-20261003/wpa_supplicant.conf \
   $BACKUP/k4-new-user-inputs-20261003/authorized_keys \
   $BACKUP/k4-new-user-inputs-20261003/dropbear-hostkey "$P/"
```

运行 Alpine 的真实组装入口，使用已有生产内核、DTB、模块和锁定 APK 缓存，不添加 --verify-release：

```sh
K=$BACKUP/k4-new-user-output-20261003/images/maintenance
python3 project/alpine/build.py \
    --cache $BACKUP/k4-new-user-inputs-20261003/alpine-cache \
    --firmware-dir "$P/firmware" \
    --wifi-config "$P/wpa_supplicant.conf" \
    --authorized-keys "$P/authorized_keys" \
    --kernel "$K/arch/arm/boot/zImage" \
    --dtb "$K/arch/arm/boot/dts/nxp/imx/imx50-kindle-k4.dtb" \
    --modules "$K/root-modules/lib/modules" \
    --out "$P/alpine-complete" > "$P/alpine-complete.log" 2>&1
```

退出码 0，生成 rootfs.tar.gz 和 build-report.json。检查归档中的六个文件确实与本次输入对应，并检查网络配置、公钥安装路径；没有与旧根包或发布包比较哈希。

按 MAINTENANCE-INPUTS.md 中完整 Python 示例生成配方，使用以下 PRIVATE/OUT（该示例只写 PRIVATE，OUT 的用户态文件只读使用）：

```sh
export PRIVATE=$BACKUP/k4-fwdoc-private-20261003
export OUT=$BACKUP/k4-new-user-output-20261003
# 执行 MAINTENANCE-INPUTS.md 中的 Python 示例。
make -C project check INPUTS="$PRIVATE/inputs.json" OUT="$PRIVATE/images"
```

实际检查输出：

```text
Created filesystem.json, ram-recipe.json, inputs.json
INPUTS_OK
etc/wpa_supplicant/wpa_supplicant.conf installed
root/.ssh/authorized_keys installed
ALPINE_FIRMWARE_OK (6 files)
MAINTENANCE_RECIPE_OK (6 files in inner and outer recipes)
kernel_release=6.6.157-k4-production
module_count=23
device_operations=False
```

## 范围与剩余输入

通过的是：真实备份只读提取、手工/脚本复制结果一致、公开监管数据库配方、Alpine 主机组装、维护内外配方文件布局、统一 check 入口。固件目录共六个文件；未将样本大小或 SHA 设为其它设备的支持前提。

未重新构建内核或完整维护镜像，未进行无线连接、RAM 启动、持久部署或冷启动测试。设备上 ath6kl API 1 的既有验证见 porting/WIFI.md，本次没有新增设备结论。

用户仍需自备网络配置、SSH 登录授权公钥、维护根 Dropbear 主机密钥；Alpine OpenSSH 主机密钥可选。公开 APK、源码缓存、工具链和用户态按构建指南准备。默认面板 flash 波形不需要作为外部输入提取。

本机产物、提取 JSON、生成配方和日志保存在 `$BACKUP/k4-fwdoc-private-20261003/`，不进入 Git。
