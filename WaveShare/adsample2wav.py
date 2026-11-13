#!/usr/bin/env python3
"""Convert an adSample recording (.ads) to a WAV file.

usage: adsample2wav.py [--bits 16|24|32] [--float] [--info] input.ads [output.wav]

  default   32-bit integer PCM, ADC codes unchanged (lossless):
            WAV full scale (+/-1.0) = +/-vref (5 V with the default AVDD ref).
  --bits N  16- or 24-bit PCM (rounded from the 32-bit codes).
  --float   32-bit float WAV holding volts.
  --info    print the header and exit.

.ads format: 64-byte little-endian header, then interleaved int32 samples.
volts = sample / 2**31 * vref.
"""
import argparse
import os
import struct
import sys

import numpy as np

HDR = struct.Struct("<4sHHHHIQddqII2BBBI")
assert HDR.size == 64
FIELDS = ("magic version header_bytes channels sample_format sample_rate frames "
          "measured_rate vref start_unix_ns repaired timing_errors in0 in1 ref filter reserved").split()


def read_ads(path):
    with open(path, "rb") as f:
        raw = f.read(HDR.size)
        if len(raw) != HDR.size:
            raise ValueError("file too short for header")
        h = dict(zip(FIELDS, HDR.unpack(raw)))
        if h["magic"] != b"ADS1" or h["version"] != 1 or h["sample_format"] != 1:
            raise ValueError("not an adSample v1 file")
        f.seek(h["header_bytes"])
        data = np.fromfile(f, dtype="<i4")
    ch, frames = h["channels"], h["frames"]
    if ch not in (1, 2) or data.size != frames * ch:
        raise ValueError(f"file truncated or corrupt: expected {frames * ch} samples, found {data.size}")
    return h, data.reshape(frames, ch)


def write_wav(path, samples, rate, fmt_tag, bits):
    ch = samples.shape[1]
    payload = samples.tobytes()
    block = ch * bits // 8
    fmt = struct.pack("<HHIIHH", fmt_tag, ch, rate, rate * block, block, bits)
    chunks = b"fmt " + struct.pack("<I", len(fmt)) + fmt
    if fmt_tag == 3:  # float needs a fact chunk
        chunks += b"fact" + struct.pack("<II", 4, samples.shape[0])
    chunks += b"data" + struct.pack("<I", len(payload))
    pad = b"\0" if len(payload) % 2 else b""
    tmp = path + ".part"
    with open(tmp, "wb") as f:
        f.write(b"RIFF" + struct.pack("<I", 4 + len(chunks) + len(payload) + len(pad)) + b"WAVE")
        f.write(chunks)
        f.write(payload)
        f.write(pad)
    os.replace(tmp, path)


def main():
    ap = argparse.ArgumentParser(description="Convert adSample .ads recordings to WAV")
    ap.add_argument("input")
    ap.add_argument("output", nargs="?")
    ap.add_argument("--bits", type=int, choices=(16, 24, 32), default=32)
    ap.add_argument("--float", action="store_true", help="32-bit float WAV in volts")
    ap.add_argument("--info", action="store_true")
    a = ap.parse_args()

    try:
        h, x = read_ads(a.input)
    except (OSError, ValueError) as e:
        sys.exit(f"error: {a.input}: {e}")

    if a.info:
        for k in FIELDS:
            if k not in ("magic", "reserved"):
                print(f"{k:14s} {h[k]}")
        return
    if h["repaired"] or h["timing_errors"]:
        print(f"note: recording has {h['repaired']} repaired sample(s), "
              f"{h['timing_errors']} timing error(s)", file=sys.stderr)

    out = a.output or os.path.splitext(a.input)[0] + ".wav"
    rate = h["sample_rate"]
    if a.float:
        write_wav(out, (x / 2.0**31 * h["vref"]).astype("<f4"), rate, 3, 32)
    elif a.bits == 32:
        write_wav(out, x.astype("<i4"), rate, 1, 32)
    else:
        shift = 32 - a.bits
        y = np.clip((x.astype(np.int64) + (1 << (shift - 1))) >> shift,
                    -(1 << (a.bits - 1)), (1 << (a.bits - 1)) - 1)
        if a.bits == 16:
            write_wav(out, y.astype("<i2"), rate, 1, 16)
        else:  # 24-bit: pack the low 3 bytes of each little-endian int32
            b = y.astype("<i4").view(np.uint8).reshape(y.shape + (4,))[..., :3]
            write_wav_24(out, b, rate)
    print(f"{out}: {h['frames']} frames, {h['channels']} ch, {rate} Hz")


def write_wav_24(path, b, rate):
    class _Raw:  # adapter so write_wav can take pre-packed 24-bit bytes
        def __init__(self, b):
            self.b, self.shape = b, b.shape[:2]

        def tobytes(self):
            return np.ascontiguousarray(self.b).tobytes()

    write_wav(path, _Raw(b), rate, 1, 24)


if __name__ == "__main__":
    main()
