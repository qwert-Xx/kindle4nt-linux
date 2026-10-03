<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# 主线 F1/F2/F3 实机验收（2026-10-03）

验收源码为 `refactor/k4-modularization` 的 `f8c933705`，工作树
`$BACKUP/k4-modularization`。先读取 AGENTS.md、project/README.md、
DISPLAY-LIFECYCLE-20261003.md、CLOCK-DEPENDENCIES-20261003.md 和
project/docs/DRIVER-LIMITS-VALIDATION.md。构建、记录提交均使用 kindle UID1000。
生效 DTB 为 `nxp/imx/imx50-kindle-k4.dtb`；本轮没有运行 debug DTB。
验收比较功能，不以旧产物哈希相等为门槛；部署传输校验与文件读回仍执行。

## 结果与范围

| 项目 | 实际结果 |
| --- | --- |
| 默认入口与部署 | 源码 images 成功，正式 release；维护 FIT 启动；p1 格式化、解包、741 个普通文件读回通过 |
| 基础健康 | 根 ext4 rw、实际读写、OpenRC watchdog、USB/Wi-Fi SSH22、Wi-Fi COMPLETED、网关 ping2/2 |
| F1 sysfs | fbdev、EPDC、PxP、Papyrus 各完整3轮；panel flash 独立3轮；每轮恢复后刷屏成功 |
| F1 模块 | 五驱动全=m RAM FIT，3轮卸载/加载，hwmon/nvmem/fbdev恢复、刷屏成功；Papyrus卸载需先unbind其内部供电关系 |
| F1 FD/mmap/在途 | 默认内核与模块内核旧FD/mmap通过；模块内核与恢复后默认内核持续写入中unbind通过 |
| F2 APBH | 单计数文件：空闲0/prepare1，显示活动enable1，blank/idle后0；ANATOP空闲suspended |
| F2 analog | 当前继承bandgap-on/APLL-off入口，两个直接bandgap引用与APLL，3轮480MHz/LOCK成功，最后恢复入口位值；并发寄存器读取与显示通过 |
| F2 PM | 默认Alpine s2idle3轮、STOP3轮；模块RAM各1轮；PMIC RTC唤醒与唤醒后刷新成功 |
| F3 波形 | 面板NVMEM WBF 111001→1175215字节；8/16/32bpp、4方向、GC16/DU/A2及全屏/局部、白/黑/灰阶/文字刷新成功 |
| F3 USB充电 | 电脑USB高速configured，500000µA额度→DAC5/480mA，PMIC raw读回0x81022b/code5；自然full保护→DAC0 |
| 停喂恢复 | 仅一次SIGSTOP官方watchdog；boot1 emmc完整重启，新boot ID、网络/SSH/watchdog恢复；USB确认窗口90.250秒 |

仅写 `/dev/mmcblk2p1`；未写 boot0、boot1、idme、fuse 或 EXT_CSD，未push。
boot1保持既有源码构建v9。本轮没有需要修改驱动源码的已确认缺陷。
硬件watchdog复位后完整启动不是kexec；没有拔USB/断电验证独立电池冷启动。

## 本地证据

