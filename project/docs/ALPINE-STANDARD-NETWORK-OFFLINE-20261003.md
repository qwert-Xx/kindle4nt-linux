<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Alpine 标准网络离线配方（2026-10-03）

基线 refactor/k4-modularization@fc2aaf4fa；按设备证据提交7f106e6c3的最终配置组装。仅kindle UID1000、LF、主机构建；未访问设备、未部署新根、未修改BusyBox根配方或用户态，未修改内核/DTB/barebox v8/既有维护包。

## 网络职责与配置

启用官方wpa_supplicant/wpa_cli 2.11-r4与networking；新增bridge 1.5-r5、ifupdown-ng与ifupdown-ng-wifi 0.13.0-r0。77个官方包及SHA锁在packages.lock.json/PACKAGES.tsv，公开sources清单及第三方许可同步。保留busybox-ifupdown包，ifup/ifdown/ifquery链接选择ifupdown-ng。

wpa_supplicant由官方OpenRC监督，nl80211、wlan0、dbus=no，rc_need='k4-coldplug hwclock'。networking增加rc_need='k4-coldplug wpa_supplicant'与rc_after='wpa_supplicant'，保留内置localmount/hostname依赖。官方wpa_cli以WPACLI_OPTS='-i wlan0 -a /etc/wpa_supplicant/wpa_cli.sh'启用默认动作脚本，need networking；官方动作CONNECTED→USR1、DISCONNECTED→USR2通知ifupdown-ng的udhcpc PID文件。没有修改官方脚本，没有新增扫描重试、等待循环或看护。

interfaces：lo loopback、usb0静态169.254.212.2/16、wlan0 dhcp；不写wifi-ssid/psk，避免wifi executor重复起supplicant。标准udhcpc.conf写RESOLV_CONF="/run/resolv.conf"，保留resolv.conf符号链接。私有凭据仍从外部输入etc/wpa_supplicant.conf读取，写入根/etc/wpa_supplicant/wpa_supplicant.conf，权限600；不进Git。world逐字节匹配设备最终记录，ifupdown-ng是直接world项，bridge/wifi/OpenRC split包是依赖；本次离线组装仍按锁定版本和SHA安装。

仅Alpine根删除k4-wifi服务、k4-wifi-connect、udhcpc-wifi与helper的wifi分支；USB SSH分支保留，conf.d增加need networking。platform-start删旧usb0等待/ifconfig段，保留gadget/SPI/accessory/charging。NTP依赖改为networking wpa_cli hwclock。BusyBox RAM/eMMC根继续原K4服务，不含OpenRC，不变。

## 比对与验证边界

19份非私有配置/脚本/包选择文件逐字节匹配已保存的设备内容或已执行变更脚本，其中包括最终world；三个runlevel链接、ifupdown链接选择及五个删除路径也一致。具体逐文件SHA和证据类型见ALPINE-STANDARD-NETWORK-OFFLINE-RESULT-20261003.json。

差异：新etc/k4-rootfs.sha256重新生成；APK数据库/脚本归档由相同77包离线生成，未保留设备最终数据库的逐字节dump，不能宣称整个根与设备逐字节一致。私有凭据、SSH身份、运行时文件、设备私有备份不比较/不公开。本轮不读取设备，配置事实来自7f106e6c3及其已有本地日志；不是设备当前状态的新快照。

两套根tar逐字节一致。77包索引/签名、315 ARM ELF（203动态）、23模块、QEMU版本查询和ifquery读取lo/usb0/wlan0通过；16服务的内置depend及conf.d rc_need/rc_after组合图无环且顺序正确。主仓库/公开草案分别19 host + 3部署夹具通过。内核/DTB哈希匹配锁；旧维护包SHA清单通过、BusyBox源路径没有变更。

设备既有7f106e6c3验证：标准做法+官方2.11，五轮明确scan aborted、20挂起success20/fail0、ping20/20；10次DHCP释放/重新取租对应官方动作，supplicant/DHCP PID不变。最终正常reboot38.593秒恢复，配置去掉临时dhcp-opts -S。仅既有设备证据，新构建根未上机；自然租约T1/T2、长时、不同认证与USB不枚举情况未覆盖。

新根 SHA256：`41fb4d11ae361bff4f81449691f56875bae5e31d0067c826a39084b3ba41467c`，19148401 bytes。a/b相同。

既有产物不变：

|文件|SHA256|
|---|---|
|boot/zImage|5c666c72ad08914c1883b76d03bd5e1bcf40046f1a5155ee58229b1575419291|
|boot/imx50-kindle-k4.dtb|8960edb8bdec2d216080b0f6dee682f38fd69b45f663062d539afc4a93bc0cdc|
|existing_barebox_v8_candidate|b283f374a5fda6e7ba2c5c3b83ba9f67a569c1e63493d9ab4ea3b79febda0606|
|existing_maintenance_bundle|a757e8eec8b2486cf67979f7603099119fb38cb75db162e1950c846b6b2dbbb4|

Roots are private host outputs; only recipes and verification metadata are published.
