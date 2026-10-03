<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# 新用户待决项实施、主机与设备验证

在 fix/new-user-pending worktree，基线 e550b249d。只写本 worktree（含 ignored .k4-build/pending）与 Windows AGENTS.md 副本；以 kindle 用户构建/提交，LF，不 push、不访问设备。内核、驱动、barebox 代码及历史日期报告未修改。

## 改动与证据

| 项目 | 改动 | 验证输出 |
|---|---|---|
| tmpfs | 删除维护 /tmp size=32m、bootstrap /run size=16m、两份 Alpine fstab /tmp size=32m；Alpine mount-early 不重复挂 /tmp、/run | 三份 shell sh -n 通过；OpenRC init.sh/localmount 源码核对；IMAGES_OK |
| mmc-utils | 锁 commit d8a8358a7207bd81d0c38dca2cf27a48bf411341，clone/fetch 并验证 commit；删除归档 SHA 合同和 Git archive 示例 | 在线获取/静态 ARMhf 构建通过；离线构建通过；两次新工具包 cmp 相同 |
| 用户态源码 | sources.lock.json 包含下载 URL 和原 SHA；rebuild.py 共用 sources/fetch.py.checked，直接读缓存；删除 cache-map 和 sources.json 要求 | 空缓存下载 8/8 SHA 通过；全组件构建、离线缓存构建通过；缓存测试覆盖下载、离线缺失、篡改与错误下载 |
| fastboot 主机 | Linux 工具/udev、Google Windows fastboot.exe/WinUSB、WSL usbipd 与 gadget 重新枚举说明 | 官方主机文档与 v9 gadget 配置核对；未连接 USB 设备 |
| RAM 参数 | 删除三条 global -r，只设置维护 bootargs/boot_atag 等必要项 | v9 emmc/usbconsole 脚本、上游 startup.c 与 boot.c 核对：倒计时 Ctrl-C 后不调用 boot，不执行 emmc 设置 k4 bootargs |
| 波形 | 新 WAVEFORMS.md，默认 NVMEM WBF 内核解码、文件备份路径、无波形的功能边界 | 驱动/设备树/原厂 module parameter 核对；文档 Python 提取代码在既有私有 WBF 构造的 flash fixture 上通过；未实机验证 |
| AGENTS | 两份同步为项目约定，删除历史日志和过时接续 | 文件 byte-identical、LF；用户入口/构建命令/私有数据/恢复事实保留 |

Alpine /run 使用原版 OpenRC 标准策略：其 init.sh 原生 run_mount_opts 含 size=20%，本任务没有修改发行版脚本；删除的是 k4 自己的重复挂载。项目自有 tmpfs 挂载已无 size，/tmp 使用内核默认上限。这不是物理内存预留。仍需设备验证启动挂载与原单一 /tmp 部署流程。

Dropbear 原站返回 HTTP403，改为上游发布页列出的 dropbear.nl 镜像。Linaro 旧发布地址跳转为 HTML 联系页，SHA 校验正确拒绝，改为保存同归档的 Armbian 镜像；原锁定 SHA 不变。没有绕过 SHA 校验。

## 构建和检查

实际主机输出保存在 worktree 的 `.k4-build/pending/`（0700，含私有产物，不入库）：

```text
python3 -m unittest discover -s project -p 'test_*.py': 32 tests, OK
python3 project/userspace/test_compare.py: 5 tests, OK
python3 porting/test-waveform-inspect.py: 8 tests, OK
make -C project check: INPUTS_OK
make -C project images: IMAGES_OK alpine/rootfs.tar.gz alpine-ram/alpine-ram.cpio.gz maintenance/ram.cpio.gz
WBF extracted: 111001 bytes; default kernel generates WRF
COMPARISON_OK; WAVEFORM_EXTRACTION_FIXTURE_OK
```

默认 images 实际使用 source 模式、当前 worktree 内核源码和既有外部 inputs.json，不使用 prebuilt。输入私有内容只读复用上一轮；三根比较以 上一轮新用户流程的 images 输出 为基线。独立下载用户态构建用 `download-cache`，结果在 `download-userspace/report.json`。

## 产物比较

逐文件比较 tar/newc 的内容、权限、所有者、类型及链接，维护内嵌 ext3 用 debugfs rdump 比较文件内容、类型和权限。外层 cpio 的 init/rootfs.ext3 变化与维护 tmpfs 改动一致；内层只变化 `etc/init.d/rcS.k4-base`。Alpine 与 Alpine RAM 的功能变化只在 `etc/fstab` 和 `etc/k4/mount-early`，以及生成的 `etc/k4-rootfs.sha256`。

