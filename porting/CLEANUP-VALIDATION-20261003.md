<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# 构建清理验收（2026-10-03）

基线 `4621fbb46`，分支 `cleanup/no-byte-locks`，独立工作树 `$BACKUP/k4-cleanup2`。以 kindle 用户构建和提交；不 push、不访问设备、不写其它 worktree 或冻结包。

## 删除与修改

删除 source/reproduce 双重验收中的 reproduce 模式和所有 `--verify-release`；内核构建保留 source（默认）和 prebuilt。删除内核 zImage/DTB/模块产物锁、用户态工具链版本锁、`--reference`、ELF 字节比较工具、冻结包哈希验收工具以及只服务精确复现的测试。内核 baseline_metadata 特例、固定构建时间、BusyBox 时间重写、ext3 假时间/hash_seed 模式和重复构建字节比较一并移除。

上游归档、工具链归档和 APK 的下载 SHA256、Linux/Alpine/regulatory.db 签名校验、显式输入校验和输入输出重叠检查保留。报告中本次输出的哈希仅供记录，不用于要求与历史产物一致。regulatory.db 仍从源码生成并校验官方签名。

删除 `project/configs/reference-a8accb2a8/` 的三份参考配置与 SHA256SUMS.json；profile 检查保留功能配置、恢复内建项、诊断隔离、模块安装与链接检查，不依赖历史配置或二进制样本。

Alpine/eMMC、Alpine RAM 与 BusyBox 维护根的 USB serial/manufacturer 为 `kindle4nt`，product 为 `Kindle 4 Non-Touch`。USB 功能、VID/PID、网络地址和硬件设备树不变。

逐文件清单（D 删除，M 修改，A 新增）：

```text
M	AGENTS.md
M	porting/STOCK-CONFIG-DIFFERENCES.md
M	porting/barebox-emmc/build.py
M	project/README.md
M	project/alpine/README.md
M	project/alpine/build.py
D	project/alpine/kernel.lock.json
M	project/alpine/verify.py
M	project/build.py
D	project/configs/reference-a8accb2a8/SHA256SUMS.json
D	project/configs/reference-a8accb2a8/k4-debug.config
D	project/configs/reference-a8accb2a8/k4-lifecycle.config
D	project/configs/reference-a8accb2a8/k4-production.config
M	project/docs/BUILD.md
M	project/docs/MAINTENANCE-INPUTS.md
M	project/docs/NEW-USER-VALIDATION.md
M	project/docs/RAM-BOOT.md
M	project/images.py
M	project/rootfs.py
M	project/test_build.py
R061	project/test_repro_filesystem.py	project/test_filesystem.py
M	project/test_rootfs.py
M	project/userspace/README.md
M	project/userspace/build_support.py
D	project/userspace/compare.py
M	project/userspace/e2fsprogs.py
M	project/userspace/rebuild.py
D	project/userspace/test_compare.py
D	project/userspace/toolchain.lock.json
M	project/userspace/wifi.sh
D	project/verify-frozen-package.py
M	project/verify_k4_defconfig.py
M	project/verify_profiles.py
M	rootfs/alpine/etc/k4/platform-start
M	rootfs/busybox/maintenance/etc/init.d/rcS

```

## 主机验收

实际输出位于工作树 ignored `.k4-build/`；含私有测试输入和镜像，不入 Git。维护配方使用本次重建的用户态；Alpine 缓存与设备固件只读复用既有外部输入。

| 检查 | 输出 |
|---|---|
| `python3 -m unittest discover -s project -p 'test_*.py'` | 30 tests, OK |
| barebox `run-tests.py` | offline 8 tests, OK；plugin 7 tests, OK |
| `python3 porting/test-waveform-inspect.py` | 8 tests, OK |
| 用户态全组件源码构建 | busybox、modutils、dropbear、wifi、regdb 成功 |
| regdb 单独离线重建 | CMS Verification successful |
| barebox 源码构建 | plugin 镜像成功；头部、DCD 表、ARM ROM ABI 与执行序列检查通过 |
| `make -C project check` | INPUTS_OK |
| `make -C project images`（默认 source 模式） | IMAGES_OK alpine/rootfs.tar.gz alpine-ram/alpine-ram.cpio.gz maintenance/ram.cpio.gz |
| Alpine `verify.py --build ... --ram ...` | 320 ELF、214 动态 ELF、23 模块、85 包签名；ABI、归档、网络/SSH/watchdog 服务依赖与 QEMU 功能检查通过 |
| 维护根与三根 gadget 检查 | FUNCTIONAL_CHECKS_OK；新字符串、shell 语法、设备节点、cat/uname/modprobe 链接、维护 ELF 与 QEMU 检查通过 |

modutils 配置关闭 CONFIG_SHOW_USAGE，其帮助请求退出 1 且不输出帮助文本，检查按实际配置验收。QEMU 不运行 PID1，不启动服务，不加载宿主模块。

首次 Alpine 组装因本次复制的私有 SSH 测试密钥权限为 0644 被 ssh-keygen 拒绝；将本 worktree 的复制件改为 0600 后重跑默认入口成功。未修改项目的 SSH 权限处理。

日志：`.k4-build/tests.log`、`barebox-tests.log`、`waveform-tests.log`、`userspace.log`、`userspace/build.log`、`regdb-verification.log`、`barebox.log`、`check.log`、`images-final.log`、`alpine-verification.log`、`functional-tests.log`。结构化报告位于 `images/alpine/verification.json`、`images/alpine-ram/ram-verification.json`、`images/functional-verification.json`。

三根产物大小：

| 产物 | 字节数 |
|---|---:|
| `alpine/rootfs.tar.gz` | 18538128 |
| `alpine-ram/alpine-ram.cpio.gz` | 18514077 |
| `maintenance/ram.cpio.gz` | 5366216 |

主机编译、结构检查和 QEMU 用户态执行已通过；未进行 RAM/kexec、冷启动或真实硬件验收。
