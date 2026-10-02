<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# ROM RAM 启动与恢复

本指南只描述 RAM 会话。boot1/barebox 持久部署另排，不写 eMMC、idme 或 fuse。原厂 boot0 是回退资产。当前没有已证实的旧内核免按键进入 ROM 软件入口；USB 下载会话 SBMR 与原厂启动不同，不足证明软件可切换启动源。

在设备有足够电量、用户在旁、备份可用时，由已知人工流程进入 ROM，Windows 应枚举 15a2:0052。按 Windows usbipd 已绑定设备的 BUSID 执行 `usbipd attach --wsl KindlePort --busid <BUSID>`，在专用 WSL KindlePort 使用已核对的 imx-usb-loader 配置将匹配 barebox 镜像下载至 RAM。不要使用安装/flash/烧写命令。这里不猜测其它型号的按键组合或替代 loader 参数，实际包须附经过核对的 loader 配置与控制脚本。

先校验整包 SHA；barebox 控制台确认 watchdog/autoping。上传匹配的 zImage、外部 DTB、RAM 根，执行包内 dry-run，核对外部 FDT 地址与 bootargs 后才启动。不要让裸 barebox 默认环境自行启动磁盘。进入 Linux 先核对 USB/guard、所有 mmcblk 只读且无挂载、正式 taint、coldplug/模块匹配，随后才做功能测试。诊断只用 debug profile 或功能通过后的独立显式会话。

正常结束用已验证板级返回，并观察旧系统 USB/健康。120秒无 USB 或未回旧，停止继续命令，由在场用户按既定恢复流程直接重新进入 ROM以保留证据；先 SDP READ_REGISTER 只读取证、不加载镜像或执行 DCD。DDR 未初始化则跳过高端 RAM，OCRAM 记录必须避开 ROM 保留区，早期工具记录使用 f8006000 以后并避开其它占用。取证后人工长按回旧，立即抢读 RAM trace，再健康检查。内存残留可能损坏，按 CRC 双副本校验，随机字节不能证明卡点。

watchdog/guard 是恢复兜底，不能保证每次硬件状态均自行回旧；不得删除、延长或绕过保护来让测试看似成功。本地冻结包与 raw 证据含私有输入，不能直接上传 GitHub。