- 构建/模块构建/工具：`$BACKUP/k4-driver-acceptance-20261003/`。
- Windows脚本、完整p1回退备份、串口、照片：
  `$BACKUP\driver-acceptance-20261003\`。
- SSH原始stdout/stderr：
  `$BACKUP\modularization-cold-20261002\driver-acceptance-20261003\`。

原始证据可能含设备身份、网络配置或私有产物，全部留仓库外。
公开记录不复制boot ID、MAC、凭据或备份二进制。

SSH执行方式（下列脚本及各tag原始结果保留在上述证据目录）：

```powershell
python modularization-cold-20261002\ssh-run.py TAG --input driver-acceptance-20261003\SCRIPT.sh --session driver-acceptance-20261003 --seconds SECONDS
# 维护根额外 --profile ram；Wi-Fi连接用本机实际地址 --host ADDRESS。
```

实际tag包括 baseline、baseline-extra、baseline-refresh、ram-preflight、
backup-hash-final、deploy-p1、new-health、root-wifi-health、wifi-ssh、
lifecycle、lifecycle-corrected、flash-cycles、clock-display、display-modes、
analog、charge、pm-wifi、usb-after-pm、modules-ram-preflight、module-cycles、
module-cycles-unbind、modules-inflight-map-corrected、modules-pm-result、
returned-health、watchdog-wifi-health、final-health-refresh、final-wifi-ssh。

## 构建、维护与部署命令

```sh
PRIVATE=$BACKUP/k4-new-user-inputs-20261003
OUT=$BACKUP/k4-driver-acceptance-20261003
make -C project check INPUTS="$PRIVATE/inputs.json" OUT="$OUT/images"
make -C project images INPUTS="$PRIVATE/inputs.json" OUT="$OUT/images"
python3 -m unittest discover -s project -p 'test_*.py'
```

`check`成功，`IMAGES_OK alpine/rootfs.tar.gz alpine-ram/alpine-ram.cpio.gz maintenance/ram.cpio.gz`。
release=`6.6.157-k4-production`，默认23模块。源码与模块构建日志未检出compiler
warning/error。产物属主kindle:kindle。当前主线项目unittest为30项，全部通过。
历史记录的`project/userspace/test_compare.py`当前不存在，不能报告该5项复跑通过。

按RAM-BOOT.md将默认维护zImage、DTB、ram.cpio.gz复制为FIT模板文件：

```sh
mkdir -p "$OUT/fit"
cp "$OUT/images/maintenance/arch/arm/boot/zImage" "$OUT/fit/k4-kernel.zImage"
cp "$OUT/images/maintenance/arch/arm/boot/dts/nxp/imx/imx50-kindle-k4.dtb" "$OUT/fit/k4-board.dtb"
cp "$OUT/images/maintenance/ram.cpio.gz" "$OUT/fit/k4-full-ram.cpio.gz"
cp porting/barebox-emmc/maintenance.its "$OUT/fit/maintenance.its"
(cd "$OUT/fit" && mkimage -f maintenance.its maintenance.itb)
```

reboot→Ctrl-C→barebox执行：

```sh
global linux.bootargs.maintenance="console=ttymxc0,115200 rdinit=/init root=/dev/ram0 watchdog.open_timeout=120 imx2_wdt.nowayout=1 ath6kl_sdio.force_virtual_scatter=0 fbcon=map:1 logo.nologo"
global.bootm.boot_atag=false
usbserial -d; usbgadget -a -A
```

初次把最后两命令分开发送，串口在usbserial -d后消失，未进入fastboot，未写存储。
用户长按电源松开复位；改为同一行后成功，后续再次进入也成功。
Windows fastboot接口缺WinUSB；沿用主机既有WSL工具，不改Windows驱动：

```powershell
usbipd attach --wsl <发行版> --busid 1-7
```

主机实际fastboot调用：

```sh
T=$BACKUP/v9-device-tools-20261003/root
LD_LIBRARY_PATH="$T/usr/lib/x86_64-linux-gnu:$T/usr/lib/x86_64-linux-gnu/android" \
  "$T/usr/bin/fastboot" boot $BACKUP/k4-driver-acceptance-20261003/fit/maintenance.itb
# 模块RAM的第二次调用将FIT换为modules-fit/maintenance.itb。
```

USB主机工具以root运行；下载约12701696字节，随后Booting kernel/barebox shutting down。
fastboot返回Status read failed (No such device)，但SSH2222与RAM根实测启动，符合已知问题。
维护根`/dev/loop0 / ext3 ro`，eMMC无挂载，BusyBox watchdog `-T30 -t10` active。
实际p1为1880064KiB。部署前：

```sh
dd if=/dev/mmcblk2p1 bs=1048576 # SSH标准输出存入主机previous-p1.img
sha256sum /dev/mmcblk2p1
```

完整备份1925185536字节，主机与设备SHA均
`6d46e7f717f0502b5cb0d683aa4cc5c3bcad2d989c1b298f0697fafa9202b29e`。
传输566.75秒。设备hash超过原180秒SSH窗口，改后台输出到/tmp/previous-p1.sha，
结束旧计算后最终核对通过。此SHA只记录本轮私有备份，不构成支持前提。

按指南SSH标准输入上传新根、deploy-emmc-root、e2fsprogs维护工具到/tmp，执行：

```sh
mkdir -p /tmp/e2fsprogs
tar -xzpf /tmp/e2fsprogs.tar.gz -C /tmp/e2fsprogs
sh /tmp/deploy-emmc-root /tmp/rootfs.tar.gz \
  376e5ff35af601de2dc9899b3fe3c608243d7ebf7acfe83fc4784fae2424719f \
  /tmp/e2fsprogs/maintenance /dev/mmcblk2p1
