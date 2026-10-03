<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# 主线发布、最终部署与公开草稿（2026-10-03）

基线 b4821f0e83e50f13ec8cacc5b1b509c569f860e3。读取 AGENTS.md 与 project/README.md；构建和提交使用 kindle（UID1000）、codex <codex@localhost>。
仅授权部署 /dev/mmcblk2p1；boot0/boot1/idme/fuse/EXT_CSD 不写，不 push。boot1 保持源码 v9（fbcd7c01…fe0e40）。

## 发布锁与主机验证

默认源码入口 make -C project images 成功，外部输入复用当日新用户流程的私有输入；输出为新的仓库外发布目录，不覆盖冻结包。
独立空输出目录 make -C project images MODE=reproduce 返回0：

```text
VERIFY_RELEASE_OK 6.6.157-k4-production modules=23
IMAGES_OK alpine/rootfs.tar.gz alpine-ram/alpine-ram.cpio.gz maintenance/ram.cpio.gz
```

发布锁 kernel.lock.json 整文件 SHA256：`0d783d868e50766ee534ddfb2f4c4dc202392d8bbd966f9b7e91b26b99ae9b90` → `cd5d676bcaebf2fb394d9f6041d58e953cea0ed4d0779a99a2b4afe7ecd32afd`。
zImage：`5c666c72ad08914c1883b76d03bd5e1bcf40046f1a5155ee58229b1575419291` → `50939951fcbb8a7855e1be0e63f61286f2714938394e1cc6ac083424a7709896`。
DTB：`8960edb8bdec2d216080b0f6dee682f38fd69b45f663062d539afc4a93bc0cdc`（未变）；23个模块 SHA 全部更新并通过独立源码重建核对。
工具链保持 ARMhf GCC13.3/binutils2.42。主机 unittest32项与用户态compare5项通过。
维护 RAM cpio 两次逐字节相同；Alpine根/Alpine RAM仍含模块build链接的构建目录元数据，故不同输出目录的整根SHA不作为reproduce合同；内核、DTB及模块逐字节验证通过。

| 产物 | 字节 | SHA256 |
|---|---:|---|
| `images/alpine/rootfs.tar.gz` | 18538157 | `30f9cb1b7abf93a37a3caddd208f137091436126f6ca497c10cbab98a94a3ff2` |
| `images/alpine-ram/alpine-ram.cpio.gz` | 18514083 | `84b99c36ae0eb4bdfd183f683d968201a44b8ea68d668a1b5ba58fdffc07f193` |
| `images/maintenance/ram.cpio.gz` | 5366224 | `4163b744bb45765a3cf78c92a1c92660a2e5b3dae00b7ce462cb89f23abf326e` |
| `fit/maintenance.itb` | 12697633 | `64902b4d257674f96052e9f185af327baa03c8ac163c82cd47796bdb60242684` |

维护FIT按RAM-BOOT.md生成，SOURCE_DATE_EPOCH=1790956800。主机构建不代替硬件验收。

## 最终产物实机部署与恢复

按 project/README.md → RAM-BOOT.md → EMMC-ROOT.md 操作。reboot 后 Ctrl-C 截住 v9倒计时；未执行emmc条目，直接设置指南maintenance命名空间、boot_atag=false并切换fastboot。没有清空命名空间或增加包装。
本次维护FIT下载成功；主机fastboot返回Status read failed/No such device，Linux实际启动且SSH2222公钥登录成功，与已知问题一致。
运行时枚举 mmcblk2、mmcblk2p1（1880064 KiB）、两boot分区；p1未挂载。完整p1部署前备份1925185536字节，主机SHA与设备整分区SHA一致；私有备份保留在仓库外、不公开。
仅执行deploy-emmc-root目标/dev/mmcblk2p1；格式化ext4、解包、sync、只读重挂载后741个普通文件SHA均通过，脚本返回0并打印Partition deployment and file readback verified。没有写boot0/boot1/idme/fuse/EXT_CSD。

维护系统 df -h /tmp /run：

```text
Filesystem                Size      Used Available Use% Mounted on
tmpfs                   118.9M     12.0K    118.9M   0% /tmp
tmpfs                   118.9M     36.0K    118.9M   0% /run
```

归档、部署脚本、e2fsprogs工具包均按指南上传/tmp，解包后/tmp使用32.9M、可用86.0M；没有临时换到/run。维护根持续BusyBox watchdog 30s/10s。
新Alpine正常启动后约32.438秒主机检测到SSH22、Wi-Fi COMPLETED和DHCP默认路由。根ext4 rw，实际创建/读取/删除临时根文件通过；sshd与官方OpenRC watchdog started，硬件watchdog active/timeout30/nowayout1。USB和Wi-Fi SSH22公钥登录通过，网关ping2/2。

恢复后的 Alpine df -h /tmp /run：

```text
Filesystem                Size      Used Available Use% Mounted on
tmpfs                   118.9M         0    118.9M   0% /tmp
tmpfs                   118.9M    304.0K    118.6M   0% /run
```

tmpfs挂载无size参数；118.9M为该内核默认上限，不是物理内存预留。部署前旧Alpine/tmp为32.0M。

仅一次SIGSTOP停喂官方watchdog PID298，不发reboot。51.531秒内观察到新boot ID、Wi-Fi关联/DHCP及SSH22恢复；barebox串口记录倒计时、Booting entry 'emmc'和读取/boot/zImage，属于硬件watchdog复位后经boot1完整启动路径，非kexec。
恢复后官方watchdog PID299正常，根rw、默认tmpfs、Wi-Fi、USB与Wi-Fi SSH22和ping2/2再次通过；ext4报告recovery complete，无EXT4错误。
设备/boot内核与DTB SHA匹配发布锁；boot0与boot1整分区SHA前后完全相同。boot1保持源码v9 SHAfbcd7c01…fe0e40对应部署状态。
这里没有拔USB独立电池冷启动、电源轨测量、长期可靠性或新的显示刷新验收；不能用本次启动/复位通过替代这些范围。

构建、SSH、串口和备份原始证据均保留仓库外的本轮发布输出/日志目录；公开记录仅保留必要验证摘要与df输出，不含MAC、boot ID、序列号、凭据或私有二进制。

## 公开源码与配方主机验收

project/export.py输出当前project/rootfs/diagnostics/sources及porting/barebox-emmc源码配方；旧barebox/overlay与实验boot1目录不再导出。README链接到当前project/README.md；公开构建指南明确获取带固定版本、SHA256与签名的上游Linux，再应用production series并传SOURCE。无子模块。
干净上游v6.6.157应用公开生产补丁后reproduce通过，zImage/DTB/23模块与发布锁一致，维护cpio与主线相同。公开barebox v9配方重建SHAfbcd7c01a1b4c213a50b4389f35f9c6c0143e976940d5295fd4bc3ee24fe0e40，匹配当前源码构建v9；不部署boot1。默认环境通过REUSE.toml annotations声明许可，没有.license文件进入defaultenv，build.py没有特殊排除逻辑。
公开文档CC-BY-4.0，原作者版权由源头header及REUSE元数据保留；新增导出版权说明待所有者推送前审查。发布推送由用户审查后执行，本轮不push。
