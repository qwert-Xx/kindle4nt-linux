<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Kindle 4 Non-Touch Linux

本项目将 Linux 6.6.157 与 Alpine Linux 移植到 **Kindle 4 Non-Touch D01100**（Yoshi/Tequila，i.MX50）。提供 barebox boot1 引导、Alpine eMMC 系统、Alpine RAM 系统和 BusyBox RAM 维护系统。其它 Kindle 型号与面板尚不在支持范围内。

这是新用户的起点。先[备份整机 eMMC](docs/RAM-BOOT.md#整机-emmc-备份)，再完成[构建](docs/BUILD.md)，准备[RAM 维护与恢复](docs/RAM-BOOT.md)，然后安装 [boot1](docs/BAREBOX-BOOT1.md) 和 [Alpine](docs/EMMC-ROOT.md)。使用前阅读[已知问题](docs/KNOWN-ISSUES.md)。

## 目录

| 目录 | 内容 |
|---|---|
| `project/` | 构建入口、用户态配方和使用文档 |
| `rootfs/` | 按目标安装路径组织的启动脚本、服务与配置 |
| `porting/barebox-emmc/` | barebox v9 源码构建配方、板级补丁和 FIT 模板 |
| `diagnostics/` | 可选诊断工具，不进入默认镜像 |
| `arch/`、`drivers/`、`include/` | Linux 源码及 K4 移植实现 |
| `sources/` | 上游归档下载、用户态缓存校验工具 |
| `porting/` | 硬件参考与历史研究记录；带日期的报告记录当时结果 |

## 第一步：整机备份

动手前先完整备份 eMMC。备份只需要先在主机上构建 barebox（`python3 porting/barebox-emmc/build.py`，见[boot1 指南](docs/BAREBOX-BOOT1.md#构建)），不需要私有输入。[整机备份](docs/RAM-BOOT.md#整机-emmc-备份)从 i.MX50 ROM USB 下载模式把 barebox 加载到 RAM，再用 DFU 读回 user（约 1.9 GB）、boot0、boot1 三个区域，不写设备；另按[boot1 指南](docs/BAREBOX-BOOT1.md)保存 EXT_CSD。boot0 保存原厂启动内容，覆盖它会失去原厂恢复路径。备份含固件、设备身份和个人数据，只放在自己的主机上。

## 准备自己的输入

构建主机使用 Linux。Windows 用户可在 WSL 中构建；可用 `wsl.exe -d <发行版>` 进入 Linux shell。依赖、工具链及输入 JSON 的完整说明在[构建指南](docs/BUILD.md)。

先按[从整机备份准备私有输入](docs/FIRMWARE-EXTRACTION.md)提取固件并准备配置、密钥和监管数据库。固件和设备数据不随仓库分发。将以下文件放在仓库外，并从自己的设备备份中取得与硬件匹配的内容：

- ath6kl AR6003 固件和板级校准数据；保持 `/lib/firmware/ath6k/AR6003/hw2.1.1/` 的目标布局。
- EPDC 默认从面板 flash 获取 WBF 并在内核解码，无需外部波形。备份与获取步骤见[显示波形](docs/WAVEFORMS.md)。没有可用波形仍可启动、维护和联网，显示不可用。
- Wi-Fi 的 `wpa_supplicant.conf`，以及 root 的 `authorized_keys`。
- 可选 SSH 主机密钥：Alpine 使用 OpenSSH ECDSA 格式，维护系统使用 Dropbear 格式。Alpine 省略主机密钥时由运行中的服务生成；RAM Alpine 每次启动可能产生新身份。维护根需预装 Dropbear 主机密钥，因为内嵌根以只读方式挂载。

SSH 登录使用你自己的私钥；镜像只需要授权公钥。Wi-Fi 配置和主机私钥属于私有输入，生成的运行包也可能含私有数据。

## 构建与安装

在仓库根运行，`PRIVATE` 指向准备好的输入目录，`OUT` 指向构建输出：

```sh
PRIVATE="$HOME/k4-inputs"
OUT="$HOME/k4-output"
make -C project images INPUTS="$PRIVATE/inputs.json" OUT="$OUT/images"
```

这一入口依次生成：

| 产物 | 用途 |
|---|---|
| `alpine/rootfs.tar.gz` | 在目标分区格式化后解包的 eMMC 系统，含 `/boot` |
| `alpine-ram/alpine-ram.cpio.gz` | 完全在 RAM 中运行的 Alpine |
| `maintenance/ram.cpio.gz` | BusyBox RAM 维护系统，部署与修复时使用 |

默认从本仓库源码构建。已有内核可选 `MODE=prebuilt`，详见[构建指南](docs/BUILD.md)。barebox 单独构建：

```sh
python3 porting/barebox-emmc/build.py --output "$OUT/barebox-v9"
```

安装命令集中在[boot1 指南](docs/BAREBOX-BOOT1.md)和[Alpine 部署指南](docs/EMMC-ROOT.md)。boot1 写入会替换引导程序；EXT_CSD[179] 决定启动分区；Alpine 部署会格式化并覆盖指定分区的数据。

## 日常连接与恢复

Alpine 在 USB 地址 `169.254.212.2` 和 Wi-Fi 地址上提供 OpenSSH（22 端口，公钥登录及 SFTP）。维护系统通过 USB 提供 Dropbear（2222 端口）与 ACM 控制台：

```sh
ssh root@169.254.212.2
ssh -p 2222 root@169.254.212.2
```

barebox 启动时有 5 秒倒计时，按 Ctrl-C 进入 shell。启用 fastboot 后可将维护 FIT 启动到 RAM，再重新部署 Alpine 或恢复 boot1。若引导程序无法运行，长按电源键强制复位，松开电源键时按住方向键“下”，进入 i.MX50 ROM USB 下载模式。完整流程见[恢复指南](docs/RAM-BOOT.md)。

Alpine 使用官方 OpenRC watchdog 服务，配置在 `/etc/conf.d/watchdog`；维护系统持续运行 BusyBox watchdog。重启进入当前选择的启动分区。

Linux 和 barebox 使用各自源码的许可；项目工具与第三方用户态的许可见[用户态文档](userspace/README.md)和[第三方说明](THIRD-PARTY.md)。

历史验收记录：[CLEANUP-VALIDATION](../porting/CLEANUP-VALIDATION-20261003.md)。

历史验收记录：[DRIVER-LIMITS-VALIDATION](../porting/DRIVER-LIMITS-VALIDATION-20261003.md)。
