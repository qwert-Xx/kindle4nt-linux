<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# kindle4nt-linux

Linux 6.6.157, barebox and an Alpine root for the Kindle 4 non-touch D01100 (Yoshi / Tequila).

[简体中文](README.zh-CN.md). This is an unofficial community project by qwert-Xx, not affiliated with or endorsed by Amazon, Lab126, NXP/Freescale or the upstream projects. Kindle and other product names are trademarks of their respective owners.

**Writing eMMC boot1 or partition p1 can destroy data, brick the device and void your warranty.** Prepare verified backups and a working recovery path first. Hold **Down while resetting** to enter the i.MX ROM downloader, then load USB barebox and a Linux RAM maintenance system. Do not rely on the short Ctrl-C window as the only recovery method. Changing EXT_CSD[179] back does not restore an overwritten p1.

## Status

Only **D01100** is supported. Evidence comes from one device; broader hardware validation is pending. Existing device results are recorded here; release preparation runs only on the host.

| Area | Verified on the reference device | Gaps / known issues |
| --- | --- | --- |
| Boot and storage | boot1 barebox v8, EXT_CSD[179]=0x50, automatic Alpine 3.24.2 p1 boot; three normal reboots | independent battery cold boot, second device, durability and recovery rehearsal |
| Display and suspend | first refresh, RTC STOP at both CPU operating points, retained memory and refresh after resume | physical rail/power measurement, long sleep and many cycles |
| Network and time | WPA2-PSK/CCMP, DHCP, USB console/SSH, NTP and normal shutdown SRTC writeback, HTTPS apk update | other Wi-Fi modes, physical unplug/replug, apk upgrade |
| Recovery | Down/reset ROM path and RAM maintenance workflow; v8 serial Ctrl-C interruption | five-second window end and host enumeration timing; historical RAM guard-to-ROM cause unresolved |
| Release builds | see [current host validation](project/docs/RELEASE-VALIDATION.md) | source builds with a user key/private inputs have different root hashes; no new hardware acceptance |

## Prepare

Use a Linux build host (reference: Ubuntu 24.04, Python 3.12, ARM hard-float GCC 13.3 / binutils 2.42). Install make, GCC host tools, flex, bison, bc, libssl-dev, pkg-config, patch, tar, xz, curl, GnuPG, openssl, kmod and the ARM cross compiler. The manifest also pins the old Linaro compiler required for the BusyBox maintenance build. Run as an ordinary user (this validation used the kindle account, UID 1000). See [source inputs](sources/README.md) and [build details](project/docs/BUILD.md).

Keep an external cache, external build directory and external private-input directory. Extract firmware/calibration, panel waveforms and boot0/idme from **your own device/backups** as described in [THIRD-PARTY.md](THIRD-PARTY.md). Supply Wi-Fi configuration and SSH authorization/identity separately if needed. No images, APKs, root archives, credentials, private signing keys or proprietary firmware are distributed in this repository.

## Quick start

One host-only command downloads locked upstream inputs, verifies hashes and Linux signatures, applies patches and builds Linux, barebox, userspace, a user-signed WPA APK and the Alpine root:

```sh
python3 project/release.py --cache /external/source-cache --out /external/new-build --private-inputs /external/device-inputs
```

Add `--offline` to use an already verified cache. Alpine Wi-Fi uses official signed main 2.11-r4 packages; no user signing key is needed. The frozen Alpine index may no longer exist on the live mirror; retain the verified cache rather than silently upgrading versions.

Deployment is a **separate manual operation**: Ctrl-C in barebox, or Down/reset → ROM, then USB barebox → RAM maintenance → back up and verify storage → write/verify boot1 and p1 → activate and reboot. Read [boot1 instructions](project/docs/BAREBOX-BOOT1.md) and [Alpine deployment](project/docs/ALPINE-ROOT.md) in full. Never format the currently mounted p1 root. No build command deploys to a device.

## Maintenance and recovery

The normal Alpine root continuously feeds the watchdog; RAM maintenance has a finite guard. Keep matching kernel/DTB/modules and a known-good RAM rescue package. Hold Down during reset for ROM rescue. Restore boot1 from your complete verified backup, or restore p1 from your own root backup in RAM; selecting original boot0 alone cannot restore the original OS. See [known issues](project/docs/KNOWN-ISSUES.md) and [RAM recovery](project/docs/RAM-BOOT.md).

## Licenses and acknowledgements

Kernel/barebox patches and derivative code: GPL-2.0-only. Original scripts/tools: GPL-2.0-or-later. Documentation: CC-BY-4.0. Individual upstream notices and file license expressions remain applicable. Full texts are in [LICENSES](LICENSES); see [copyright provenance](COPYRIGHT-PROVENANCE.md) and [third-party components](THIRD-PARTY.md). Attribution classifications were reviewed and approved by the project owner; the provenance table records the source and notice for each affected file.

Thanks to Linux, barebox, Alpine, BusyBox and the other upstream maintainers, and to the Amazon/Lab126/Freescale original open-source code authors. This repository contains source, patches, recipes and build scripts only.
