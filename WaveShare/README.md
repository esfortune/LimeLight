# adSample — Waveshare High-Precision AD HAT (ADS1263) recorder

## Build

```
make
sudo setcap cap_sys_nice,cap_ipc_lock+ep adSample   # real-time priority; repeat after every rebuild
```

SPI must be enabled (`dtparam=spi=on` in `/boot/firmware/config.txt`) and the user must be in the `spi` and `gpio` groups.

## Record

```
./adSample <channels> <rate> <seconds>
./adSample 1 19200 60
./adSample -o test.ads -i 2,3 -r int 2 1200 10
```

| channels | rate (Hz)                              | seconds    |
|----------|----------------------------------------|------------|
| 1        | 1200, 2400, 4800, 7200, 14400, 19200   | 0.1 – 60   |
| 2        | 1200                                   | 0.1 – 60   |

The rates are the ADS1263's native data rates, so no resampling is done.

Options:

- `-o FILE`: output file. The default is `adSample_YYYYmmdd_HHMMSS.ads`.
- `-i P[,P]`: AIN input for each channel. The default is `0,1`. Each input is measured against AINCOM, so connect AINCOM to your signal ground.
- `-r avdd|int`: voltage reference.
  - `avdd` is the default. Full scale is ±5 V, as in the Waveshare demo.
  - `int` uses the internal 2.5 V reference. Full scale is ±2.5 V, with better accuracy and lower noise.
- `-f 1-4`: order of the sinc filter, 1 channel only. The default is 1, which gives the widest bandwidth (−3 dB at about 0.44 × rate). Higher orders reject aliasing better, but roll off sooner.

Exit status:

- 0: success.
- 1: error. No file was written.
- 3: a file was written, but some samples were repaired or mistimed. The details are printed and stored in the header.

## Convert to WAV

```
./adsample2wav.py rec.ads                # 32-bit PCM, lossless (full scale = ±vref)
./adsample2wav.py --bits 16 rec.ads      # 16- or 24-bit PCM
./adsample2wav.py --float rec.ads        # 32-bit float, in volts
./adsample2wav.py --info rec.ads         # print header
```

## How it works and its limits

- **1 channel.** The ADC runs on its own clock and every conversion is read.
  - The kernel timestamps each DRDY edge. From those timestamps the program rebuilds the ADC's conversion grid, so a conversion that was missed is detected and located exactly.
  - Missed conversions are filled by linear interpolation and counted.
  - The ADC clock is measured against the Pi clock and stored in the header; it is typically about 60 ppm fast.
- **2 channels.** The ADS1263 has a single ADC behind a multiplexer.
  - After each channel switch it needs about 230 µs to settle, so 2-channel capture tops out around 2100 pairs/s. 1200 Hz is the only native rate that fits.
  - The Pi clock paces each frame. Channel 1 converts at the tick, then channel 2 about 0.23 ms later; the channels are **not** sampled simultaneously.
  - Each conversion is a 26 µs sinc1 average at 38400 SPS.
  - Frames that start more than 20 µs late are counted.
- **38400 SPS cannot be used.** Each spidev transfer on the Pi 5 takes about 25 µs, which is the whole 26 µs conversion period.
- **Anti-aliasing.** The ADC's sinc filter gives only weak anti-aliasing, so band-limit your signal in the analog domain to below rate/2.

## File format (.ads)

The file starts with a 64-byte little-endian header, followed by interleaved `int32` samples. Volts = sample / 2³¹ × vref.

| offset | type    | field                                   |
|--------|---------|-----------------------------------------|
| 0      | char[4] | magic `ADS1`                            |
| 4      | u16     | version (1)                             |
| 6      | u16     | header bytes (64)                       |
| 8      | u16     | channels                                |
| 10     | u16     | sample format (1 = int32)               |
| 12     | u32     | sample rate (Hz, nominal)               |
| 16     | u64     | frames                                  |
| 24     | f64     | measured ADC rate (Hz; 0 for 2 ch)      |
| 32     | f64     | vref (V)                                |
| 40     | i64     | start time (Unix ns)                    |
| 48     | u32     | repaired (interpolated) samples         |
| 52     | u32     | timing errors (2 ch)                    |
| 56     | u8[2]   | AIN input per channel (255 = unused)    |
| 58     | u8      | reference (0 internal, 1 AVDD)          |
| 59     | u8      | sinc filter order                       |
| 60     | u32     | reserved                                |

Read the file in Python:

```python
h = np.fromfile(f, np.uint8, 64)
x = np.fromfile(f, '<i4', offset=64).reshape(-1, channels)
```
