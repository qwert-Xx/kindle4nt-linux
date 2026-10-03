<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Offline Alpine K4 recipe

Official 2.11-r4 supplicant and wpa_cli OpenRC services handle association and DHCP events. networking/ifupdown-ng handles wlan0 DHCP and usb0 static addressing. WPACLI_OPTS enables Alpine default wpa_cli.sh; conf.d dependencies follow K4 coldplug. Lock files cover all 84 official packages. External private Wi-Fi credentials are installed at /etc/wpa_supplicant/wpa_supplicant.conf (600). Only Alpine drops the K4 Wi-Fi supervisor; BusyBox recipes retain it.

See the standard networking offline report for exact settings, device evidence, two-build reproduction and comparison boundaries.
Official OpenSSH 10.3_p1-r1 uses the unmodified Alpine sshd OpenRC service on port 22, listening on all IPv4/IPv6 addresses. USB (169.254.212.2) and Wi-Fi accept root public-key authentication; passwords and keyboard-interactive authentication are disabled, and SFTP uses internal-sftp. USB gadget initialization stays in k4-platform and ttyGS0 remains a root shell. RAM maintenance retains Dropbear on port 2222.

Provide an external OpenSSH-format ECDSA private host key with --ssh-host-key /absolute/ssh_host_ecdsa_key (installed mode 600; its public key is derived mode 644). Preserve the existing identity when migrating. Omit this option to let the standard Alpine sshd service generate an ECDSA key at first start. No host keys are generated during assembly. Supply root authorization with --authorized-keys /absolute/authorized_keys (600), or stage root/.ssh/authorized_keys in the existing external K4 root input. Keep all keys and credentials outside Git. Two builds reproduce exactly only with identical external inputs; first-start generated identities are runtime data.
