<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# DDR ZQ 参考

默认 barebox 使用上游 LPDDR1 配置 PU=23/PD=8，CTL75 为 0x817，CTL74 装载字段采用 +1 编码（24/9）。其它取值可靠性尚不确定，参见[已知问题](KNOWN-ISSUES.md)。

zqcal 是独立 barebox RAM 诊断命令，不属于默认 v9 镜像或 Linux 模块。它在 OCRAM 内、DDR 自刷新期间测量，保存原配置并恢复 DDR，暂停/恢复 USB DMA，输出测量和内存校验结果。硬件参数与初始化顺序说明保留在 `porting/` 的历史研究记录中。

当前系统的构建、安装与恢复使用[项目入口](../README.md)，不需要运行 zqcal。
