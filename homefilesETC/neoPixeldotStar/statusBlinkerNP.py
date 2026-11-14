#!/home/canopylife/PyEnvs/neopixel/bin/python3
# Copyright Eric Fortune, CanopyLife, April 2025
# Code written for MothPad device.  Updated November 2026.
"""
statusBlinkerNP.py - show device status by blinking an Adafruit NeoPixel LED.

This is the NeoPixel (WS2812, one data wire) version.  statusBlinkerDS.py is
the matching DotStar (APA102, data + clock wires) version.

How the LED is driven
---------------------
SPI is deliberately NOT used, because the SPI0 bus belongs to the Waveshare
High-Precision AD HAT.  A NeoPixel listens to every byte on its data wire and
has no chip-select, so sharing SPI would make it flicker and could corrupt
ADC commands.  Instead the Raspberry Pi 5's PIO hardware generates the
NeoPixel signal on an ordinary GPIO pin (package
Adafruit-Blinka-Raspberry-Pi5-Neopixel).  This needs no root access, only
membership of the `gpio` group.

The data pin is read from config.py (statusNeoPixel_gpio, default GPIO 26,
physical pin 37) and can be overridden with --pin.

Usage examples
--------------
    statusBlinkerNP.py working        # fast green blink, forever
    statusBlinkerNP.py error          # red double-blink, forever
    statusBlinkerNP.py 2              # old numeric codes still work (2 = working)
    statusBlinkerNP.py off            # make sure the LED is dark
    statusBlinkerNP.py test           # red, green, blue once each - check wiring
    statusBlinkerNP.py --list         # show every pattern and what it means
    statusBlinkerNP.py attention --brightness 0.3 --pixels 1

"Forever" patterns run until the process is stopped (Ctrl-C, `kill`, or a
parent program terminating it).  In every case the LED is switched off
cleanly before the script exits, so it is never left stuck "on".
"""

import argparse
import signal
import sys
import time
from dataclasses import dataclass

# Default data pin, used only if config.py cannot be found.
DEFAULT_PIN = 26

# ---------------------------------------------------------------------------
# Colours (24-bit 0xRRGGBB).  Half-intensity green/purple match the original
# script; they are bright enough to see and much easier on the eyes.
# ---------------------------------------------------------------------------
OFF = 0x000000
RED = 0xFF0000
GREEN = 0x008000
BLUE = 0x0000FF
PURPLE = 0x800080


@dataclass(frozen=True)
class Pattern:
    """One blink pattern.

    steps   -- sequence of (colour, seconds) pairs that is played in order.
               Each step sets *all* pixels to the colour and holds it.
    repeats -- how many times to play the sequence; None means forever.
    help    -- one-line description shown by --list.
    """
    steps: tuple
    repeats: int | None
    help: str


# ---------------------------------------------------------------------------
# Pattern table.  Adding a new pattern is just a matter of adding an entry
# here - no new function or if/elif branch is needed.
# ---------------------------------------------------------------------------
PATTERNS = {
    "error-fast": Pattern(
        steps=((RED, 0.05), (OFF, 0.05)),
        repeats=None,
        help="fast red blinking (10 Hz)",
    ),
    "working": Pattern(
        steps=((GREEN, 0.05), (OFF, 0.05)),
        repeats=None,
        help="fast green blinking - machine is working",
    ),
    "error": Pattern(
        steps=((RED, 0.2), (OFF, 0.1), (RED, 0.2), (OFF, 1.6)),
        repeats=None,
        help="red double-blink every 2.1 s - definitely an error",
    ),
    "ok": Pattern(
        steps=((GREEN, 1.0), (OFF, 1.0)),
        repeats=4,
        help="four long green blinks, then stop - all is OK",
    ),
    "reset": Pattern(
        steps=((RED, 1.0), (OFF, 1.0)),
        repeats=4,
        help="four long red blinks, then stop - please reset",
    ),
    "off": Pattern(
        steps=((OFF, 0.0),),
        repeats=1,
        help="turn the LED off",
    ),
    "attention": Pattern(
        steps=((PURPLE, 0.02), (OFF, 1.0)),
        repeats=None,
        help="brief purple flash every second - user should intervene",
    ),
    "test": Pattern(
        steps=((RED, 1.0), (GREEN, 1.0), (BLUE, 1.0), (OFF, 0.0)),
        repeats=1,
        help="red, green, blue for 1 s each - check wiring and colour order",
    ),
}

# The original script took the numbers 1-6.  Keep them so that any existing
# programs or shell scripts that call `statusBlinker.py <n>` keep working
# exactly as before.  Code 7 is new: the purple pattern existed in the old
# file but could never be selected.
NUMERIC_CODES = {
    "1": "error-fast",
    "2": "working",
    "3": "error",
    "4": "ok",
    "5": "reset",
    "6": "off",
    "7": "attention",
}


def config_pin(name: str, fallback: int) -> int:
    """Read a GPIO number from the MothPad config.py, if it is available.

    config.py normally sits in the same directory as this script, which
    Python searches first.  If it is missing (e.g. testing elsewhere) or
    does not define the setting, the fallback is used instead.
    """
    try:
        import config
    except ImportError:
        return fallback
    return getattr(config, name, fallback)


