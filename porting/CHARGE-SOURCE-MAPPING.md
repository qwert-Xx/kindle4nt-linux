<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# 原厂 USB 充电档位与现代额度交接

原厂输入为 Amazon attributed Linux 2.6.31 的 `drivers/usb/gadget/arcotg_udc.c`
及 `file_storage.c`，本地只读参考位于 `reference/stock-audit-2.6.31-20261001`。
以下行号对应该参考源码。原厂变量名 mA 不代表毫安：实际传递 DAC 码。

| 来源/状态 | 原厂代码与位置 | 本次实现 |
|---|---|---|
| 主机未枚举（100mA 初始额度） | arcotg_udc.c:3907-3908 调 CHARGING_HOST，:237 定义为 1 | 正预算 100mA 向下量化为 DAC1=80mA |
| 主机高速配置 | file_storage.c:344 定义 ICHRG_VALUE_HIGH=5（注释480mA），:1468 传码5 | 标准500mA额度直接按标称值量化为 DAC5=480mA |
| 主机全速配置 | file_storage.c:345 定义 ICHRG_VALUE_FULL=1，:1470 传码1 | 有意偏离原厂：与高速相同，按已配置 bMaxPower 预算量化；500mA为DAC5，100mA为DAC1，无速度特例 |
| 墙充/DCP | arcotg_udc.c:3880-3902 依据 PORTSC 线状态识别墙充，:462 调 charging_wall_mA，:4722 初始化为 CHARGING_WALL，:238 定义5 | 保留 MAX14656 DCP 分类/额度，以板级属性480mA选 DAC5 |
| CDP | 原厂该调用链没有独立 BC1.2 CDP 分支，不能声称原厂有 CDP 专用码 | 保留 MAX14656 CDP 额度，复用原厂受控充电最大 DAC5 |
| Unknown/未枚举第三方 | :3908 先码1；:3923-3925 在 J/K 状态安排 third_party_work；:3861-3863 超时仍连接且未枚举时选 CHARGING_THIRD_PARTY=:239 的码5 | 按用户范围决定维持现有分类；Unknown 无检测额度，不新增超时猜墙充。若另有有效 gadget 额度，则按其额度充电 |
| 断开/零额度/挂起 | 原厂断开与停止路径设码0 | 标准零或低于80mA额度选码0 |

`fsl_vbus_draw()` (:2076-2090) 将参数直接保存至 ichrg_value/charger_enumerated；
`pmic_set_chg_current()` (:3602-3618) 将 curr 写入 REG_CHARGE 电流字段。
以上路径没有减60mA、按+15%扣减或最坏上界换算。删除这两项移植策略，
也删除 reserve DT 属性及驱动成员，不保留旧并行路径。480mA 作为板级 DT
`amazon,max-charge-current-microamp` 保留，binding 与 common DTS 写明出处。

现代 power_supply/USB gadget 仍使用标准微安/毫安单位，不能把 DAC5 错当5mA。
未配置的已连接 SDP 由上游 `composite_reset()` / `set_config(..., 0)` 提供100mA，
量化为DAC1；断开0和挂起2mA仍为DAC0，不能把所有零额度当未配置并提高。
额度按 MC13892 标称表向下量化，不用芯片公差额外降档；中间的合法额度
例如300/400mA分别量化240/400mA，随后受板级/用户上限、原厂温度等策略限制。
MAX14656 分类/错误处理、温度、电压、低压、充满、硬件故障及累计时长策略未改。

后续项：原厂 J/K 线状态与超时第三方升档，需单独评估现代分类交接与真实源
识别，当前未实现，也不把 Unknown 描述为已识别 DCP。CDP 行为为现代分类与
原厂板级充电码的组合，不是原厂 CDP 实测证据。
