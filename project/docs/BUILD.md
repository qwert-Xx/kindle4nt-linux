<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# 构建

所有命令在仓库根执行。Linux 主机需 Python 3.12、make、ARM 交叉 GCC/binutils、dtc、U-Boot mkimage、patch、tar/gzip、mke2fs/debugfs、dpkg-deb、openssl、ssh-keygen、pkg-config 及构建用户态所需的开发库。内核当前工具链为 ARMhf GCC 13.3 / binutils 2.42；精确复现时以 `project/alpine/kernel.lock.json` 为准。BusyBox 使用锁定 Linaro 4.9.4 工具链，见[用户态配方](../userspace/README.md)。Alpine 组装自行从锁定缓存提取 QEMU；维护 applet 安装直接读取 busybox.links。

## 输入目录

以下约定贯穿指南：

```sh
PRIVATE="$HOME/k4-inputs"
OUT="$HOME/k4-output"
mkdir -p "$PRIVATE" "$OUT"
```

`PRIVATE` 保存自己的固件/波形、Wi-Fi 配置、授权公钥、主机密钥、第三方归档和 JSON 配方。固件目录按目标 `/lib/firmware` 布局，含 ath6kl 固件/校准和签名 regulatory.db。默认显示从面板 flash 获取 WBF 并解码，外部波形不是构建必填项；完整获取命令见[显示波形](WAVEFORMS.md)。没有可用波形可启动、维护和联网，显示不可用。

APK 缓存可用以下命令准备；已有缓存也会校验锁定哈希：

```sh
python3 project/alpine/download.py --out "$PRIVATE/alpine-cache"
```

维护用户态先按[用户态配方](../userspace/README.md)构建，保存 `bin/` 和同配置的 `busybox.links`。mmc-utils 与 mke2fs 是独立维护工具：

```sh
python3 project/userspace/maintenance.py --cache "$PRIVATE/source-cache" --out "$OUT/mmc-tools"
python3 project/userspace/e2fsprogs.py --source "$PRIVATE/e2fsprogs-1.47.1.tar.xz" --out "$OUT/e2fsprogs"
```

## 输入 JSON

`inputs.json` 引用维护 RAM 根逐文件配方，并给出 Alpine 的显式输入路径。相对路径以 JSON 所在目录为基准。下面的 `SHA256_OF_RAM_RECIPE` 是 `sha256sum "$PRIVATE/ram-recipe.json"` 的结果：

```json
{
  "kernel_profile": "production",
  "release": "6.6.157-k4-production",
  "inputs": {
    "ram_recipe": {"path": "ram-recipe.json", "sha256": "SHA256_OF_RAM_RECIPE"}
  },
  "alpine": {
    "cache": "alpine-cache",
    "firmware_dir": "firmware",
    "wifi_config": "wpa_supplicant.conf",
    "authorized_keys": "authorized_keys",
    "ssh_host_key": "ssh_host_ecdsa_key"
  }
}
```

`authorized_keys` 与 `ssh_host_key` 参数可选；要通过 SSH 登录需实际安装授权公钥。省略 Alpine 主机密钥会在首次运行生成。`tools_dir` 可选，提供项目 ELF 工具。项目文本从 `rootfs/` 安装，诊断不进默认产物。

维护配方 `ram-recipe.json` 的 `entries` 描述外层 cpio；`filesystem_recipe` 引用内嵌 ext3 根配方，`filesystem_recipe_sha256` 校验它。内层含 `image_bytes`、`uuid`、`entries` 和：

```json
"busybox_links": {"path": "/absolute/userspace/busybox.links", "sha256": "SHA256_OF_LINKS"}
```

每个条目包含 `name`（相对目标路径）、`kind`、`mode`（十进制权限）；file 使用 `source`/`sha256`，link 使用 `target`，char/block 使用 `major`/`minor`。例如 755 是十进制 493，644 是 420。外部文件逐项校验；已由 `rootfs/common`、`rootfs/busybox/maintenance` 和 `rootfs/busybox/ram` 管理的目标文件从仓库读取。模块由所选内核的 modules_install 结果加入。

从新用户态和私有输入生成这两份配方的完整可复制示例见[维护配方示例](MAINTENANCE-INPUTS.md)。

## 三种入口

### 从源码构建（默认）

完整研究仓库已含 K4 Linux 源码，在仓库根运行：

