<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Kindle 4 Non-Touch Linux

从 [项目入口](project/README.md)开始：先备份整机 eMMC，再构建、准备 RAM 维护并安装 boot1 与 Alpine。

公开树提供源码补丁与配方，不分发固件、校准、波形、凭据或设备备份。上游版本与 SHA256 见 sources/manifest.json 及 project 的锁文件；不使用子模块。

先取得 Linux v6.6.157，在独立源码目录按 kernel/patches/series 顺序应用补丁；debug 另按 kernel/debug-patches/series 应用。按构建指南执行 `make -C project images SOURCE=/path/to/linux INPUTS="$PRIVATE/inputs.json" OUT="$OUT/images"`。
