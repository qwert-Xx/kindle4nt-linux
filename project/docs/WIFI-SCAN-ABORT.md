<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# 扫描中止结论：采用官方 wpa_supplicant 2.11

2026-10-03 用户决定直接采用 2.11 并彻底移除扫描中止补丁及其专用测试，不设观察期。
2.12 的 wpa_supplicant/events.c:2649–2653 丢弃 aborted 扫描结果；上游 2.11 的 events.c:2526–2550 没有该分支。
本机此前 2.12 在连续 devices/devices/s2idle 后停在 SCANNING，收到 SCAN_ABORTED、丢弃缓存结果后未继续自动扫描。

移植仓库提交 dc6989aa2 的真机实验记录：官方 Alpine 2.11-r4 在五轮有明确中止证据的组合场景全部自主恢复；共44次挂起、0失败，supplicant/DHCP PID不变，无新增扫描钩子或看护。此为既有真机证据，本次仅离线构建，未重新操作设备。

Alpine 使用官方 main 2.11-r4（含 OpenRC split 子包，K4服务仍调用 /sbin/wpa_supplicant，不启发行版 Wi-Fi 服务）。BusyBox RAM维护根和eMMC根从未修改的上游2.11源码静态构建，supplicant和CLI版本一致。两份扫描重试补丁及其专用测试已删除；构建不应用扫描补丁，也没有新增重试代码。

硬件参数、内核、DTB、barebox v8不变。本机证据限定AR6003、当前固件/内核、WPA2-PSK/CCMP与所记录序列；新离线根包未部署，长期压力与其他认证模式未验证。