reboot
```

返回0，741个普通文件OK，打印`Partition deployment and file readback verified`。
新Alpine根rw，实际创建/读取/删除/root/k4-acceptance-check通过；sshd/watchdog
status started、watchdog active/30秒、Wi-Fi COMPLETED、USB与Wi-Fi公钥SSH22通过。

## F1 命令、顺序与结果

运行时枚举所得ID：PxP=`4100c000.pxp`，EPDC=`41010000.display-controller`，
fbdev=`framebuffer`，Papyrus=`1-0048`，flash=`spi1.0`。五目录均有bind/unbind。
逐个向对应`/sys/bus/{platform,i2c,spi}/drivers/DRIVER/unbind`写ID，
恢复顺序flash→Papyrus/PxP→EPDC→fbdev；仅对未绑定设备写bind。
每轮运行`/tmp/fb-probe pattern-write`，读取fb0/device/state和PxP/diagnostic。

首次lifecycle脚本的restore函数覆盖外层d/id，supplier后两轮变为fbdev，
该首轮不作为五驱动各3轮证据。修正为subshell后，完整覆盖fbdev/EPDC/PxP/Papyrus
各3轮；flash首次快速恢复时前端未稳定恢复，脚本退出，保存f1-flash-failure证据。
独立flash-cycles每轮unbind后保存绑定目录，等待1秒，再逐provider bind并等1秒，
最后bind fbdev；3轮成功。立即与1秒后均见flash/fbdev解绑；恢复后WBF重解码。
快速连续bind的自动重探测时序没有完全归因，不将该首次脚本退出写成驱动崩溃。

旧FD/mmap工具：打开fb0并mmap完整shadow，frontend unbind后读写旧映射头尾，
旧FD pread/pwrite返回`-1 errno=19`，重新bind后新fb可刷新，再munmap/close旧引用。
默认及模块内核均打印`OLD_FD_MMAP_PASS`。
在途工具使用pthread持续pwrite，每1ms一次，主线程250ms后unbind：
写线程在注销过渡状态得到EPERM，unbind返回后pread得到ENODEV；bind后刷新成功。
初工具仅接受ENODEV误判，按fb_chrdev.c先检查FBINFO_STATE、后检查registered_fb
的真实语义修正后，模块及默认内核均`INFLIGHT_UNBIND_PASS`；未改内核语义。

模块验收构建：复制已完成默认输出到独立modules-kernel，项目入口应用五项=m片段：

```sh
python3 project/build.py --inputs "$PRIVATE/inputs.json" --preset production \
  --config "$OUT/all-modules.config" --out "$OUT/modules-kernel"
