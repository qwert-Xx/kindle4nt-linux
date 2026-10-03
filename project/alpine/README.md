<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Alpine 系统

构建总入口与输入 JSON 见[构建指南](../docs/BUILD.md)，部署见[eMMC 指南](../docs/EMMC-ROOT.md)。`build.py` 使用 `packages.lock.json` 中锁定的 Alpine 3.24.2 armv7 包、官方索引和签名；`ram.py` 将同一根目录转换为 RAM 镜像。

## 网络与 SSH

官方 wpa_supplicant 2.11-r4、wpa_cli OpenRC 服务及默认 `wpa_cli.sh` 处理关联和 DHCP 事件；networking/ifupdown-ng 配置 wlan0 DHCP 与 usb0 静态 `169.254.212.2/16`。

官方 OpenSSH 10.3_p1-r1 与 sshd OpenRC 服务监听 22 端口及所有 IPv4/IPv6 地址，root 仅使用公钥登录，SFTP 使用 internal-sftp。USB gadget 在 k4-platform 中初始化，ttyGS0 提供 root shell。维护根另用 Dropbear/2222。

`--firmware-dir` 是外部 `/lib/firmware` 的内容，`--wifi-config` 是外部 Wi-Fi 配置。`--authorized-keys` 提供 root 公钥授权（安装权限 600）；`--ssh-host-key` 接受外部 OpenSSH ECDSA 私钥（600），公钥由 ssh-keygen 派生（644）。省略主机密钥时，官方 sshd 服务首次启动生成 ECDSA 密钥。构建过程不生成随机身份；运行时生成的密钥另行保存。

## Watchdog 与源文件

官方 OpenRC watchdog 服务读取 `/etc/conf.d/watchdog`，当前参数为 `-T 30 -t 10`、设备 `/dev/watchdog`。块设备保持内核默认访问状态。

项目配置来源为 `rootfs/common/` 与 `rootfs/alpine/`，按目标路径覆盖官方根。诊断工具从默认产物中过滤。`--tools-dir` 可提供项目 ELF 工具，默认不会拷贝诊断工具。

单独组装时运行 `python3 project/alpine/build.py --help` 查看与总入口相同的参数；`--clean` 清理指定输出，`OUT` 环境变量提供默认输出路径。APK 缓存由 `python3 project/alpine/download.py --out "$PRIVATE/alpine-cache"` 下载并校验。
