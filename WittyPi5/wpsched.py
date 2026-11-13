#!/usr/bin/env python3
"""
wpsched - simple flat-file on/off scheduler and logger for the UUGear Witty Pi 5.

Commands
  wpsched apply    read ~/wittypi_schedule.txt, sync the RTC, arm the next
                   shutdown/startup alarms and set the voltage protection
  wpsched plan     show what 'apply' would do, without touching the hardware
  wpsched status   show live readings, board settings and armed alarms
  wpsched log [EVENT]  append one line of readings to ~/wittypi_log.csv

Witty Pi 5 has one startup alarm and one shutdown alarm, so this program
always arms just the next pair of events.  It runs at every boot (the start
of each ON window), so the alarms are re-armed for the following window.

Register map and encodings come from UUGear's Witty-Pi-5-Software
(wp5lib.h / wp5lib.c, BSD-3-Clause).  The I2C lock file is shared with wp5d.
"""

import argparse
import csv
import datetime as dt
import fcntl
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

from smbus2 import SMBus

HOME = Path(os.environ.get("WPSCHED_HOME", Path.home()))
SCHEDULE_FILE = HOME / "wittypi_schedule.txt"
DATA_LOG = HOME / "wittypi_log.csv"
EVENT_LOG = HOME / "wittypi_events.log"

I2C_BUS = 1
ADDR = 0x51
I2C_LOCK = "/var/lock/wittypi5_i2c.lock"

# --- Registers (wp5lib.h) ----------------------------------------------------
FW_ID, FW_MAJOR, FW_MINOR = 0x00, 0x01, 0x02
VUSB_MV, VIN_MV, VOUT_MV, IOUT_MA = 0x03, 0x05, 0x07, 0x09   # MSB; LSB = +1
POWER_MODE = 0x0B          # 0 = via Vusb, 1 = via Vin
ACTION_REASON = 0x0E       # high nibble = startup reason, low = shutdown reason
CONF_DEFAULT_ON_DELAY = 0x11
CONF_POWER_CUT_DELAY = 0x12
CONF_LOW_VOLTAGE = 0x16    # volts x10, 0 = disabled
CONF_RECOVERY_VOLTAGE = 0x17
ALARM1 = 0x20              # startup:  sec, min, hour, day (BCD)
ALARM2 = 0x24              # shutdown: sec, min, hour, day (BCD)
RTC_SEC = 0x50             # sec, min, hour, weekday(bit), day, month, year (BCD)
TEMP_MSB = 0x60

REASONS = ["unknown", "scheduled startup", "scheduled shutdown", "button",
           "Vin below low-voltage", "Vin above recovery-voltage",
           "over temperature", "below temperature", "power newly connected",
           "reboot", "missed heartbeat", "shutdown externally",
           "reboot externally"]

MERGE_GAP_MIN = 3          # windows closer than this are merged