# IMX50_PXP_KERNEL, IMX50_EPDC, FB_IMX50_EPDC,
# REGULATOR_K4_PAPYRUS, NVMEM_K4_PANEL_FLASH均=m；release保持正式名称。
```

模块FIT仅从fastboot启动RAM，未替换p1内核。实际3轮命令：

```sh
M=/lib/modules/$(uname -r)/kernel
rmmod imx50_epdc_fb
rmmod imx50_k4_epdc
rmmod imx50_pxp
printf 1-0048 > /sys/bus/i2c/drivers/k4-papyrus/unbind
rmmod k4_papyrus
rmmod k4_panel_flash
insmod "$M/drivers/nvmem/k4-panel-flash.ko"
insmod "$M/drivers/regulator/k4-papyrus.ko"
insmod "$M/drivers/soc/imx/imx50-pxp.ko"
insmod "$M/drivers/video/fbdev/imx50-k4-epdc.ko"
insmod "$M/drivers/video/fbdev/imx50-epdc-fb.ko"
/tmp/fb-probe pattern-write
```

文档原始直接rmmod Papyrus返回Resource temporarily unavailable，模块refcnt=1、
holders为空。源码Papyrus VCOM的supply_name=display、两个desc owner=THIS_MODULE；
regulator/core.c set_supply持有supplier模块引用。解绑Papyrus注销regulator，释放
内部VCOM→DISPLAY引用后正常卸载。这是标准引用关系，无强制rmmod或owner绕过。
3轮均`updates=2 last_error=0 power_error=0`，PxP `result=0 fault=0 clocks_retained=0`，
fbdev/hwmon/nvmem恢复。MemAvailable依次163440/163408/163400KiB，未见逐轮大幅增长
或DMA quarantine；短期计数不能证明任意长时间绝无泄漏。模块内核tainted=0。
production稳态MemAvailable约209044→209112KiB，首次波形加载分配不作为泄漏。

## F2 单时钟、analog 与 PM

实际clock-display.sh共3轮：

```sh
mount -t debugfs debugfs /sys/kernel/debug
A=$(find /sys/kernel/debug/clk -type d -name apbh_dma)
P=/sys/bus/platform/devices/41018000.clock-controller
cat /sys/kernel/debug/clk/clk_summary > /tmp/clk-summary.txt
cat "$P/registers"
cat "$A/clk_enable_count" "$A/clk_prepare_count" "$P/power/runtime_status"
# 后台运行fb-probe pattern-write，逐100ms读取上面单计数与runtime状态。
/tmp/fb-probe blank
/tmp/fb-probe unblank
/tmp/fb-probe patch-write
```

| 采样状态 | APBH enable/prepare | ANATOP runtime |
| --- | --- | --- |
| 初始空闲、summary/register读后 | 0/1 | suspended |
| 显示刷新中多次样本 | 1/2 | suspended（显示持桥，analog无用户） |
| blank、恢复刷新后3秒空闲 | 0/1 | suspended |
| analog与显示并发 | 1或2 | analog持引用时active |
| 所有测试停止后的单计数 | 0/1 | suspended |

summary自身会唤醒provider，summary中的APBH1不作为泄漏证据。
PLL1_SW800MHz、EPDC/PxP AXI200MHz、pixel32MHz；没有重设共享PLL或改为PFD5。

临时ccf-probe.ko通过of_clk_get_from_provider取index0 APLL和两次index2 bandgap，
每轮prepare两个bandgap→prepare APLL→release APLL→release两个bandgap，重复3轮。
不强制写模拟电源寄存器、不调整CPU/PLL/PFD频率。与显示模式循环和register读取并发。

```sh
insmod /tmp/ccf-probe.ko
rmmod ccf_probe
```

入口`misc=00010000 pllctrl=00ff0000`；APLL运行
`misc=00110001 pllctrl=80ff04b0`（LOCK），打印`APLL=480000000 shared_votes=2`；
APLL释放但两个bandgap引用尚在时`misc=00110000 pllctrl=00ff0000`；最后恢复入口。
3轮rc0，未见hung task/clock/PM WARN。临时外部模块带预期taint4096（O），
未发生WARN taint；卸载后重启，最终默认内核tainted=0。
本轮覆盖继承reference-on/APLL-off，未强制构造reference-off或测试PFD5调频。

PM使用主线porting/dual-rtc-probe.c静态编译的/tmp/dual-rtc，后台执行：

```sh
for mode in --s2idle --mem; do
  for n in 1 2 3; do
    /tmp/fb-probe pattern-write
    /tmp/dual-rtc "$mode"
    /tmp/fb-probe patch-write
    sleep 4
    cat /sys/power/suspend_stats/success /sys/power/suspend_stats/fail
  done
done
```

`mem_sleep=s2idle shallow [deep]`，freeze=s2idle、mem=STOP。
每轮PMIC15秒闹钟、SRTC45秒后备，IRQ312、PMIC_EVENT raw1a0、
SRTC_FALLBACK_NOT_FIRED、offset_change0或1；RTC均清理enabled0。
production最终success6/fail0，每轮刷新无错、APBH0、ANATOP suspended、UDC configured。
模块RAM在模块循环后另外各1轮，success2/fail0，MODULE_PM_PASS、tainted0。
USB网络在挂起/重新枚举时短暂不可达，循环完成后USB及Wi-Fi SSH恢复。

没有外部输入电流仪器/成对同条件基线，因此没有物理功耗差值结论；
不得由APBH gate闭合直接推出整机省电数值。disabled APBH-DMA/GPMI节点未测试。

## F3 波形与充电读回

`WBF decoded: 111001 bytes to 1175215 bytes, source NVMEM`。
没有波形CRC/格式/分配/DMA错误。温度约28–29℃，未注入传感器或改电气参数。
通过主线fb-probe.c静态工具执行：

```sh
for bpp in 8 16 32; do
  for angle in 0 90 180 270; do /tmp/fb-probe mode-pattern "$bpp" "$angle"; done
done
/tmp/fb-probe mode 32 0
for mode in du a2 gc16; do
  echo "$mode" > /sys/class/graphics/fb0/device/waveform_mode
  /tmp/fb-probe pattern-mmap
  /tmp/fb-probe patch-write
