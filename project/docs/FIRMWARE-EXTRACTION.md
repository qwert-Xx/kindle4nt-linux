<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# 从整机备份准备私有输入

本页从自己的 Kindle 4 Non-Touch D01100 原厂 eMMC 备份中提取无线固件，准备 Alpine eMMC、Alpine RAM 和 BusyBox RAM 维护系统共用的输入目录。先按入口的[整机备份](RAM-BOOT.md#整机-emmc-备份)取得 `user.bin`、`boot0.bin`、`boot1.bin` 和 EXT_CSD。本页只读取主机上的 `user.bin`，不连接 Kindle；boot0、boot1 和 EXT_CSD 留作恢复，不是根文件系统构建输入。

完整输入由三部分组成：从备份提取的四个 AR6003 文件、公开配方提供的监管数据库与构建依赖、用户自己准备的网络配置和 SSH 密钥。原厂整机备份并不能直接提供后两部分的全部内容。

## 准备

在 Linux 主机的仓库根、Bash shell 中执行。需要 Python 3、util-linux（sfdisk、losetup、mount、umount）和主机 ext3 支持；loop 挂载使用 sudo。构建依赖见[构建指南](BUILD.md)。

```sh
BACKUP="$HOME/k4-backup"
PRIVATE="$HOME/k4-inputs"
OUT="$HOME/k4-output"
mkdir -p "$PRIVATE" "$OUT"
```

这里的 `user.bin` 是整个 eMMC 用户区，而不是单独的 rootfs 分区。若备份流程使用其它名称，将命令中的路径替换成自己的文件名。输入、备份和构建输出均放在仓库外。

Windows/WSL 用户先进入 Linux shell，例如 `wsl.exe -d <发行版> -u <用户> --exec bash`。如果该 WSL 用户没有 sudo 权限，可用 `wsl.exe -d <发行版> -u root --exec bash` 执行挂载/提取，再将输出目录所有权交回构建用户；构建与提交仍使用普通用户。

## 原厂用户区包含什么

用自己的分区表计算偏移，不将下表的数值写死到提取流程：

```sh
sfdisk --json "$BACKUP/user.bin"
```

2026-09-23 原厂 DFU 备份的实际布局如下，扇区大小为 512 字节：

| 分区 | 起始扇区 | 扇区数 | 字节偏移 | 内容 |
|---|---:|---:|---:|---|
| p1 | 65536 | 716800 | 33554432 | ext3 原厂系统，含 /etc、/usr、/opt/ar6k |
| p2 | 782336 | 131072 | 400556032 | ext3 诊断系统，含工厂工具及另一套无线固件 |
| p3 | 913408 | 65536 | 467664896 | ext3 LocalVars，原厂 /var/local，含设置、数据库和日志 |
| p4 | 978944 | 2846720 | 501219328 | 用户存储容器；内部另有 MBR，FAT32 从容器内第 16 扇区开始，含 documents、system 等 |

p4 不能直接当作 FAT 文件系统挂载；如需查看它，先只读建立 p4 loop，再对该 loop 运行 `sfdisk --json`，按内部表计算 FAT 起点。上表样本的 FAT 在整机镜像字节偏移 501227520。提取固件只需要 p1，不需要打开个人文档、设置或日志。

## 一条命令提取固件

```sh
sudo python3 project/extract-firmware.py "$BACKUP/user.bin" "$PRIVATE"
```

脚本读取 sfdisk 的 JSON 分区表，按 `start × sectorsize` 和 `size × sectorsize` 建立 p1 的只读 loop，以 `ro,noload` 挂载 ext3（不重放日志），复制下表四个文件，然后卸载并释放 loop。它跟随备份内的 `active_calibration` 链接，包括绝对链接；不会从主机的 /opt 读取校准文件。输出采用普通 0644 权限，sudo 调用时所有权交回调用用户；再次执行会更新这四个目标文件，不改其它输入。

原厂源目录为 `/opt/ar6k/target/AR6003/hw2.1.1/bin/`，目标目录为 `$PRIVATE/firmware/ath6k/AR6003/hw2.1.1/`：

| 原厂文件 | 目标文件 | 性质 |
|---|---|---|
| otp.bin | otp.bin | OTP 初始化程序，属于固件；不是本机 OTP 内容的转储 |
| athwlan.bin | athwlan.bin | 无线运行固件 |
| data.patch.hw3_0.bin | data.patch.bin | 对应硬件版本的补丁 |
| active_calibration 指向的文件 | bdata.bin | 原厂选用的板级校准/射频配置 |

样本 p1 的 `active_calibration` 指向 `AR6103_QCA_15dBm_08032011.bin`。它是带固定版本名的原厂板型配置，不是已经证明逐台唯一的校准转储；同机型、同原厂固件/板型配置通常共用这些文件，但一台备份不能证明所有批次完全相同。因此提取自己的链接目标，不使用其它板型的通用 bdata。设备身份、MAC、芯片内 OTP 等逐机数据不由本工具克隆，本项目构建也不要求将这些数据作为单独私有文件提供。

p2 诊断系统存在不同版本和不同射频档位的文件；样本默认 `active_calibration` 与 `active_calibration_teq` 也不相同。正常系统构建使用 p1 的选择，不混用 p2。现代驱动的 API 1 文件名及既有 K4 无线验证见[无线移植记录](../../porting/WIFI.md#首次-ram-启动结果)。

脚本另写 `$PRIVATE/firmware-extraction.json`，记录分区偏移、源/目标路径和字节数，不记录凭据或文件内容。大小用于确认复制结果，不作为其它设备的支持条件。

## 手工只读挂载与复制

下面与脚本做同一件事，二选一即可。shell 的 EXIT trap 负责卸载；offset 和 sizelimit 均从分区表读取。

```sh
(
set -e
read -r OFFSET LENGTH < <(
    sfdisk --json "$BACKUP/user.bin" | python3 -c '
import json,sys
t=json.load(sys.stdin)["partitiontable"]; p=t["partitions"][0]
print(p["start"]*t["sectorsize"], p["size"]*t["sectorsize"])'
)
MOUNT=$(mktemp -d)
LOOP=$(sudo losetup --find --show --read-only \
    --offset "$OFFSET" --sizelimit "$LENGTH" "$BACKUP/user.bin")
trap 'mountpoint -q "$MOUNT" && sudo umount "$MOUNT"; sudo losetup -d "$LOOP"; rmdir "$MOUNT"' EXIT
sudo mount -o ro,noload "$LOOP" "$MOUNT"
SRC="$MOUNT/opt/ar6k/target/AR6003/hw2.1.1/bin"
DST="$PRIVATE/firmware/ath6k/AR6003/hw2.1.1"
mkdir -p "$DST"
cp "$SRC/otp.bin" "$DST/otp.bin"
cp "$SRC/athwlan.bin" "$DST/athwlan.bin"
cp "$SRC/data.patch.hw3_0.bin" "$DST/data.patch.bin"
CAL="$SRC/active_calibration"
while [ -L "$CAL" ]; do
    TARGET=$(readlink "$CAL")
    case "$TARGET" in
        /*) CAL="$MOUNT$TARGET" ;;
        *) CAL="$(dirname "$CAL")/$TARGET" ;;
    esac
done
cp "$CAL" "$DST/bdata.bin"
chmod 644 "$DST/"*
cmp "$SRC/otp.bin" "$DST/otp.bin"
cmp "$SRC/athwlan.bin" "$DST/athwlan.bin"
cmp "$SRC/data.patch.hw3_0.bin" "$DST/data.patch.bin"
cmp "$CAL" "$DST/bdata.bin"
echo "COPY_OK (4 files)"
)
```

这里的 cmp 只确认复制没有改变文件；不要求用户的文件匹配本机样本或某个发布产物的 SHA。

## 监管数据库：来自公开输入

原厂备份没有现代 cfg80211 所需的 `regulatory.db` 和 `regulatory.db.p7s`。p2 工厂工具中的 `regulatoryData_AG.bin` 不是它们的替代品。使用项目锁定的公开 wireless-regdb 配方：

```sh
python3 project/userspace/rebuild.py --components regdb \
    --cache "$PRIVATE/source-cache" --out "$OUT/regdb"
cp "$OUT/regdb/bin/regulatory.db" "$OUT/regdb/bin/regulatory.db.p7s" \
    "$PRIVATE/firmware/"
```

这一步下载归档并保留 SHA256 校验，生成数据库并验证随官方归档提供的签名。已有完整缓存可加 `--offline`。如果已经按[用户态配方](../userspace/README.md)构建全部组件，直接从 `$OUT/userspace/bin/` 复制这两个文件即可。监管数据库是公开的、与设备无关的数据。

最终固件目录：

```text
firmware/
├── regulatory.db
├── regulatory.db.p7s
└── ath6k/AR6003/hw2.1.1/
    ├── otp.bin
    ├── athwlan.bin
    ├── data.patch.bin
    └── bdata.bin
```

## 自己准备网络配置与密钥

原厂 /var/local 有 wifid 配置、账户数据库和日志，但它们不是本项目要求的 wpa_supplicant 配置或 SSH 授权文件。不必移植原厂账户数据，按自己要连接的网络重新准备：

```sh
umask 077
# 使用主机安装的 wpa_passphrase，交互输入无线密码。
printf 'ctrl_interface=/run/wpa_supplicant\n' > "$PRIVATE/wpa_supplicant.conf"
wpa_passphrase '你的SSID' | sed '/^[[:space:]]*#psk=/d' >> "$PRIVATE/wpa_supplicant.conf"
# 使用自己的 SSH 登录公钥；对应私钥留在登录主机。
cp "$HOME/.ssh/id_ed25519.pub" "$PRIVATE/authorized_keys"
# 维护根必需：Dropbear 格式的预置主机密钥。
dropbearkey -t ecdsa -s 256 -f "$PRIVATE/dropbear-hostkey"
# Alpine 可选：提供稳定的 OpenSSH 主机身份。
ssh-keygen -t ecdsa -b 256 -N '' -f "$PRIVATE/ssh_host_ecdsa_key"
```

如已有这些文件直接使用即可；缺少登录密钥时先用主机 ssh-keygen 创建自己的登录密钥。配置其它网络认证方式时按 wpa_supplicant 的配置格式编辑。Dropbear 主机密钥与 OpenSSH 私钥格式不同，不能直接互换。Alpine 可省略主机密钥，由首次启动的服务生成；维护只读根需要预置 Dropbear 密钥。Wi-Fi 配置和私钥属于用户私有输入，authorized_keys 含用户选择的公钥，不从别人的镜像复制。

EPDC 默认由内核读取面板 flash 波形，不要求从 user.bin 的 `/lib/firmware/imx/` 复制旧 EPDC 文件；外部波形与备份说明见[显示波形](WAVEFORMS.md)。原厂内核模块、device.bin、athtcmd_ram.bin、原厂诊断监管数据、boot0/boot1 均不是当前 Alpine/维护根必需输入。

## 接入构建并检查

在[维护配方示例](MAINTENANCE-INPUTS.md)中使用这个 PRIVATE，生成 filesystem.json、ram-recipe.json 和 inputs.json；Alpine 的 `firmware_dir` 指向 `firmware`，维护配方将同一目录装进 /lib/firmware。公开 APK/源码缓存与工具链按[构建指南](BUILD.md)准备。

```sh
for f in otp.bin athwlan.bin data.patch.bin bdata.bin; do
    test -s "$PRIVATE/firmware/ath6k/AR6003/hw2.1.1/$f"
done
test -s "$PRIVATE/firmware/regulatory.db"
test -s "$PRIVATE/firmware/regulatory.db.p7s"
make -C project check INPUTS="$PRIVATE/inputs.json" OUT="$OUT/images"
make -C project images INPUTS="$PRIVATE/inputs.json" OUT="$OUT/images"
```

当前 check 只验证顶层 JSON 的哈希引用，不检查固件目录内容；`INPUTS_OK` 不能单独证明固件齐全。前面的文件检查确认布局，images 实际组装根文件系统。验收看六个文件是否进入 /lib/firmware、配置和授权是否安装、根是否正常组装；不要求产物与某台设备的包逐字节一致。主机验收不能代替设备上的无线连接、RAM 启动或冷启动验收。

真实备份的执行命令、结果与范围见[主机实测记录](../../porting/FIRMWARE-EXTRACTION-VALIDATION-20261003.md)。