def list_patterns() -> str:
    """Return a human-readable table of every pattern and its numeric code."""
    code_for = {name: code for code, name in NUMERIC_CODES.items()}
    lines = ["Available patterns (name / legacy number):"]
    for name, pattern in PATTERNS.items():
        lines.append(f"  {name:<11} {code_for.get(name, '-'):>2}   {pattern.help}")
    return "\n".join(lines)


def resolve_pattern(choice: str) -> str:
    """Turn a user's choice (name or legacy number) into a pattern name.

    Used as an argparse `type=` so bad input produces a tidy error message.
    """
    name = NUMERIC_CODES.get(choice, choice.lower())
    if name not in PATTERNS:
        raise argparse.ArgumentTypeError(
            f"unknown pattern {choice!r}\n{list_patterns()}"
        )
    return name


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Blink a NeoPixel status LED (Pi 5 PIO, no SPI).",
        epilog=list_patterns(),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "pattern",
        nargs="?",
        type=resolve_pattern,
        help="pattern name or legacy number 1-7 (see list below)",
    )
    parser.add_argument(
        "-p", "--pin", type=int,
        default=config_pin("statusNeoPixel_gpio", DEFAULT_PIN),
        help="GPIO (BCM) number of the NeoPixel data line "
             "(default: statusNeoPixel_gpio in config.py, else %(default)s)",
    )
    parser.add_argument(
        "-n", "--pixels", type=int, default=10,
        help="number of NeoPixels on the strip (default: 10)",
    )
    parser.add_argument(
        "-b", "--brightness", type=float, default=1.0,
        help="overall brightness from 0.0 to 1.0 (default: 1.0)",
    )
    parser.add_argument(
        "-l", "--list", action="store_true",
        help="list the available patterns and exit",
    )
    args = parser.parse_args(argv)

    if args.list:
        print(list_patterns())
        sys.exit(0)
    if args.pattern is None:
        parser.error("a pattern is required (try --list)")
    if not 0.0 <= args.brightness <= 1.0:
        parser.error("--brightness must be between 0.0 and 1.0")
    if args.pixels < 1:
        parser.error("--pixels must be at least 1")
    return args


def open_pixels(pin: int, count: int, brightness: float):
    """Create the NeoPixel object on the given GPIO pin.

    The hardware libraries are imported here, not at the top of the file,
    so that `--help` and `--list` work even on a machine without the LED.

    On a Pi 5, Blinka automatically sends the data through the PIO block
    when Adafruit-Blinka-Raspberry-Pi5-Neopixel is installed.

    auto_write=False means changing colours does *not* immediately send data
    to the LEDs; we call show() once per step instead.  This avoids redundant
    transfers and makes every colour change a single, atomic update.
    """
    import board
    import neopixel

    try:
        gpio = getattr(board, f"D{pin}")
    except AttributeError:
        sys.exit(f"statusBlinkerNP: GPIO {pin} is not a valid pin on this board")

    return neopixel.NeoPixel(
        gpio, count, brightness=brightness, auto_write=False
    )


def set_colour(pixels, colour: int) -> None:
    """Set every pixel to `colour` and push it to the LEDs in one transfer."""
    pixels.fill(colour)
    pixels.show()


def run_pattern(pixels, pattern: Pattern) -> None:
    """Play a pattern, keeping accurate timing.

    Rather than calling sleep(duration) after each step (which slowly drifts
    because writing to the LED itself takes time), we keep a running
    "deadline" based on time.monotonic() and sleep only for whatever time
    remains.  The blink rhythm therefore stays steady however long it runs.
    """
    deadline = time.monotonic()
    plays = 0
    while pattern.repeats is None or plays < pattern.repeats:
        for colour, duration in pattern.steps:
            set_colour(pixels, colour)
            deadline += duration
            remaining = deadline - time.monotonic()
            if remaining > 0:
                time.sleep(remaining)
        plays += 1


def main(argv=None) -> int:
    args = parse_args(argv)
    pattern = PATTERNS[args.pattern]

    pixels = open_pixels(args.pin, args.pixels, args.brightness)

    # Convert "polite" termination requests (kill, closing the terminal) into
    # the same KeyboardInterrupt that Ctrl-C raises, so a single `finally`
    # block below handles every way the script can be stopped.
    def _stop(signum, frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGHUP, _stop)

    try:
        run_pattern(pixels, pattern)
    except KeyboardInterrupt:
        pass  # normal way to end a "forever" pattern
    finally:
        # Always leave the LED dark.  "Off" is sent twice because the very
        # first transfer after start-up is occasionally mis-read by the LED;
        # the original script did the same thing for the same reason.
        set_colour(pixels, OFF)
        time.sleep(0.01)
        set_colour(pixels, OFF)
        pixels.deinit()  # release the GPIO pin
    return 0


if __name__ == "__main__":
    sys.exit(main())
