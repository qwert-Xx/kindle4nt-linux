<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Alpine 3.24.2 armv7 默认根配方

仅源码/配方。根 tar、私钥、AR6003 私有固件/校准、波形、Wi-Fi 凭据、SSH身份和设备备份不入 Git；构建时由用户从外部提供。官方锁定包、索引和工具见 project/alpine/packages.lock.json、PACKAGES.tsv；本地包来源见 wpa-static.lock.json。不得把构建用输入或输出提交。

## 静态 2.12 本地 APK

package_wpa.py 将外部已验证的静态 wpa_supplicant/wpa_cli 2.12（含扫描中止修复）封装为签名 2.12-r0，安装 /sbin；不装官方2.11或重复副本。源码/许可来源需随未来二进制分发履行。RSA256私钥仅外置，公钥已入库；当前锁对应现有公钥，自行生成新密钥须同步公开锁与来源记录，不绕过验签。

```sh
python3 project/alpine/package_wpa.py --bin-dir /absolute/static-wpa --copying /absolute/wpa-COPYING --key /absolute/private-key --apk /absolute/host-apk.static --out /absolute/new-k4-repository
```

根 repositories 使用 `@k4 /var/lib/apk/k4`，world 为 `wpa_supplicant@k4`，本地 APK 和 APKINDEX 均验签。test_k4_repository.py 用真实 apk 测试带标签保留K4、去标签负对照升级和坏包拒绝。不能将预签名包假称为自行源码重编结果。

## 离线构建与复现

所有命令以 kindle UID1000执行。download.py 取得锁定官方输入；已冻结索引会随上游更新，SHA不同不能当本次快照。build.py 不连设备，用 apk --no-network/--no-scripts 安装并审查生成服务。外部 BusyBox tar提供既有K4用户态和私有输入，内核/DTB/23模块必须与 kernel.lock.json 对齐。

```sh
python3 project/alpine/download.py --out /absolute/cache
python3 project/alpine/build.py --cache /absolute/cache --k4-repo /absolute/k4-repository --busybox-tar /absolute/busybox-root.tar.gz --busybox-sha 221468c1686b8cc6b671d22f500fcc97e039307a866ecbd1b19015bac6c04a74 --kernel /absolute/zImage --dtb /absolute/imx50-kindle-k4.dtb --modules /absolute/lib/modules --out /absolute/new-alpine-a
# 同输入另建 new-alpine-b，再验证
python3 project/alpine/verify.py --build /absolute/new-alpine-a --compare /absolute/new-alpine-b
```

部署版 tar SHA256 `d81de7ef896e51d384e2ca4589a5fea1f08778c5a366246b4afa757f37507e37`，19,471,521 bytes。包含用户外部私有输入，其他用户自己的输入会得到不同tar；仅公开配方，不分发该tar。正式 zImage `5c666c72ad08914c1883b76d03bd5e1bcf40046f1a5155ee58229b1575419291`，方案 A DTB `8960edb8bdec2d216080b0f6dee682f38fd69b45f663062d539afc4a93bc0cdc`。

## 时间与原厂做法

原厂启动 hwclock -u -s，正常 halt/reboot hwclock -u -w。Alpine OpenRC hwclock采用同一UTC SRTC rtc0，hctosys/systohc=YES、adjfile=NO；rtc1为PMIC，不自动按日期大小切换、不回写PMIC。
可选 k4-ntpd 用 BusyBox ntpd -n -p pool.ntp.org、依赖Wi-Fi/hwclock；DHCP/DNS/UDP123需可用，正常关机保存纠正后的时间。RTC为1970时 hwclock 本身不能创造正确日期。强制reboot、掉电/watchdog不保证关机回写。无固定构建时间兜底或TLS绕过。禁用/启用：rc-update del/add k4-ntpd default。原厂epoch下限策略未照搬。
既有Alpine验收确认NTP纠正、正常重启SRTC读写与官方HTTPS apk update；未执行upgrade或完整耗尽电池测试。

## 部署与回退（说明，不自动执行）

1. 准备主机核验的p1/完整用户区与boot备份、ROM人工恢复路径、足电和维护工具。v8 Ctrl-C→shell→YMODEM加载方案A RAM维护包；确认RAM运行、guard健康且时间足够、p1未挂载（含/dev/root或UUID），eMMC只读。不要在正在运行的Alpine根执行格式化。
2. 上传tar、修正后的 project/tools/deploy-emmc-root、静态mke2fs维护包到RAM tmpfs，逐项核验SHA。maintenance包内旧脚本有 ! grep 缺陷，必须使用本草案共享修正版。
3. 显式执行 `sh deploy-emmc-root /tmp/rootfs.tar.gz EXPECTED_SHA /tmp/maintenance`。脚本只格式化p1，解包/sync/卸载/只读重挂载逐文件核验，恢复主设备和分区只读；不写boot0/boot1/179。错误SHA和已挂载检测在解除只读或格式化前退出。
4. guard健康期限内主动reboot。v8从p1 /boot直接启动，无initrd。确认根rw、OpenRC、持续watchdog、模块/无线/显示/时间健康。
5. 回退BusyBox用相同RAM流程重写p1为核验过的自洽BusyBox tar。当前23模块对齐备选SHA `16733c41230b910e4f4b4ead7b8eb50024f2779df042fcce66dfc75752070264`；原K历史21模块包仍为自洽备选，不是当前设备完整备份。回退流程尚未实际演练。
6. 下键+复位→ROM→USB barebox→RAM用于人工救援；boot1可从完整v7备份恢复并核验全区/只读。179=0x48仅选择boot0，不恢复已替换p1；原厂系统还需原厂根备份。不得把启动选择当完整回退。

后续为长期稳定性、第二台K4和发布前用户许可审阅。不得从本配方复现推定新的设备验收。
