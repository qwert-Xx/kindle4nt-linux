<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# 用户态构建

Alpine 使用官方 APK；本目录构建 BusyBox 维护根所需的第三方工具，以及两种根共用的 `k4-epd-update`。源码按 `sources.lock.json` 中的来源 URL 自动下载到缓存，使用 `sources/fetch.py` 的同一机制校验 SHA256；构建直接读取缓存。

```sh
python3 project/userspace/rebuild.py --cache "$PRIVATE/source-cache" --out "$OUT/userspace"
```

已有缓存可加 `--offline`，缺少文件或哈希不符会报错；`--cache` 指定缓存目录，默认 `~/.cache/k4/sources`。

默认组件：BusyBox 1.31.1、独立 modutils、Dropbear 2024.86、wpa_supplicant 2.11、libnl 3.12.0、iw 6.17、wireless-regdb 2026.09.03 和项目刷屏工具（`epd`）。可用 `--components busybox` 等选择组件。`--clean` 清理输出，环境变量 `OUT` 设置默认输出。

BusyBox 使用锁定的 Linaro GCC 4.9.4-2017.01 arm-linux-gnueabi 工具链；其余使用 ARMhf GCC。BusyBox 构建同时运行 `make busybox.links`，将清单输出为 `OUT/userspace/busybox.links`，二进制输出在 `OUT/userspace/bin/`。维护根配方引用同一配置生成的清单，详见[构建输入](../docs/BUILD.md)。

regulatory.db 从官方源码生成；签名复制自锁定的官方归档。

Dropbear 关闭密码认证；维护 Wi-Fi 使用 nl80211。Alpine 使用自己的标准网络和 SSH 服务，见[Alpine 文档](../alpine/README.md)。kexec 为可选工具，当前恢复入口使用 barebox 与 ROM，见[恢复指南](../docs/RAM-BOOT.md)。

[维护工具](MAINTENANCE.md)单独提供 mmc-utils 与 mke2fs。固件、校准、波形和凭据来自外部输入。BusyBox/kexec 使用 GPL-2.0 系列许可，libnl 为 LGPL-2.1 系列，wpa_supplicant 为 BSD，iw/regdb 为 ISC，Dropbear 含 MIT 和多来源条款。构建与分发时保留对应源码及 COPYING/LICENSE；详见[第三方说明](../THIRD-PARTY.md)。

只构建刷屏工具可用 `--components epd --offline`；无需下载输入，输出为
`bin/k4-epd-update`，使用仓库的 lf-6.6 UAPI，静态链接 ARMhf libc。
Alpine 使用 `tools_dir` 安装，维护根配方加入对应文件与 SHA256；
操作方式见[显示接口](../docs/DISPLAY.md)。
