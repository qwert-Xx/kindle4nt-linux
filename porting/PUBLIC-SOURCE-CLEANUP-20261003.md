<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# 公开源文件清理与审查修正（2026-10-03）

本次仅修改项目工具、文档和历史记录中的环境标识。不访问设备、不 push，
不改驱动或内核代码，不改变硬件参数、部署包或原有设备验收结论。
生效设备树仍为 `nxp/imx/imx50-kindle-k4.dtb`；本次验证仅限主机。

## 源文件与导出

12 个诊断探针从 `ip route show default` 的 `default via` 读取网关；没有
网关时输出 `SKIP gateway ping: no default route with a gateway`。历史主机工具
中的同类检查也采用这个做法。用户指南使用 `<发行版>`、`<用户>`、`<BUSID>`，
usbipd 使用默认 WSL 分发选择形式。记录中的本机路径改用 `$BACKUP`、`$TOOLS`
和 `$HOME`，保留产物相对路径、SHA、寄存器及测量值；网络示例改为 RFC5737
文档地址，SSID 字段改为 `<SSID>`。记录中的 WSL 内部 IP 改为 `<WSL-IP>`。

历史脚本的私人输入使用 `K4_WORK_DIR`、`K4_PRIVATE_DIR`、`K4_BUILD_DIR`、
`K4_SSH_HOST`、`K4_SSH_KEY`、`K4_WSL_DISTRO` 和 `K4_ALERT_SCRIPT` 环境变量。
已有路径参数改为显式必填，避免传入参数仍依赖本机默认路径。波形测试显式
传入 `--wbf`、`--wrf`、`--builtin-wbf` 和 `--builtin-wrf`。RAM 上传工具使用
`K4_BUILD_DIR`、`K4_KEXEC`、`K4_SSH_TARGET`、`K4_SSH_KEY`，known_hosts 默认
为 `$HOME/.ssh/known_hosts`，可由 `K4_KNOWN_HOSTS` 覆盖。

验收记录移至 [清理验收](CLEANUP-VALIDATION-20261003.md) 和
[驱动额度验收](DRIVER-LIMITS-VALIDATION-20261003.md)。导出器对所选源文件
直接复制，不再改写 Markdown；内核补丁拆分和许可 sidecar 生成方式保持原有流程。

## 审查与验证范围

`project/audit_public.py` 默认检查 Git 跟踪的当前工作文件，并以发现或私有
二进制输入作为非零退出条件。它检测 Linux 用户路径、挂载盘路径、Windows
盘符路径、WSL UNC、反斜杠 home 路径、RFC1918 IPv4、私钥头，以及带引号或
不带引号的凭据值。空字段、变量和占位示例可用；RFC5737 和项目 USB 链路
本地地址不会作为 RFC1918 命中。压缩图片不进行随机字节文本匹配。

完整 Linux 工作树中，仅排除与上游 v6.6.157 相同的文件；报告逐项列出排除
文件。上游网络示例、自测及源代码中的地址不是本机配置，不为清理而改写。
公开补丁树没有这个排除。`--history` 另行列出所有可达旧 blob 的发现，不以
旧历史替代当前源文件检查，也不抹去或改写已有提交。

主机回归覆盖新增路径格式、三类私有网段、文档/USB地址、凭据与私钥、当前
未提交文件内容及保留历史，并对 12 个实际探针的网关检查段模拟有网关、无
路由、无 via 路由三种情况。公开树还需通过 project 联合测试、REUSE lint
与复制源文件逐字节比对。设备、RAM/kexec、冷启动和持久部署均未进行新验证。
