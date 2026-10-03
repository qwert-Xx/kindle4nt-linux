<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Locked upstream inputs

The manifest records archives, host tools and every selected Alpine APK. No archive is distributed here. Run `python3 sources/fetch.py --cache /external/cache` to download and verify; add `--offline` to use only local verified cache. A mutable Alpine index is deliberately rejected when it no longer matches the frozen snapshot; preserve the verified cache. APK verification is also mandatory in project/alpine/build.py, using the keys from the locked minirootfs, signed index membership and `apk verify`. The local K4 APK has a separate public key and lock.

Linux uses the kernel.org developer signature over the uncompressed tar, with the key acquired using WKD. See https://www.kernel.org/signature.html. The official barebox release provides MD5; we additionally record SHA256 and compare to the local release tag. The mmc-utils legacy archive needs upstream snapshot verification before the release gate can pass.
