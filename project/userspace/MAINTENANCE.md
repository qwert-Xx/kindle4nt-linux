<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# RAM 维护系统与工具

维护系统是 BusyBox RAM 根，默认由 `make -C project images` 生成 `maintenance/ram.cpio.gz`。USB ACM 提供 shell，Dropbear 监听 `169.254.212.2:2222`，root 采用公钥认证。启动方式见[RAM 启动与恢复](../docs/RAM-BOOT.md)。

维护根使用 BusyBox init/inittab，rcS 持续运行 `busybox watchdog -T 30 -t 10 /dev/watchdog`。内嵌 ext3 根的引导检查以只读方式挂载。部署工具对显式目标分区进行格式化和读回验证。

## 普通命令与 PATH

打包时读取同一 BusyBox 构建生成的 `busybox.links`，在 `/bin`、`/sbin`、`/usr/bin`、`/usr/sbin` 建立指向 `/bin/busybox` 的符号链接（以及清单中的 `/linuxrc`）。已有独立程序及链接保留，例如独立 modutils；不使用 alias 或包装脚本。PATH 为 `/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin`，SSH 非交互命令 `cat`、`uname` 等可按普通命令查找。

## 存储维护工具

mmc-utils 按锁文件中的上游 Git 提交获取源码并校验 commit ID，不要求用户生成归档：

```sh
python3 project/userspace/maintenance.py --cache "$PRIVATE/source-cache" --out "$OUT/mmc-tools"
python3 project/userspace/e2fsprogs.py --help
```

锁定提交为 `d8a8358a7207bd81d0c38dca2cf27a48bf411341`（v1.0）。首次使用 clone，缓存缺少提交时 fetch；`--offline` 只使用已有 Git 缓存。输出包括静态 ARMhf mmc-utils 与只读 `extcsd-read`。

`maintenance.py` 校验 `maintenance-sources.lock.json`，输出静态 ARMhf 工具和带源码、SOURCE-COMMIT 和许可的 `maintenance.tar.gz`。`extcsd-read DEVICE` 读取 512 字节 EXT_CSD；mmc-utils 支持查询与更改启动分区。mke2fs 构建参数见[构建指南](../docs/BUILD.md)。工具包内旧 `*-draft.sh` 针对固定设备号与旧流程，当前操作命令集中在[boot1](../docs/BAREBOX-BOOT1.md)和[Alpine 部署](../docs/EMMC-ROOT.md)。
