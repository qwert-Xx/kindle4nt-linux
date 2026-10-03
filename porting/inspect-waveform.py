#!/usr/bin/env python3
"""Inspect Amazon WBF and its separate EPDC WRF proxy without loading hardware.

Header offsets come from the K4 GPL eink_waveform.h and mxc_epdc_fb.c.
WRF keeps WBF metadata; its header filesize/CRC are NOT WRF integrity fields.
"""
import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import struct
import sys
import zlib

HEADER_SIZE = 48
WBF_LIMIT = 256 * 1024
WRF_LIMIT = 2 * 1024 * 1024


class WaveformError(ValueError):
    pass


def load_file(path, limit):
    with Path(path).open("rb") as stream:
        encoded = stream.read(limit + 4097)
    if len(encoded) > limit + 4096:
        raise WaveformError("encoded input exceeds size limit")
    if encoded.startswith(b"\x1f\x8b"):
        try:
            with gzip.GzipFile(fileobj=io.BytesIO(encoded)) as stream:
                data = stream.read(limit + 1)
        except (OSError, EOFError, zlib.error) as exc:
            raise WaveformError("invalid or truncated gzip") from exc
    else:
        data = encoded
    if len(data) > limit:
        raise WaveformError("decoded input exceeds size limit")
    return data


def layout(data):
    if len(data) < HEADER_SIZE:
        raise WaveformError("truncated 48-byte waveform header")
    temperatures = data[38] + 1
    # Same copy boundary as the old K4 and NXP EPDC firmware loader.
    offset = HEADER_SIZE + temperatures + 1
    if offset >= len(data):
        raise WaveformError("truncated temperature table or empty waveform payload")
    return {
        "header_size": HEADER_SIZE,
        "temperature_entries": temperatures,
        "temperature_bounds_raw": list(data[HEADER_SIZE:offset - 1]),
        "byte_after_temperature_table": data[offset - 1],
        "data_offset_after_header_and_temperature_table": offset,
        "data_size_after_header_and_temperature_table": len(data) - offset,
        "mode_count_field": data[37],
        "format_version": data[35],
        "luts_field": data[36],
    }


def inspect_wbf(data):
    if len(data) > WBF_LIMIT:
        raise WaveformError("WBF exceeds K4 source's 256 KiB bound")
    result = layout(data)
    stored, declared = struct.unpack_from("<II", data)
    if declared:
        if declared != len(data):
            raise WaveformError("WBF declared filesize does not match input (WRF is separate)")
        computed = zlib.crc32(bytes(4) + data[4:]) & 0xffffffff
        if computed != stored:
            raise WaveformError("WBF CRC32 mismatch")
        integrity = "whole_file_crc32_verified"
    else:
        if (sum(data[:31]) & 255) != data[31] or (sum(data[32:47]) & 255) != data[47]:
            raise WaveformError("legacy WBF header checksum mismatch")
        integrity = "legacy_header_sum8_only_payload_unverified"
    result.update({
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "declared_wbf_size": declared,
        "integrity": integrity,
        "waveform_type": f"0x{data[19]:02x}",
        "mode_version": data[16],
        "panel_platform": data[13],
        "panel_size_code": f"0x{data[20]:02x}",
        "manufacturer_code": f"0x{data[21]:02x}",
        "frame_rate_code": f"0x{data[23]:02x}",
        "xwia_address_in_wbf": int.from_bytes(data[28:31], "little"),
        "wmta_address_in_wbf": int.from_bytes(data[32:35], "little"),
    })
    return result


def inspect_pair(wbf, wrf=None):
    result = {"wbf": inspect_wbf(wbf), "hardware_compatibility": "unverified"}
    if wrf is None:
        result["epdc_input"] = "WRF proxy still required; do not use raw WBF"
        return result
    if len(wrf) > WRF_LIMIT:
        raise WaveformError("WRF exceeds K4 source's 2 MiB bound")
    proxy = layout(wrf)
    if wrf == wbf:
        raise WaveformError("WRF is identical to raw WBF; proxy not established")
    if wrf[:HEADER_SIZE] != wbf[:HEADER_SIZE]:
        raise WaveformError("WBF/WRF 48-byte headers differ; pairing not established")
    if proxy["temperature_bounds_raw"] != result["wbf"]["temperature_bounds_raw"]:
        raise WaveformError("WBF/WRF temperature tables differ; pairing not established")
    proxy.update({
        "bytes": len(wrf),
        "sha256": hashlib.sha256(wrf).hexdigest(),
        "matching_wbf_header_and_temperature_table": True,
        "epdc_loader_payload_offset": proxy["data_offset_after_header_and_temperature_table"],
        "epdc_loader_payload_size": proxy["data_size_after_header_and_temperature_table"],
        "payload_sha256": hashlib.sha256(wrf[proxy["data_offset_after_header_and_temperature_table"]:]).hexdigest(),
        "integrity": "WRF_payload_unverified_WBF_checksum_does_not_cover_it",
    })
    result["wrf"] = proxy
    result["epdc_input"] = "WRF structure inspected; waveform semantics and panel match unverified"
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wbf", required=True, type=Path)
    parser.add_argument("--wrf", type=Path, help="separate proxy; raw or gzip input")
    args = parser.parse_args()
    try:
        wbf = load_file(args.wbf, WBF_LIMIT)
        wrf = load_file(args.wrf, WRF_LIMIT) if args.wrf else None
        print(json.dumps(inspect_pair(wbf, wrf), indent=2))
    except (OSError, WaveformError) as exc:
        print(f"waveform inspection failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
