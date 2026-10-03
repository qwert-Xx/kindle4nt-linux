<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# 离线收尾全 refs 隐私与许可检查

扫描全部 refs 可达 blobs，含历史版本，以及全部提交作者/提交者/消息元数据。独立 .git 只有 draft/public，无 remote；未push、不重写历史。

未发现实际私钥、Wi-Fi凭据、设备身份/MAC、私有附件或编译二进制。唯一路径规则命中为 project/audit_public.py 自身的扫描正则，人工核对为规则文本。Alpine验签公钥为公开数据，不是私钥。全可达文本无CRLF，提交元数据无隐私模式命中。

当前选定源码/文档SPDX缺口0；编入barebox镜像的环境脚本使用.license旁注保留字节。新增项目配方、锁/包清单/公钥附许可通知或旁注。历史仅 project/debug-patches/README.md 的旧blob a18d41894d62a5892d065a7a9bad9ceecd60f5b5 缺SPDX，当前已补；不重写历史，不宣称全历史许可通知完美。

内核/裸机代码保留GPL/上游通知，Alpine、静态glibc/WPA及官方包许可证与对应源码义务见THIRD-PARTY.md。当前只公开源码/配方与公共公钥，不分发固件、校准、波形、APK、维护二进制或含私有输入根tar。自动扫描不代替逐组件法律审阅；发布前用户许可审阅仍待办。

扫描原始JSON保留在忽略out目录；最终扫描含本记录自身的提交再运行，最终对象数量在交付汇报中给出。构建/测试与逐字节一致结果见REPRO-20261003.md及repro-close-20261003.json；内核patch未变，本轮未重编内核。
