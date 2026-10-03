<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# 已知问题

## barebox 的 DFU 与 fastboot 组合

`usbgadget -a -D -A` 同时启用 DFU 和 fastboot 时，主机会报告重复 interface 0，USB 配置失败，ACM 控制台也消失。长按电源键复位可恢复正常启动。当前一次只启用一种功能，例如 `usbgadget -a -A` 或 `usbgadget -a -D`。

源码原因位于上游 barebox 2026.09.0 的 `drivers/usb/gadget/function/dfu.c`：`dfu_bind()` 调用 `usb_interface_id(c, f)` 分配接口号，但随后用 xzalloc 建立各 alternate descriptor 时没有设置 `desc[i].bInterfaceNumber`，其值保持 0。组合功能会与其它接口冲突。当前板级配方没有修改这段上游代码。

## fastboot 的主机退出状态

`fastboot boot maintenance.itb` 成功交给 Linux 后，主机仍可能显示 `Status read failed (No such device)`。barebox 的最终 fastboot 状态在 bootm 返回之后发送，而正常 Linux 启动不会返回。可通过设备 USB 枚举、控制台或维护 SSH 判断启动结果，见[RAM 启动](RAM-BOOT.md)。

## 硬件和支持范围

- 支持 Kindle 4 Non-Touch D01100。其它 Kindle、其它面板、WPA2-PSK/CCMP 以外的无线认证尚未验证。
- 完全耗尽电池后的 USB 冷启动与低电反复重启行为仍需验证；已有充电实现不等于低电自救已验证。
- DDR ZQ 使用上游 23/8；其它取值的可靠性尚不确定。[ZQ 参考](ZQCAL.md)说明相关背景。
- 某些 legacy compatible 仍缺上游 YAML schema 覆盖。K4 可匹配 schema 的校验与这些覆盖缺口是不同问题。
- 显示 provider 的模块卸载、跨版本内核 ABI、6.6→6.6 kexec、长期功耗和电气裕量仍有验证缺口。默认显示链内建。
- barebox 首次写入锁定 watchdog WDBG=0，与原厂引导配置不同，Linux 驱动会告警但仍注册。

## 软件行为

Watchdog 持续喂狗，喂狗停止后触发硬件复位。重启进入当前选择的启动分区。硬件失效时可使用[ROM 下载与维护恢复](RAM-BOOT.md)。

## 维护 SSH 的输入与传输

维护内嵌 ext3 根以只读方式挂载，缺失 Dropbear 主机密钥时无法在其中生成密钥；构建前预置 `etc/dropbear/k4-hostkey`。维护默认用户态没有 SCP/SFTP 服务程序，传输文件使用 SSH 的 `cat` 与标准输入/输出，见[部署指南](EMMC-ROOT.md)。Alpine 使用官方 OpenSSH/SFTP。