```sh
make -C project check INPUTS="$PRIVATE/inputs.json" OUT="$OUT/images"
make -C project images INPUTS="$PRIVATE/inputs.json" OUT="$OUT/images"
```

源码默认 `k4_defconfig` 加 production 片段。`SOURCE=/path/to/linux` 或 JSON 的 `kernel_source` 可指定其它已应用 K4 改动的 Linux 树；公共导出中的 `kernel/patches/series` 按顺序应用于 v6.6.157，debug 再应用 debug-patches。当前完整研究仓库无需重复应用补丁。

公开发布树提供补丁与配方，不内嵌上游 Linux 源码，也不使用子模块。先从固定版本与 SHA256 获取上游，验证开发者签名，再按 series 应用生产补丁：

```sh
mkdir -p "$PRIVATE/kernel-source"
python3 sources/fetch.py --cache "$PRIVATE/source-cache" --name Linux --extract "$PRIVATE/kernel-source"
LINUX="$PRIVATE/kernel-source/linux-6.6.157"
while IFS= read -r patch_name; do
    patch -d "$LINUX" -p1 < "kernel/patches/$patch_name"
done < kernel/patches/series
make -C project check SOURCE="$LINUX" INPUTS="$PRIVATE/inputs.json" OUT="$OUT/images"
make -C project images SOURCE="$LINUX" INPUTS="$PRIVATE/inputs.json" OUT="$OUT/images"
```

上游下载验证需要 xz、GnuPG 和可用的 kernel.org WKD 网络访问；版本、SHA256 与签名指纹见 `sources/manifest.json`。离线缓存另加 `--offline`，须提前具备归档、签名和已验证的开发者公钥。已有上游源码也可直接应用补丁。公开树后续的 kernel/images/reproduce 命令均需 `SOURCE="$LINUX"` 或输入 JSON 的 `kernel_source`；debug 再按 `kernel/debug-patches/series` 应用补丁。

只构建内核时：

```sh
python3 project/build.py --inputs "$PRIVATE/inputs.json" --out "$OUT/kernel"
```

### 使用预编译内核

JSON 的 `inputs` 额外提供 `zImage`、`dtb`、`modules` 的 `path/sha256`。modules 是包含 `lib/modules/RELEASE` 的 tar 归档，排除指向构建主机的 `build`/`source` 链接。构建会检查 ARM 模块和内核 release 匹配：

```sh
make -C project images MODE=prebuilt INPUTS="$PRIVATE/prebuilt-inputs.json" OUT="$OUT/prebuilt"
```

### 精确复现

源码重建后按 `kernel.lock.json` 比较内核、DTB 和模块 SHA，且核对锁定工具链：

```sh
make -C project images MODE=reproduce INPUTS="$PRIVATE/inputs.json" OUT="$OUT/reproduce"
```

reproduce 用于核对已发布版本：使用该发布对应的源码、配置、工具链和输入，按发布锁比较新内核、DTB 与模块。当前开发源码或配置修改使用 source 模式；发布锁随正式发布的内核与产物一起更新。

## 配置与输出

`project/build.py --config` 在 preset 后覆盖配置。`OUT` 环境变量可设置默认目录；`--clean` 清理该目录重新构建：

```sh
python3 project/build.py --inputs "$PRIVATE/inputs.json" --out "$OUT/kernel" --config "$PRIVATE/extra.config" --clean
```

统一 images 入口目前不转发 `--config`/`--clean`；可在 JSON 中提供哈希锁定的 `inputs.config` 作为覆盖片段，或先用 build.py，再用 prebuilt 方式组装。输出放在源码外，或本仓库 ignored 的 `.k4-build/`；输入与输出使用不同目录，清理会删除输出内容。

统一入口生成 `alpine/rootfs.tar.gz`、`alpine-ram/alpine-ram.cpio.gz`、`maintenance/ram.cpio.gz`，报告保存在各输出目录的 JSON 中。barebox 单独构建，见[boot1](BAREBOX-BOOT1.md)。构建完成后先准备[维护 FIT](RAM-BOOT.md)，再进行安装。

## 主机检查

```sh
python3 -m unittest discover -s project -p 'test_*.py'
python3 project/userspace/test_compare.py
```

这些检查验证配方、归档、模块匹配与部署脚本的主机模拟；真实硬件行为见[已知问题](KNOWN-ISSUES.md)。
