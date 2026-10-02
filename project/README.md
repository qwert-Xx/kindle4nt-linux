<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# K4 离线构建入口

`make -C project images INPUTS=/absolute/external/inputs.json OUT=/absolute/external/build`

仅执行主机构建，不连接设备、不加载镜像、不执行诊断、不调用 SSH/ROM/响铃或远端发布。OUT 必须在源码树之外。Linux v6.6.157、ARM GCC 13.3/binutils 2.42 是当前内核验证组合；barebox 基线仍使用原 GCC 11.4/上游 ZQ 23/8，不由此入口重建或升级。

## 输入与配方

外部 JSON 包含 `inputs.config`（`path/sha256`）、`dtb`（如 `nxp/imx/imx50-kindle-k4-stock-pxp.dtb`）、`release`、`metadata`（KBUILD_BUILD_*），以及可选 `cross_compile`。相对路径相对于 JSON；哈希错误立即停止。

`inputs.ram_recipe` 是外部 JSON 文件（同样有 path/sha256），内含 `entries`：每项 `name/kind/mode`，file 另有 `source/sha256`，link 有 target，char/block 有 major/minor。源码文本、固定用户态二进制、固件、波形、私有配置均显式列出，不从个人目录自动搜集。

有内层 ext3 时，外层配方写 `filesystem_recipe/filesystem_recipe_sha256` 指向第二份外部 JSON；其 entries 是逐文件根目录清单，另有 image_bytes/uuid。构建用 mke2fs/debugfs 创建**主机普通文件**，从不挂载或打开板上设备。内层模块从本次 modules_install 结果重新加入，排除主机 build/source symlink，保留基线权限。cpio 固定时间生成；ext3 以条目类型/权限/链接/文件哈希作语义比较（文件系统内部元数据可能不同）。

诊断默认关闭：配方 automatic_diagnostics 默认 false，bootmark 替换为成功返回的空 stub；watchdog/health/板级返回和只读检查脚本不替换。正式构建拒绝声明自动诊断的配方，也拒绝未列出内层逐文件配方的不透明 ext3。compatibility 的 `profile: private-replay` 可显式保留已验收的诊断环境；这是本地等价验证专用。

Wi-Fi 配置、SSH key、ath6kl 固件/校准、WBF/WRF 波形和所有含这些输入的运行包均留在仓库外。配方用 private_inputs=true 标注，产物不可直接公开重分发。固件/波形从本人合法持有的原厂只读备份取得，不打包发布。外部用户态二进制须记录来源/版本/许可；第三方用户态源码核验配方见 userspace/README.md；该步骤不替换固定运行输入。

`inputs.ram_root/barebox` 仅 private-replay 接受，逐字节保留明确 SHA 的旧验收输入；它们不代替逐文件 RAM 根配方。基线的旧临时 weak UTS 和空 cpio mtime 可在 baseline_metadata 中指定：temporary_uts、empty_cpio_epoch。从同一源码重建，未复制旧 kernel 对象或 zImage。

`build-report.json` 保存产物 SHA、modules.order、config SHA 和 RAM 配方报告。新入口已验证 zImage/DTB/235模块精确一致，外层25项与内层412项语义一致；构建和物理验收严格分开。

## 导出与测试

`python3 project/export.py --out <new-directory>` 只导出主题 patch 与 project 白名单，不复制 Git 历史、porting 原始日志或外部输入。导出是本地预览，发布前仍须许可/隐私审查，不自动 push。

`python3 project/test_build.py`、`python3 project/test_rootfs.py` 使用现有 Python/C 工具，不装包、不新建 venv。

## 阶段2双 profile 与外部源码

干净公共项目不包含 Linux 历史。先在独立 Linux v6.6.157 工作树应用 kernel/patches/series；debug 再显式应用 kernel/debug-patches/series。可用 make -C project images SOURCE=/path/to/linux INPUTS=/path/to/inputs.json OUT=/path/to/out；或 JSON 的 kernel_source（相对于 JSON）指明源码目录。无需把源码搬进公共仓库。未给 config 时使用 project/configs/k4-production.config，kernel_profile=debug 才选 debug 配置。默认 release/构建用户/主机/时间固定为通用值。正式配方检查 OCRAM/PM/health/restart/charger/USB/watchdog 内建，并拒绝与 profile 不符的诊断配置。

正式 DTS 使用阶段3已等价验证的 common + 顶层结构，不绑定独立诊断驱动；历史 include 链仅本地归档。共享 Papyrus 寄存器头保留正式路径，STOP 汇编/代码偏移/池布局不变，trace 返回 stub 不参与功能成功判定。

阶段3 DTS：默认正式目标为 `nxp/imx/imx50-kindle-k4.dtb`，只包含正式 common；旧 `stock-pxp` 别名继续兼容外部配方，两者与已冷验基线字节相同。debug 顶层为 `nxp/imx/k4-debug/imx50-kindle-k4-debug.dtb`，需 debug patch 系列；debug kernel profile 不改变硬件参数。74份历史 DTS 只在研究仓库本地归档，不公开导出，不列入默认 dtbs。离线等价检查：`python3 project/verify_dtb.py --baseline BASE.dtb --candidate NEW.dtb --report REPORT.json`；报告包含五类硬件属性逐项对照。W=1 dtc检查不等同 dt-schema，后者现已用外部独立工具验证；K4专项通过、全量剩上游CCM IRQ编码问题，见docs/KNOWN-ISSUES.md。

Stage 4 input profile: production GPIO_KEYS is modular; power-button and recovery drivers stay builtin. Structured RAM-root generation wraps the unchanged external rcS as rcS.k4-base, then runs generic modalias coldplug after protected startup succeeds (10 s per request, 60 s total). Coldplug is nonfatal, does not feed watchdog, uses existing modprobe without -b or blacklist, and skips already bound devices. Original SPI coldplug is preserved. Production excludes dmatest/usbtest and rejects diagnostic modules in the installed root; debug does not automatically run generic coldplug. BusyBox/modutils binaries are external hashed inputs and unchanged. Hardware acceptance remains pending the combined stage4 checklist.

公共草稿入口：[范围与状态](docs/README.md)、[构建](docs/BUILD.md)、[RAM启动/恢复](docs/RAM-BOOT.md)、[zqcal](docs/ZQCAL.md)、[限制](docs/KNOWN-ISSUES.md)。这些说明不扩大既有硬件验收范围，不提供boot1安装方案。

阶段7可选 `filesystem_recipe.reproducible_metadata=true` 固定主机ext3内部时间与目录hash seed；默认false保留旧配方。仅元数据，不改条目内容/模式/链接/设备号，guard/只读保护代码不变。两次clean比对使用独立外部配方启用，不重写任何冻结包。
