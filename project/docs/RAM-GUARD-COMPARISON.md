<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# WDI 方案 A 与三轮 RAM guard 对照

脱敏摘要，依据研究分支 74ff1775e 的三轮记录，不发布原始串口、内存、设备身份或网络标识。

| 入口/外部 DTB | 实读 WDI | 30秒 expire-health 自然退出后 |
| --- | --- | --- |
| kexec，继承方案 A | ALT2/0x0c | 自动经 v7 回 eMMC，WRSR10/SRSR0 |
| ROM→冻结 USB barebox→YMODEM，旧 DTB | ALT1/0x84 | 掉 ROM；人工恢复前 SRC reset 状态0x10 |
| 相同 ROM/USB/YMODEM，仅换方案 A DTB | ALT2/0x0c | 自动经 v7 回 eMMC，无 ROM，WRSR10/SRSR0 |

各轮均采集到期后超过250秒。支持本条件下 WDI 配置影响恢复；每条件只有一轮，非900秒维护包/v5完整重演，不证明唯一历史根因或长期可靠性。第三轮控制器和卡 runtime suspended 仅为软件 PM 状态，不是 card sleep/物理断电证据；第二轮无 runtime 状态，不能追补。
原厂 WDI ALT2 作为硬件基线；现代 restart pinctrl 持有方式是接口实现差异。没有因为对照添加永久限频或改电源参数。当前维护使用方案 A 与900秒 guard，在健康期限内主动 reboot；人工 ROM 恢复仍需预备。
