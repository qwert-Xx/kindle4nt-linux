#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
import argparse,hashlib,pathlib
p=argparse.ArgumentParser(description='Host-only frozen package checks');p.add_argument('package');a=p.parse_args();r=pathlib.Path(a.package).resolve()
for line in (r/'SHA256SUMS').read_text().splitlines():
 sha,name=line.split('  ',1);n=pathlib.PurePosixPath(name)
 if n.is_absolute() or '..' in n.parts:raise ValueError('unsafe checksum path')
 assert hashlib.sha256((r/name).read_bytes()).hexdigest()==sha,name
print('FROZEN_HASHES_PASS_NO_DEVICE_OPERATIONS')
