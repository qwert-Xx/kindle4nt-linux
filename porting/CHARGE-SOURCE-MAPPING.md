<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# 原厂 USB 充电档位与现代额度交接

原厂输入为 Amazon attributed Linux 2.6.31 的 `drivers/usb/gadget/arcotg_udc.c`
及 `file_storage.c`，以下行号对应K4原厂2.6.31源码。原厂变量名 mA 不代表毫安：实际传递 DAC 码。

| 来源/状态 | 原厂代码与位置 | 当前实现 |
|---|---|---|
| 主机未枚举（物理输入已存在） | arcotg_udc.c:3907-3908 调 CHARGING_HOST，:237 定义为 1 | CHGDETS=1 且 gadget/detector 额度均为0时先 DAC1=80mA；复位后的100mA额度也量化为DAC1 |
| 主机高速配置 | file_storage.c:344 定义 ICHRG_VALUE_HIGH=5（注释480mA），:1468 传码5 | 标准500mA额度直接按标称值量化为 DAC5=480mA |
| 主机全速配置 | file_storage.c:345 定义 ICHRG_VALUE_FULL=1，:1470 传码1 | 有意偏离原厂：与高速相同，按已配置 bMaxPower 预算量化；500mA为DAC5，100mA为DAC1，无速度特例 |
| 墙充/DCP | arcotg_udc.c:3880-3902 依据 PORTSC 线状态识别墙充，:462 调 charging_wall_mA，:4722 初始化为 CHARGING_WALL，:238 定义5 | 保留 MAX14656 DCP 分类/额度，以板级属性480mA选 DAC5 |
| CDP | 原厂该调用链没有独立 BC1.2 CDP 分支，不能声称原厂有 CDP 专用码 | 保留 MAX14656 CDP 额度，复用原厂受控充电最大 DAC5 |
| Unknown/未枚举第三方 | :3908 先码1；:3923-3925 在 J/K 状态安排 third_party_work；:3861-3863 超时仍连接且未枚举时选 CHARGING_THIRD_PARTY=:239 的码5 | 有意偏离原厂：按 BC1.2 处理，MAX14656 未识别的来源按 SDP 规则，非零额度使用 gadget 额度；CHGDETS=1 且两路额度均为0先DAC1，复位后未配置100mA→DAC1，不按超时升档 |
| 断开/挂起 | arcotg_udc.c:3957-3979 断开设码0；USB总线挂起路径本身不直接写充电码，不能与所有停止路径等同 | CHGDETS=0停充；gadget挂起2mA时保持当前档位，仍受故障、电池及用户上限等策略约束 |

`fsl_vbus_draw()` (:2076-2090) 将参数直接保存至 ichrg_value/charger_enumerated；
`pmic_set_chg_current()` (:3602-3618) 将 curr 写入 REG_CHARGE 电流字段。
以上路径直接使用标称DAC码；当前额度按标称表量化。480mA 作为板级 DT
`amazon,max-charge-current-microamp` 保留，binding 与 common DTS 写明出处。

现代 power_supply/USB gadget 仍使用标准微安/毫安单位，不能把 DAC5 错当5mA。
主机尚未复位/配置时 gadget 额度为0：仅当CHGDETS=1且detector也无额度，
按原厂先选DAC1；原始额度仍为0。复位后的未配置 SDP 由上游
`composite_reset()` / `set_config(..., 0)` 提供100mA，量化为DAC1。
CHGDETS=0停充；gadget挂起2mA时以当前DAC作为来源上限，保留当前
档位；原始额度仍取两路较大值。非挂起时按合并额度量化来源上限。
DAC1同样受板级/用户上限、温度及其他既有条件限制。
额度按 MC13892 标称表向下量化，不用芯片公差额外降档；中间的合法额度
例如300/400mA分别量化240/400mA，随后受板级/用户上限、原厂温度等策略限制。
CHRGRAW >=6.0V停充，回落<6.0V重新采样决定恢复；没有输入欠压停充。
完整采样确认CHGDETS=0、合并额度=0且输入<4.4V才清零重试计数。
触发条件的逐项对照见 `CHARGE-STOCK-TRIGGER-AUDIT-20261004.md`。

Unknown 来源不移植原厂 J/K 线状态 + 超时升档。原厂在没有充电器检测硬件
的路径上，用“线处于 J/K、超时仍未枚举”推断第三方充电器；该推断无法区分未
响应的主机口或供电不足的电源。K4 板载 MAX14656 按 BC1.2 区分 SDP/CDP/DCP，
并识别Apple 0.5/1/2A与500mA专用充电器。AL32（Apple 12W）
在当前表中为Unknown、额度0，按Unknown规则处理。原厂超时分支针对的
第三方充电器多数已被标准检测覆盖；仍无法识别的来源按 BC1.2 视为 SDP。
不把 Unknown 描述为已识别 DCP。CDP 行为为现代分类与原厂板级充电码的组合，
不是原厂 CDP 实测证据。