def bcd(n):
    return ((n // 10) << 4) | (n % 10)


def unbcd(b):
    return (b >> 4) * 10 + (b & 0x0F)


def reason_name(code):
    return REASONS[code] if 0 <= code < len(REASONS) else f"code {code}"


def event(msg):
    line = f"{dt.datetime.now():%Y-%m-%d %H:%M:%S}  {msg}"
    print(line)
    try:
        with open(EVENT_LOG, "a") as f:
            f.write(line + "\n")
    except OSError:
        pass


# --- I2C access -------------------------------------------------------------
class WittyPi:
    """Every transaction holds the same flock as UUGear's wp5d/wp5 tools."""

    def __enter__(self):
        old = os.umask(0)
        try:
            self.lock_fd = os.open(I2C_LOCK, os.O_CREAT | os.O_RDWR, 0o666)
        finally:
            os.umask(old)
        fcntl.flock(self.lock_fd, fcntl.LOCK_EX)
        self.bus = SMBus(I2C_BUS)
        return self

    def __exit__(self, *exc):
        self.bus.close()
        fcntl.flock(self.lock_fd, fcntl.LOCK_UN)
        os.close(self.lock_fd)

    def get(self, reg):
        """Read until two consecutive reads agree (as wp5lib does)."""
        last = None
        for _ in range(6):
            try:
                v = self.bus.read_byte_data(ADDR, reg)
            except OSError:
                time.sleep(0.02)
                continue
            if v == last:
                return v
            last = v
            time.sleep(0.002)
        raise IOError(f"I2C read of register 0x{reg:02X} failed")

    def set(self, reg, value):
        for _ in range(4):
            try:
                self.bus.write_byte_data(ADDR, reg, value)
                time.sleep(0.005)
                if self.get(reg) == value:
                    return
            except OSError:
                time.sleep(0.02)
        raise IOError(f"I2C write of register 0x{reg:02X} failed")

    def raw_set(self, reg, value):
        self.bus.write_byte_data(ADDR, reg, value)

    def get_live(self, reg):
        """Single read for live measurements, which legitimately change between
        reads (wp5lib also reads these without validation)."""
        for _ in range(4):
            try:
                return self.bus.read_byte_data(ADDR, reg)
            except OSError:
                time.sleep(0.02)
        raise IOError(f"I2C read of register 0x{reg:02X} failed")

    def milli(self, msb_reg):
        msb, lsb = self.get_live(msb_reg) & 0x7F, self.get_live(msb_reg + 1)
        return ((msb << 8) | lsb) / 1000.0

    def temperature(self):
        msb, lsb = self.get_live(TEMP_MSB), self.get_live(TEMP_MSB + 1)
        raw = (msb << 4) | (lsb >> 4)
        if raw & 0x800:
            raw -= 0x1000
        return raw * 0.0625

    def read_alarm(self, base):
        s, m, h, d = (unbcd(self.get(base + i)) for i in range(4))
        return None if d == 0 else (d, h, m, s)

    def write_alarm(self, base, when):
        vals = [0, 0, 0, 0] if when is None else \
            [bcd(when.second), bcd(when.minute), bcd(when.hour), bcd(when.day)]
        for i, v in enumerate(vals):
            self.set(base + i, v)

    def rtc_time(self):
        r = [self.get(RTC_SEC + i) for i in range(7)]
        try:
            return dt.datetime(2000 + unbcd(r[6]), unbcd(r[5]), unbcd(r[4]),
                               unbcd(r[2]), unbcd(r[1]), unbcd(r[0]))
        except ValueError:
            return None

    def write_rtc(self, t):
        wday = (t.weekday() + 1) % 7                       # 0 = Sunday
        vals = [bcd(t.second), bcd(t.minute), bcd(t.hour), 1 << wday,
                bcd(t.day), bcd(t.month), bcd(t.year - 2000)]
        for i, v in enumerate(vals):
            self.set(RTC_SEC + i, v)


# --- Schedule file ----------------------------------------------------------
class Config:
    def __init__(self):
        self.windows = []                  # [(start_min, end_min)], minutes of day
        self.low_voltage = 0.0
        self.recovery_voltage = 0.0
        self.default_on_delay = 255


def parse_schedule(path):
    cfg = Config()
    hhmm = r"([01]?\d|2[0-3]):([0-5]\d)"
    for n, raw in enumerate(path.read_text().splitlines(), 1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        key, _, val = line.partition(" ")
        key, val = key.upper(), val.strip()
        try:
            if key == "ON":
                m = re.fullmatch(hhmm + r"\s*-\s*" + hhmm, val)
                if not m:
                    raise ValueError("expected HH:MM-HH:MM")
                a = int(m[1]) * 60 + int(m[2])
                b = int(m[3]) * 60 + int(m[4])
                if a == b:
                    raise ValueError("start and end are equal")
                cfg.windows.append((a, b))
            elif key == "LOW_VOLTAGE":
                cfg.low_voltage = float(val)
            elif key == "RECOVERY_VOLTAGE":
                cfg.recovery_voltage = float(val)
            elif key == "DEFAULT_ON_DELAY":
                cfg.default_on_delay = int(val)
            else:
                raise ValueError(f"unknown keyword '{key}'")
        except ValueError as e:
            raise SystemExit(f"{path}:{n}: {e}: {raw.strip()}")
    for v in (cfg.low_voltage, cfg.recovery_voltage):
        if not 0 <= v <= 25.5:
            raise SystemExit(f"{path}: voltages must be 0-25.5 V")
    if cfg.low_voltage and cfg.recovery_voltage and \
            cfg.recovery_voltage <= cfg.low_voltage + 0.3:
        raise SystemExit(f"{path}: RECOVERY_VOLTAGE must be at least 0.3 V above LOW_VOLTAGE")
    if not 0 <= cfg.default_on_delay <= 255:
        raise SystemExit(f"{path}: DEFAULT_ON_DELAY must be 0-255")
    return cfg


def intervals(cfg, now):
    """Concrete ON intervals (datetimes) from yesterday to 3 days ahead, merged."""
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    iv = []
    for day in range(-1, 4):
        base = midnight + dt.timedelta(days=day)
        for a, b in cfg.windows:
            s = base + dt.timedelta(minutes=a)
            e = base + dt.timedelta(minutes=b if b > a else b + 1440)
            iv.append([s, e])
    iv.sort()
    merged = []
    for s, e in iv:
        if merged and s - merged[-1][1] < dt.timedelta(minutes=MERGE_GAP_MIN):
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])
    return merged


def next_events(cfg, now):
    """Return (inside_window, shutdown_at, startup_at)."""
    for s, e in intervals(cfg, now):
        if s <= now < e:                               # on now: off at e, on at next start
            later = [x for x in intervals(cfg, e) if x[0] >= e]
            return True, e, later[0][0]
        if s > now:                                    # off-window: wake at s, off at e
            return False, e, s
    raise RuntimeError("no upcoming window found")


def describe_windows(cfg):
    return ", ".join(f"{a//60:02d}:{a%60:02d}-{b//60:02d}:{b%60:02d}" for a, b in cfg.windows)


# --- Commands ---------------------------------------------------------------
def ntp_synced():
    try:
        out = subprocess.run(["timedatectl", "show", "-p", "NTPSynchronized", "--value"],
                             capture_output=True, text=True, timeout=10).stdout.strip()
        return out == "yes"
    except (OSError, subprocess.SubprocessError):
        return False


def show_plan(cfg, now):
    """Print the plan for reference time `now`; return (shutdown_at, startup_at)."""
    print(f"Schedule file : {SCHEDULE_FILE}")
    print(f"ON windows    : {describe_windows(cfg) or 'none (scheduling disabled)'}")
    volts = lambda v: f"{v} V" if v else "disabled"
    print(f"Low voltage   : {volts(cfg.low_voltage)}   recovery: "
          f"{volts(cfg.recovery_voltage)}   default-on delay: {cfg.default_on_delay} s")
    if not cfg.windows:
        return None, None
    inside, off_at, on_at = next_events(cfg, now)
    print(f"Now           : {now}  ({'inside' if inside else 'outside'} an ON window)")
    print(f"Next shutdown : {off_at}")
    print(f"Next startup  : {on_at}")
    if not inside:
        print("  (Pi is running outside an ON window; it stays on until the "
              "end of the next window, or until you shut it down.)")
    return off_at, on_at


def cmd_plan(args):
    show_plan(parse_schedule(SCHEDULE_FILE), dt.datetime.now().replace(microsecond=0))


def cmd_apply(args):
    cfg = parse_schedule(SCHEDULE_FILE)
    with WittyPi() as wp:
        if wp.get(FW_ID) != 0x51:
            raise SystemExit("Witty Pi 5 not found at I2C 0x51")

        # Pick a trustworthy clock.  Without network the Witty Pi RTC
        # (battery backed) is the reference, not the possibly unset system clock.
        sys_now = dt.datetime.now().replace(microsecond=0)
        rtc = wp.rtc_time()
        rtc_ok = rtc is not None and rtc.year >= 2025
        if ntp_synced():
            now, rtc_note = sys_now, "RTC set from NTP-synced system clock"
            wp.write_rtc(dt.datetime.now())
        elif rtc_ok:
            now = rtc
            rtc_note = (f"no NTP, using Witty Pi RTC (system clock differs by "
                        f"{abs((rtc - sys_now).total_seconds()):.0f} s)")
        elif sys_now.year >= 2025:
            now, rtc_note = sys_now, "WARNING: no NTP and RTC invalid; RTC set from system clock"
            wp.write_rtc(dt.datetime.now())
        else:
            raise SystemExit("Neither system clock nor RTC is set; refusing to arm alarms.")

        off_at, on_at = show_plan(cfg, now)

        def alarm_bytes(t):
            return [0, 0, 0, 0] if t is None else \
                [bcd(t.second), bcd(t.minute), bcd(t.hour), bcd(t.day)]

        want = {CONF_LOW_VOLTAGE: round(cfg.low_voltage * 10),
                CONF_RECOVERY_VOLTAGE: round(cfg.recovery_voltage * 10),
                CONF_DEFAULT_ON_DELAY: cfg.default_on_delay}
        want.update({ALARM1 + i: v for i, v in enumerate(alarm_bytes(on_at))})
        want.update({ALARM2 + i: v for i, v in enumerate(alarm_bytes(off_at))})

        # The firmware saves changed settings to its flash by itself once
        # the I2C bus is quiet; re-read afterwards and repair anything that
        # did not stick.
        changed = [r for r, v in want.items() if wp.get(r) != v]
        repaired = 0
        for r in changed:
            wp.set(r, want[r])
    for attempt in range(4):
        time.sleep(3)
        with WittyPi() as wp:
            bad = [r for r, v in want.items() if wp.get(r) != v]
            if not bad:
                break
            repaired += len(bad)
            for r in bad:
                wp.set(r, want[r])
    else:
        raise SystemExit("Witty Pi did not keep settings in registers "
                         + ", ".join(f"0x{r:02X}" for r in bad))

    msg = (f"applied: windows [{describe_windows(cfg) or 'none'}], "
           f"next shutdown {off_at or '-'}, next startup {on_at or '-'}, "
           f"low {cfg.low_voltage} V, recovery {cfg.recovery_voltage} V; {rtc_note}")
    if changed:
        msg += f"; {len(changed)} register(s) updated"
    if repaired:
        msg += f"; {repaired} register(s) had to be re-written after settling"
    event(msg)


def cmd_status(args):
    with WittyPi() as wp:
        fw = f"{wp.get(FW_MAJOR)}.{wp.get(FW_MINOR)}"
        vin, vusb, vout, iout = (wp.milli(r) for r in (VIN_MV, VUSB_MV, VOUT_MV, IOUT_MA))
        mode = "Vin" if wp.get(POWER_MODE) else "USB-C"
        temp = wp.temperature()
        reason = wp.get(ACTION_REASON)
        low, rec = wp.get(CONF_LOW_VOLTAGE) / 10, wp.get(CONF_RECOVERY_VOLTAGE) / 10
        dod, pcd = wp.get(CONF_DEFAULT_ON_DELAY), wp.get(CONF_POWER_CUT_DELAY)
        rtc = wp.rtc_time()
        a1, a2 = wp.read_alarm(ALARM1), wp.read_alarm(ALARM2)

    def fmt(a):
        return "not set" if a is None else f"day {a[0]:02d} {a[1]:02d}:{a[2]:02d}:{a[3]:02d}"

    print(f"Witty Pi 5 firmware {fw}, powered via {mode}")
    print(f"  Vin  {vin:6.3f} V    Vusb {vusb:6.3f} V")
    print(f"  Vout {vout:6.3f} V    Iout {iout:6.3f} A   ({vout*iout:.2f} W)")
    print(f"  Board temperature {temp:.1f} C    CPU {cpu_temp():.1f} C")
    print(f"  Last startup reason : {reason_name(reason >> 4)}")
    print(f"  Last shutdown reason: {reason_name(reason & 0x0F)}")
    print(f"  Low-voltage cutoff  : {f'{low} V' if low else 'disabled'}   "
          f"recovery: {f'{rec} V' if rec else 'disabled'}")
    print(f"  Default-on delay {dod} s   power-cut delay {pcd} s")
    print(f"  RTC {rtc}   system {dt.datetime.now():%Y-%m-%d %H:%M:%S}")
    print(f"  Startup alarm : {fmt(a1)}")
    print(f"  Shutdown alarm: {fmt(a2)}")


def cpu_temp():
    try:
        return int(Path("/sys/class/thermal/thermal_zone0/temp").read_text()) / 1000
    except (OSError, ValueError):
        return float("nan")


def vcgencmd(*args):
    try:
        return subprocess.run(["vcgencmd", *args], capture_output=True,
                              text=True, timeout=5).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


LOG_FIELDS = ["timestamp", "event", "vin_V", "vusb_V", "vout_V", "iout_A", "power_W",
              "source", "board_temp_C", "cpu_temp_C", "pi_5v_V", "throttled",
              "uptime_h", "load_1m", "disk_free_GB", "startup_reason",
              "low_cutoff_V", "next_startup", "next_shutdown"]


def cmd_log(args):
    row = {"timestamp": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
           "event": args.event}
    try:
        with WittyPi() as wp:
            vin, vusb, vout, iout = (wp.milli(r) for r in (VIN_MV, VUSB_MV, VOUT_MV, IOUT_MA))
            a1, a2 = wp.read_alarm(ALARM1), wp.read_alarm(ALARM2)
            row.update(vin_V=f"{vin:.3f}", vusb_V=f"{vusb:.3f}", vout_V=f"{vout:.3f}",
                       iout_A=f"{iout:.3f}", power_W=f"{vout*iout:.2f}",
                       source="Vin" if wp.get(POWER_MODE) else "USB",
                       board_temp_C=f"{wp.temperature():.2f}",
                       startup_reason=reason_name(wp.get(ACTION_REASON) >> 4),
                       low_cutoff_V=wp.get(CONF_LOW_VOLTAGE) / 10,
                       next_startup="" if a1 is None else f"d{a1[0]:02d} {a1[1]:02d}:{a1[2]:02d}",
                       next_shutdown="" if a2 is None else f"d{a2[0]:02d} {a2[1]:02d}:{a2[2]:02d}")
    except Exception as e:                       # still log the Pi side
        row["source"] = f"ERROR: {e}"
    m = re.search(r"=([\d.]+)V", vcgencmd("pmic_read_adc", "EXT5V_V"))
    row["pi_5v_V"] = f"{float(m[1]):.3f}" if m else ""
    row["throttled"] = vcgencmd("get_throttled").partition("=")[2]
    row["cpu_temp_C"] = f"{cpu_temp():.1f}"
    row["uptime_h"] = f"{float(Path('/proc/uptime').read_text().split()[0]) / 3600:.2f}"
    row["load_1m"] = f"{os.getloadavg()[0]:.2f}"
    row["disk_free_GB"] = f"{shutil.disk_usage('/').free / 1e9:.1f}"

    new = not DATA_LOG.exists() or DATA_LOG.stat().st_size == 0
    with open(DATA_LOG, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=LOG_FIELDS)
        if new:
            w.writeheader()
        w.writerow(row)
    if not args.quiet:
        print(", ".join(f"{k}={row.get(k, '')}" for k in LOG_FIELDS))


def main():
    p = argparse.ArgumentParser(prog="wpsched", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("apply", help="read the schedule file and arm the Witty Pi")
    sub.add_parser("plan", help="show what apply would do (no hardware changes)")
    sub.add_parser("status", help="show live readings and armed alarms")
    lp = sub.add_parser("log", help="append one row to the CSV log")
    lp.add_argument("event", nargs="?", default="manual")
    lp.add_argument("-q", "--quiet", action="store_true")
    args = p.parse_args()

    if args.cmd == "apply":
        try:
            cmd_apply(args)
        except SystemExit as e:
            if e.code not in (0, None):
                event(f"apply FAILED: {e.code}")
            raise
        except Exception as e:
            event(f"apply FAILED: {e}")
            raise SystemExit(1)
    elif args.cmd == "plan":
        cmd_plan(args)
    elif args.cmd == "status":
        cmd_status(args)
    else:
        cmd_log(args)


if __name__ == "__main__":
    main()
