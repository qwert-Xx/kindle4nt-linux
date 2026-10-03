<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# 来源、许可与分发边界

- 内核基于 Linux v6.6.157。主题patch保留每个文件的SPDX与原作者通知，新增正式驱动通常GPL-2.0-only；必要树内接口不是稳定跨版本ABI。
- barebox源码overlay基于v2026.09.0，zqcal保留代码SPDX与对原厂ram_init.S/mx50_suspend.S的来源说明。只发布原创/可提供源码的overlay，不发布实物boot0/SPL二进制或反汇编归档；派生代码作者/许可notice仍须发布前人工复核，不能用脚本扫描替代该审阅。
- 原创主机构建/测试/工具GPL-2.0-or-later，原创文档CC-BY-4.0。LICENSES保存内核项目提供的对应许可文本；以单个文件SPDX为准，GPL-or-later文件可按GPLv2分发。
- BusyBox1.31.1与独立modutils GPLv2系列；Dropbear2024.86多来源MIT等宽松条款；wpa_supplicant2.11 BSD；libnl3.12.0 LGPL2.1系列；iw6.17/regdb2026.09.03 ISC；kexec-tools2.0.32 GPLv2系列。源码归档及SHA见project/userspace/sources.lock.json，每个归档的完整COPYING/LICENSE才是组件通知的依据。当前只发布配方，不发布这些二进制；将来二进制分发必须提供匹配源码/补丁/配置/notice。
- signed regulatory.db按官方release资产取得，不持有维护者签名私钥。ath6kl固件、板级校准、WBF/WRF/VCOM数据、SSH key、Wi-Fi凭据、设备备份和含这些输入的RAM包不在公开树。由本人合法拥有的备份在本地提供，不承诺重分发权。
- 主机工具环境（包括dt-schema、外部SWIG/Python headers）仅核验工具，不是设备运行输入、不开系统安装/CI必需依赖。锁定版本记录与公开源码配方分开。

本地draft不是已批准的GitHub发布；完整人工许可/隐私审阅与阶段4/5冷门槛通过前，不贴冷验release标签，不上传私有运行附件。

- e2fsprogs 1.47.1 使用其各文件 GPL/LGPL/BSD/MIT 通知；mmc-utils v1.0 使用 GPL-2.0 系列，HMAC/SHA2保留BSD声明。锁文件给出源码归档SHA；构建维护包保留完整源码归档/NOTICE。静态glibc重分发还须履行LGPL对应源码与重新链接义务；当前公开草案只分发配方，不分发维护二进制或私有根tar。

Alpine 使用官方 OpenSSH 10.3_p1-r1（SSH-OpenSSH）和 libedit 20260508.3.1-r1（BSD-3-Clause），锁定包与SHA见 project/alpine/packages.lock.json；保留包本身的完整许可通知。Dropbear2024.86只属于BusyBox/RAM维护构建，Alpine不再安装Dropbear。OpenSSH主机私钥、authorized_keys、Wi-Fi凭据仍是仓库外输入。
