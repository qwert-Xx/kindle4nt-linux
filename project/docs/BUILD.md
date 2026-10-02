<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# 离线构建

需要 Linux 主机、Python 3（源码配方需支持 tarfile data filter）、make、ARM GCC 13.3、binutils 2.42、dtc、mke2fs/debugfs 与完整匹配的交叉 libc。不要为了模块加载替换运行 BusyBox。

公共导出采用主题 patch 系列。准备独立 Linux v6.6.157 源码，按 kernel/patches/series 顺序应用；debug 额外应用 kernel/debug-patches/series。使用所选系列提供的正式 K4 common 与顶层 DTS，不混用诊断/历史 DTS。当前仍是草稿，不是已发布发行版。

一条命令组装正式镜像：

```sh
make -C project images SOURCE=/absolute/linux INPUTS=/absolute/private/inputs.json OUT=/absolute/new-output
```

JSON 输入 schema 与逐文件 RAM 配方见 [构建入口](../README.md)。config 默认 production，外部输入逐项 SHA256 校验，输出必须位于源码外。固件/波形/凭据由外部配方显式引用，构建不扫描个人目录、不连接设备、不执行诊断或烧写。配方里的源码文件也必须锁定 SHA；通用 modalias coldplug 位于 guard/存储保护和旧 SPI coldplug 完成之后，使用现有 modprobe、不使用 blacklist/-b。

源码重建用户态是独立核验步骤，见 [配方](../userspace/README.md)；它不替换正式运行输入。barebox 单独维护，开发基线保持已验的上游23/8；不可把诊断 zqcal 镜像作为默认加载器或更换编译器后沿用旧硬件结论。

构建记录应保存输入 SHA、配置、release、元数据、模块列表、根目录清单与输出 SHA。检查正式无诊断入口，eMMC 保护与 guard 文件哈希不变。运行 project/test_build.py、test_rootfs.py、test_coldplug.py、test_export.py（现有工具，不装包）。构建通过不能代替冷验。