done
```

所有请求返回成功、last_error/power_error0，PxP完成76次时fault0。
初次powerup/needs_full路径由驱动执行INIT，未通过不存在的fbdev INIT模式注入命令。
额外标准fb写入全白、全黑、灰阶/棋盘和`K4 F1 F2 F3 OK`文字fixture，随后写refresh=1。
照片确认可见内容、无大片缺块/花屏，全白全黑没有先前棋盘残留；照片质量不证明
每个灰阶电平或每种旋转的精确光度。两处固定表面斑点在白/黑图位置一致，
疑似表面污点/反光，不据此认定驱动故障。

充电实际命令（charge.sh结束恢复原上限及control；进入前已是480000和1）：

```sh
C=/sys/class/power_supply/k4-charger
cat "$C/device/state" "$C/uevent"
cat /sys/class/udc/ci_hdrc.0/state /sys/class/udc/ci_hdrc.0/current_speed
echo 480000 > "$C/constant_charge_current_max"
echo 1 > "$C/device/control"
sleep 3
cat "$C/device/state" "$C/uevent"
```

旧基线电脑USB configured/high-speed、500mA，旧策略budget/target/code4，400mA。
新内核关键读回：

```text
control=1 reason=eligible error=0 write_error=0 fault=0 full=0
usb_ua=500000 input_mv=4758 charger0=0x81022b code=5
limit_code=5 board_max_code=5 target_code=5
budget_code=5 gadget_ua=500000 detector_ua=0 detector_present=1
POWER_SUPPLY_CONSTANT_CHARGE_CURRENT=480000
POWER_SUPPLY_CONSTANT_CHARGE_CURRENT_MAX=480000
```

MAX14656分类SDP，detector额度0，由gadget配置额度提供500000µA预算。
`state`的charger0/code来自驱动PMIC采样读回，不能把target_code当寄存器读回。
本轮自然full时reason=full、code/target0、raw0x810203；后续eligible再次DAC5。
恢复后还读到input_mv4781、temp284decic、voltage4199000µV、current47302µA、
capacity100、fault0；容量100不自动替代驱动full判定，没有绕过电池保护。
VBUS input_mv约4711–4957为设备采样，净电池电流随恒压/负载变化；
未使用串联电流表，不能报告真实VBUS总电流或把DAC480mA当净电池电流。
PM中额度2mA→100mA→500mA，充电相应暂停/恢复，未见write_error/fault。
未做实体FS主机、墙充/CDP/DCP、拔插、低温、自然低电量或完整充电周期测试。

## 停喂恢复与最终设备状态

只执行一次`kill -STOP "$p"`，p为pidof watchdog得到的官方OpenRC PID299，
先确认watchdog0 active；不发reboot、不关闭watchdog设备。记录停止前boot ID，
随后持续监听串口（不发送Ctrl-C）与SSH，新boot ID比较通过。

```text
Booting entry 'emmc'
Loading ARM Linux zImage '/mnt/emmc/boot/zImage'
recovered=True seconds=90.250 boot_id_changed=True
watchdog status: started / state active
wpa_state=COMPLETED
```

90.250秒是主机USB SSH确认窗口，包含Windows重新枚举/APIPA等待，
不是watchdog硬件超时；Wi-Fi在USB探测窗口内另验证成功。
恢复后root rw实测读写、USB/Wi-Fi SSH22、网关ping2/2、watchdog和sshd started。
`EXT4-fs: recovery complete`后正常rw挂载，无EXT4错误。
再次在途unbind/bind和整屏/局部刷新通过，APBH0/prepare1、ANATOP suspended、
last_error/power_error0、tainted0、WBF再次NVMEM解码。相机文字/棋盘/灰阶确认正常。

照片（仅本地、不入库）：production-pattern.jpg、production-full.jpg、
production-white.jpg、production-black.jpg、after-pm.jpg、modules-after-pm.jpg、
watchdog-recovered-pattern.jpg、final-text.jpg，均在Windows证据目录。
使用capture-kindle-camera.py，manual focus14；初始默认crop780:1050:1590:950，
full-frame核对整屏后扩大crop为980:1120:1450:920，rotate180，完整保留屏幕边缘。

## 问题清单与剩余验收

1. 串口切换必须同一行发送；初次需要用户复位一次，后续自动截住倒计时成功。
2. 两处验收工具假设已修正（shell循环变量、在途EPERM）；不计作驱动通过或缺陷。
3. flash快速连续恢复出现时序问题；独立provider顺序等待3轮通过。快速零等待恢复
   未完全归因，保留原始证据，未为驱动增加延时/保护/包装。
4. 原模块文档的直接rmmod Papyrus不足；内部regulator引用需先unbind。补充顺序
   3轮通过，不强制卸载、不移除合法引用。本轮不修改驱动代码。
5. 默认production与模块RAM通过的功能不能替代debug配置、analog reference-off、
   PFD5或真实功耗/墙充/全速主机/长期压力/独立断电冷启动等未执行场景。

本轮没有第二种合理方法仍失败的设备问题，也未写恢复boot区域。
最终设备保持新默认Alpine production，watchdog持续喂狗。
