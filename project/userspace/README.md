<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# 用户态源码重建（不替换运行输入）

这是 host-only 核验配方。输出必须是新的仓库外目录；不连接设备、不安装系统包、不自动下载、不覆盖原目录，也不将结果写入 RAM 根。先备齐 sources.lock.json 列出的归档，在外部 JSON 中用归档文件名映射到本地绝对路径；归档逐项SHA校验，配置与补丁在本目录。

```sh
python3 project/userspace/rebuild.py --cache-map /external/sources.json --out /external/new-rebuild --reference /external/accepted/inner/bin
python3 project/userspace/test_compare.py
```

版本：BusyBox1.31.1（启动与独立modutils各一配置），Dropbear2024.86，wpa_supplicant2.12+有界扫描重试补丁，libnl3.12.0，iw6.17，wireless-regdb2026.09.03。libnl静态库作为Wi-Fi构建依赖，不是单独运行文件。参数与日志见rebuild.py、wifi.sh；WPA只启nl80211/内部加密，不添加TLS/EAP/WPA3功能；Dropbear密码认证关闭。modutils不启blacklist，运行coldplug不使用-b。

启动BusyBox用归档锁定的 Linaro GCC4.9.4-2017.01 arm-linux-gnueabi（含配套libc/binutils），其余用 Ubuntu ARMhf GCC13.3.0-6ubuntu2~24.04.1、gcc交叉包13.3.0-6ubuntu2~24.04.1cross1、binutils2.42-4ubuntu2.10、libc6-dev-armhf-cross2.39-0ubuntu8cross1。配方严格核验compiler版本；完整包版本见证据，非同工具链不能沿用等价结论。构建依赖现有make/autoconf生成文件、pkg-config、openssl、Python3，不新建venv。

BusyBox1.31.1的confdata.c直接生成AUTOCONF_TIMESTAMP，不支持用KBUILD_BUILD_TIMESTAMP锁此串。prepare后仅固定generated include/autoconf.h的时间宏，分别2026-09-24 23:41:16 CST与2026-09-27 21:26:22 CST；不改运行逻辑。参考二进制时间不同须先明确新基线，不能静默改。

本轮7个第三方ELF：modutils/dropbear/dropbearkey3个逐字节相同；busybox/wpa_supplicant/wpa_cli/iw4个整文件仅20字节GNU build-id描述符不同（iw实际19字节差异）。compare.py只清零该note中的描述符，ELF头、全部段、填充及其它每个字节均比较，不是只比.text。构建路径/未strip的调试输入等会影响链接build-id，strip后保留该ID；没有为了凑旧哈希伪造ID。代码、数据、配置与文件布局完全一致，等价边界仅编译标识，不宣称最终文件SHA一致。

regulatory.db从db.txt/db2fw.py重建，和原RAM根字节一致；regulatory.db.p7s复制SHA锁定官方release资产，与原RAM根相同。使用归档wens.x509.pem验证detached CMS签名，-noverify意味着不验证外部PKI信任链，归档SHA是此处信任锚；不是重新签名，不掌握维护者私钥。不要运行regdb make all生成个人key。

可选kexec-tools2.0.32为外部会话恢复工具，不是当前内层根的7个第三方ELF之一：先核验锁定Linaro归档，再 `bash project/userspace/kexec.sh /external/cache /external/new-kexec /external/linaro/bin/arm-linux-gnueabi-`，显式交叉CC/LD/AS/AR/STRIP，应用DTB handoff补丁。已构建；原文件包含符号/调试元数据，两个隔离副本strip后仅build-id不同。原工具与所有运行输入不替换。

外层BusyBox与内层同SHA；其它k4-*为项目源码/脚本（guard、health、bootstrap、显示/PM/探针等），不冒充第三方；归档源码位置与现有正式构建由项目root配方锁定。签名regdb可公开按许可取得，ath6kl固件/校准、WBF/WRF、Wi-Fi/SSH配置不能随配方入库。归档从对应上游release取得再校验sources.lock，无法取得锁定版本时停止，不切换最新版。

第三方许可证须保留其源码归档的完整COPYING/LICENSE：BusyBox/kexec GPL-2.0系列，libnl LGPL-2.1系列，wpa_supplicant BSD，iw/regdb ISC，Dropbear含MIT及多来源条款，配套glibc/工具链按各自许可。原创配方GPL-2.0-or-later不改变第三方许可；发布二进制前完成源码提供义务与完整notice整理（阶段7）。
