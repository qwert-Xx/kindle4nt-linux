<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Offline Alpine K4 recipe

Official 2.11-r4 supplicant and wpa_cli OpenRC services handle association and DHCP events. networking/ifupdown-ng handles wlan0 DHCP and usb0 static addressing. WPACLI_OPTS enables Alpine default wpa_cli.sh; conf.d dependencies follow K4 coldplug. Lock files cover all 77 official packages. External private Wi-Fi credentials are installed at /etc/wpa_supplicant/wpa_supplicant.conf (600). Only Alpine drops the K4 Wi-Fi supervisor; BusyBox recipes retain it.

See the standard networking offline report for exact settings, device evidence, two-build reproduction and comparison boundaries.
