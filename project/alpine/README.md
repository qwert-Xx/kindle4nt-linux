<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Offline Alpine K4 recipe

Use official main wpa_supplicant 2.11-r4 and its OpenRC split package, locked with SHA256 in packages.lock.json and PACKAGES.tsv. K4 Wi-Fi continues to call /sbin/wpa_supplicant; the distribution Wi-Fi service is not enabled. No local APK repository, build, signing key or package signature workflow is needed.

download.py obtains locked official inputs; build.py authenticates and installs them offline; verify.py checks ABI, versions, paths, dependencies and reproducibility; ram.py prepares the RAM image. Private inputs and outputs stay outside Git.
