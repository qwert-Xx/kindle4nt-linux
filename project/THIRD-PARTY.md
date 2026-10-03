<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# 来源、许可与分发边界

- 内核基于 Linux v6.6.157。主题patch保留每个文件的SPDX与原作者通知，新增正式驱动通常GPL-2.0-only；必要树内接口不是稳定跨版本ABI。
- barebox源码overlay基于v2026.09.0，zqcal保留代码SPDX与对原厂ram_init.S/mx50_suspend.S的来源说明。仓库提供源码配方、板级补丁与配置，不包含实物 boot0/SPL 备份。
- 原创主机构建/测试/工具GPL-2.0-or-later，原创文档CC-BY-4.0。LICENSES保存内核项目提供的对应许可文本；以单个文件SPDX为准，GPL-or-later文件可按GPLv2分发。
- BusyBox1.31.1与独立modutils GPLv2系列；Dropbear2024.86多来源MIT等宽松条款；wpa_supplicant2.11 BSD；libnl3.12.0 LGPL2.1系列；iw6.17/regdb2026.09.03 ISC；kexec-tools2.0.32 GPLv2系列。源码归档及SHA见project/userspace/sources.lock.json，每个归档的完整COPYING/LICENSE才是组件通知的依据。当前只发布配方，不发布这些二进制；将来二进制分发必须提供匹配源码/补丁/配置/notice。
- signed regulatory.db按官方release资产取得，不持有维护者签名私钥。ath6kl固件、板级校准、WBF/WRF/VCOM数据、SSH key、Wi-Fi凭据、设备备份和含这些输入的RAM包不在公开树。由本人合法拥有的备份在本地提供，不承诺重分发权。
- 主机工具环境（包括 dt-schema、SWIG/Python headers）用于构建或校验，与设备运行输入分别记录。

Alpine 使用官方 OpenSSH 10.3_p1-r1（SSH-OpenSSH）和 libedit 20260508.3.1-r1（BSD-3-Clause），锁定包与SHA见 project/alpine/packages.lock.json；保留包本身的完整许可通知。Dropbear2024.86只属于BusyBox/RAM维护构建。OpenSSH主机私钥、authorized_keys、Wi-Fi凭据仍是仓库外输入。