**两项构建位置/标识差异明确保留在 comparison.json，不宣称无条件逐字节一致：** Alpine 两根中 `lib/modules/6.6.157-k4-production/build` 链接的目标为新输出目录；独立重建 BusyBox 仅 GNU build-id 20字节不同，compare.py 确认 ELF 全部其它字节相同。默认三根使用原哈希锁定用户态输入，所以根内 BusyBox 不变。8个其它用户态文件和 busybox.links 均逐字节相同。没有改变运行时内核、DTB、模块二进制或其它根文件功能；严格的“除 tmpfs 外产物所有字节相同”仍不成立，原因是已有打包/构建的位置元数据，不应隐藏或引入本机固定路径来伪造一致。

内核 SHA256：50939951fcbb8a7855e1be0e63f61286f2714938394e1cc6ac083424a7709896；DTB SHA256：8960edb8bdec2d216080b0f6dee682f38fd69b45f663062d539afc4a93bc0cdc。两者与基线逐字节一致。

| 三根产物 | 字节数 | SHA256 |
|---|---:|---|
| `alpine/rootfs.tar.gz` | 18538062 | `7001a351b215eb0cd2814639005cade530a98960572e59d17b22f2dbd8c6092f` |
| `alpine-ram/alpine-ram.cpio.gz` | 18513993 | `f66a3a2de0a4024b6d09bf2927487934d414b08edd3b380552344c60713120f4` |
| `maintenance/ram.cpio.gz` | 5366224 | `4163b744bb45765a3cf78c92a1c92660a2e5b3dae00b7ce462cb89f23abf326e` |

mmc-utils 新工具包两次相同 SHA256：`1d35dadd8a4cdcee057a22acdbbe7bc8c764bd09adbf10d41195e25ac8d4a278`。源码来源以 SOURCE-COMMIT 校验，不以生成归档 SHA 作输入合同。

## 波形获取摘要与设备缺口

默认从只读 `/sys/bus/nvmem/devices/k4-panel-flash*/nvmem` 备份 NOR，按 0x886 和 WBF header 长度提取、验证 CRC；内核自动生成 WRF。原厂系统可查询 `/sys/module/*/parameters/waveform_to_use`，从当前面板缓存复制同名 WBF/WRF；自己的文件备份可直接复制后检查。完整命令见 [WAVEFORMS.md](WAVEFORMS.md)。本次只有源码/fixture 验证，未执行 SSH/flash 读取或刷新。没有波形时可启动/维护/联网，显示不可用；不加固定样本 SHA。

设备待验证：两种 Alpine 的标准挂载时序、维护 /tmp 同时存放根和维护工具并按原流程部署；简化 barebox 参数后的 fastboot 启动；Linux/Windows 主机 USB 权限、驱动、WSL gadget 转接；面板 NOR 导出、波形面板匹配及刷新/跨温区画质。主机验证不代替这些设备验收。

功能提交：1411ef298（tmpfs）、349cd7f7f/c5dfaa4b2（mmc commit/包元数据）、620427144（自动源码缓存）、827e84f29（fastboot/RAM参数）、949ff6a2a/8a4f07bf9/34d0332de（波形）、587eb3a2e（AGENTS）。后续报告与文字校对见本文件的 Git 历史。

## 本轮发布的设备验证补充

以上主机阶段的“设备待验证”是当时范围。本轮发布已按简化barebox参数启动维护FIT并经SSH2222连接，确认维护/tmp与/run均118.9M；根归档和维护工具均放/tmp，解包后仍可用86.0M，原指南单一/tmp部署流程通过。新Alpine仅部署到/dev/mmcblk2p1并只读文件读回通过；根rw、官方watchdog、Wi-Fi/DHCP/ping、USB与Wi-Fi SSH22通过。eMMC Alpine实际df显示/tmp与/run同为118.9M，挂载无size参数；以本轮运行结果为准，不把早先对OpenRC脚本20%选项的静态描述当作运行时容量。一次停喂51.531秒内自动经v9返回新Alpine，默认tmpfs与上述服务再次通过。详细输出及验证边界见[发布实机记录](../../porting/RELEASE-DEPLOY-PUBLIC-20261003.md)。

Alpine RAM挂载时序仍仅主机构建；本轮沿用既有Windows USB/IP与驱动，未新增独立Linux普通用户USB权限验收。面板NOR导出/匹配/刷新、物理拔USB电池启动、电源轨及长期稳定性没有本轮实机证据。
