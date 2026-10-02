#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Apply only the seven ZQ DCD writes; stdlib only, no device access."""
import argparse, hashlib, json, re, struct
from pathlib import Path
ADDRESSES = [0x1400012c, 0x14000128, 0x14000124, 0x14000124,
             0x14000128, 0x14000124, 0x14000124]
ZQ = set(ADDRESSES)
UPSTREAM = [0x817, 0x09180000, 0x310000, 0x200000, 0x09180010, 0x310000, 0x200000]
WRITE = re.compile(r"^wm\s+32\s+(0x[0-9a-fA-F]+)\s+(0x[0-9a-fA-F]+)\s*$")

def expected(pu, pd):
    if not 0 <= pu <= 30 or not 0 <= pd <= 14:
        raise ValueError("plus-one field overflow")
    cfg = ((pd + 1) << 24) | ((pu + 1) << 16)
    return list(zip(ADDRESSES, [(pd << 8) | pu, cfg, 0x310000,
                              0x200000, cfg | 16, 0x310000, 0x200000]))

def parse_fragment(text):
    pairs = []
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line: continue
        match = WRITE.fullmatch(line)
        if not match: raise ValueError("fragment allows only wm 32 ZQ writes")
        pairs.append(tuple(int(x, 16) for x in match.groups()))
    if len(pairs) != 7 or [a for a, v in pairs] != ADDRESSES:
        raise ValueError("wrong ZQ write order or length")
    pu = pairs[0][1] & 31
    pd = (pairs[0][1] >> 8) & 15
    if pairs != expected(pu, pd): raise ValueError("not the shipped LPDDR1 encoding")
    return pairs, pu, pd

def apply(base, fragment):
    pairs, pu, pd = parse_fragment(fragment)
    lines = base.splitlines(keepends=True)
    indices, old = [], []
    for index, line in enumerate(lines):
        match = WRITE.fullmatch(line.strip())
        if match and int(match[1], 16) in ZQ:
            indices.append(index); old.append((int(match[1], 16), int(match[2], 16)))
    if old != list(zip(ADDRESSES, UPSTREAM)):
        raise ValueError("upstream seven-write baseline changed; review required")
    for index, (address, value) in zip(indices, pairs):
        lines[index] = f"wm 32 0x{address:08x} 0x{value:08x}\n"
    return "".join(lines), pu, pd

def dcd_writes(data):
    ivt = 0x400
    if len(data) < ivt + 32: raise ValueError("truncated IVT")
    if data[ivt] != 0xd1 or int.from_bytes(data[ivt+1:ivt+3], "big") != 32:
        raise ValueError("not the expected i.MX50 IVT")
    dcd_ptr, self_ptr = struct.unpack_from("<I", data, ivt+12)[0], struct.unpack_from("<I", data, ivt+20)[0]
    pos = ivt + dcd_ptr - self_ptr
    if pos < 0 or pos + 4 > len(data) or data[pos] != 0xd2:
        raise ValueError("invalid DCD pointer/header")
    end = pos + int.from_bytes(data[pos+1:pos+3], "big")
    if end < pos + 4 or end > len(data): raise ValueError("truncated DCD")
    pos += 4
    writes = []
    while pos < end:
        if pos + 4 > end: raise ValueError("truncated command header")
        tag, length, flags = data[pos], int.from_bytes(data[pos+1:pos+3], "big"), data[pos+3]
        if length < 4 or pos + length > end: raise ValueError("bad DCD command length")
        if tag == 0xcc:
            if flags != 4 or (length - 4) % 8: raise ValueError("unexpected write format")
            for offset in range(pos+4, pos+length, 8):
                writes.append(struct.unpack_from(">II", data, offset))
        elif tag != 0xcf:
            raise ValueError("unexpected DCD command")
        pos += length
    return writes

def measurement(text):
    rows = re.findall(r"record run (\d+): PU=(\d+) PD=(\d+) status=(-?\d+) checks=([0-9a-f]+)", text)
    if len(rows) != 16 or any(row[3:] != ("0", "00000007") for row in rows):
        raise ValueError("measurement must contain 16 fully verified records")
    if [int(x[0]) for x in rows] != list(range(1, 17)):
        raise ValueError("measurement sequence missing")
    values = {(int(x[1]), int(x[2])) for x in rows}
    if len(values) != 1: raise ValueError("this profile needs a reviewed stable 16-run result")
    return values.pop()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=["apply", "verify"])
    p.add_argument("--profile", required=True, type=Path)
    p.add_argument("--header", type=Path)
    p.add_argument("--image", type=Path)
    p.add_argument("--measurement", type=Path)
    a = p.parse_args()
    pairs, pu, pd = parse_fragment(a.profile.read_text(encoding="utf-8"))
    if a.action == "apply":
        if not a.header: p.error("--header required")
        result, pu, pd = apply(a.header.read_text(encoding="utf-8"), a.profile.read_text(encoding="utf-8"))
        a.header.write_bytes(result.encode())
        print(json.dumps({"profile": a.profile.name, "PU": pu, "PD": pd}))
    else:
        if not a.image or not a.measurement: p.error("--image and --measurement required")
        if measurement(a.measurement.read_text(encoding="utf-8")) != (pu, pd):
            raise ValueError("profile differs from measured machine")
        writes = dcd_writes(a.image.read_bytes())
        if [(x,y) for x,y in writes if x in ZQ] != pairs:
            raise ValueError("image DCD differs from profile")
        print(json.dumps({"profile": a.profile.name, "PU": pu, "PD": pd,
                          "ZQ_writes": pairs, "DCD_writes": len(writes),
                          "image_sha256": hashlib.sha256(a.image.read_bytes()).hexdigest(),
                          "measurement_sha256": hashlib.sha256(a.measurement.read_bytes()).hexdigest(),
                          "physical_storage_writes": False, "cold_verified": False}, indent=2))
if __name__ == "__main__": main()
