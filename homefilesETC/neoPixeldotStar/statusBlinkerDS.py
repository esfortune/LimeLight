#!/home/canopylife/PyEnvs/neopixel/bin/python3
# Copyright Eric Fortune, CanopyLife, March 2026
# Code written for MothPad device.  Updated November 2026.
"""
statusBlinkerDS.py - show device status by blinking an Adafruit DotStar LED.

This is the DotStar (APA102 / "DotStar 5050", data + clock wires) version.
statusBlinkerNP.py is the matching NeoPixel version.  Both have the same
options; the patterns and numeric codes differ to match each device's
original script.

How the LED is driven
---------------------
SPI is deliberately NOT used, because the SPI0 bus belongs to the Waveshare
High-Precision AD HAT.  Unlike a NeoPixel, a DotStar has a separate clock
line and no strict timing requirements, so the library simply toggles two
ordinary GPIO pins in software ("bit-banging").  For a single LED an update
takes about half a millisecond, which is far quicker than any blink step.

The pins are read from config.py (statusDotStarData_gpio, default GPIO 26 /
physical pin 37, and statusDotStarClock_gpio, default GPIO 5 / physical
pin 29) and can be overridden with --data-pin and --clock-pin.

Colour order
------------
The DotStar 5050 LED used on MothPad expects its colour bytes in the order
red, blue, green.  The old script sent them as red, green, blue and made
up for it with confusing colour values (e.g. 0xFFFF00 for "purple").  This
version tells the library the correct order (RBG), so the colour constants
below are the true colours - and the bytes sent to the LED are identical to
before.  If colours ever look wrong on new hardware, run the `test` pattern
(red, green, blue) and adjust --order.

Usage examples
--------------
    statusBlinkerDS.py working        # green blink, forever
    statusBlinkerDS.py attention      # slow purple flash, forever
    statusBlinkerDS.py 2              # old numeric codes still work (2 = working)
    statusBlinkerDS.py off            # make sure the LED is dark
    statusBlinkerDS.py test           # red, green, blue once each - check wiring
    statusBlinkerDS.py --list         # show every pattern and what it means
    statusBlinkerDS.py ok --brightness 0.3

"Forever" patterns run until the process is stopped (Ctrl-C, `kill`, or a
parent program terminating it).  In every case the LED is switched off
cleanly before the script exits, so it is never left stuck "on".
"""

import argparse
import signal
import sys
import time
from dataclasses import dataclass

# Default pins, used only if config.py cannot be found.
DEFAULT_DATA_PIN = 26
DEFAULT_CLOCK_PIN = 5

# Byte order the LED expects (see "Colour order" above).
DEFAULT_ORDER = "RBG"

# ---------------------------------------------------------------------------
# True colours (24-bit 0xRRGGBB).  The values below give exactly the same
# light output as the old script's 0xFFFF00 / 0x000080 / 0x008000.
# ---------------------------------------------------------------------------
OFF = 0x000000
RED = 0xFF0000
GREEN = 0x008000   # half intensity, as before
BLUE = 0x000080    # half intensity, as before
PURPLE = 0xFF00FF  # full red + full blue, as before


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
    "attention": Pattern(
        steps=((PURPLE, 0.2), (OFF, 1.0)),
        repeats=None,
        help="purple flash every 1.2 s - user should intervene",
    ),
    "working": Pattern(
        steps=((GREEN, 0.15), (OFF, 0.15)),
        repeats=None,
        help="green blinking (~3 Hz) - machine is working",
    ),
    "error-fast": Pattern(
        # 0.3 s per cycle x 200 cycles = 60 seconds, then the script exits.
        steps=((RED, 0.15), (OFF, 0.15)),
        repeats=200,
        help="red blinking (~3 Hz) for 60 s, then stop",
    ),
    "ok": Pattern(
        steps=((BLUE, 1.0), (OFF, 1.0)),
        repeats=4,
        help="four long blue blinks, then stop - all is OK",
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
    "error": Pattern(
        steps=((RED, 0.2), (OFF, 0.1), (RED, 0.2), (OFF, 1.6)),
        repeats=None,
        help="red double-blink every 2.1 s - definitely an error",
    ),
    "test": Pattern(
        steps=((RED, 1.0), (GREEN, 1.0), (BLUE, 1.0), (OFF, 0.0)),
        repeats=1,
        help="red, green, blue for 1 s each - check wiring and colour order",
    ),
}

# The original DotStar script took the numbers 1-6 (with a different meaning
# from the NeoPixel script).  Keep them so existing callers work exactly as
# before.  Code 7 is new: the red double-blink existed in the old file but
# could never be selected.
NUMERIC_CODES = {
    "1": "attention",
    "2": "working",
    "3": "error-fast",
    "4": "ok",
    "5": "reset",
    "6": "off",
    "7": "error",
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
        description="Blink a DotStar status LED (bit-banged GPIO, no SPI).",
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
        "-d", "--data-pin", type=int,
        default=config_pin("statusDotStarData_gpio", DEFAULT_DATA_PIN),
        help="GPIO (BCM) number of the DotStar data line "
             "(default: statusDotStarData_gpio in config.py, else %(default)s)",
    )
    parser.add_argument(
        "-c", "--clock-pin", type=int,
        default=config_pin("statusDotStarClock_gpio", DEFAULT_CLOCK_PIN),
        help="GPIO (BCM) number of the DotStar clock line "
             "(default: statusDotStarClock_gpio in config.py, else %(default)s)",
    )
    parser.add_argument(
        "-n", "--pixels", type=int, default=1,
        help="number of DotStars in the chain (default: 1)",
    )
    parser.add_argument(
        "-b", "--brightness", type=float, default=1.0,
        help="overall brightness from 0.0 to 1.0 (default: 1.0)",
    )
    parser.add_argument(
        "-o", "--order", default=DEFAULT_ORDER,
        choices=["RGB", "RBG", "GRB", "GBR", "BRG", "BGR"],
        help="colour byte order the LED expects (default: %(default)s)",
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
    if args.data_pin == args.clock_pin:
        parser.error("--data-pin and --clock-pin must be different")
    return args


def open_pixels(data_pin: int, clock_pin: int, count: int,
                brightness: float, order: str):
    """Create the DotStar object on the given data and clock pins.

    The hardware libraries are imported here, not at the top of the file,
    so that `--help` and `--list` work even on a machine without the LED.

    Because these are not the hardware SPI pins, adafruit_dotstar
    automatically drives them in software rather than through SPI.

    auto_write=False means changing colours does *not* immediately send data
    to the LEDs; we call show() once per step instead.  This avoids redundant
    transfers and makes every colour change a single, atomic update.
    """
    import board
    import adafruit_dotstar

    pins = []
    for pin in (clock_pin, data_pin):
        try:
            pins.append(getattr(board, f"D{pin}"))
        except AttributeError:
            sys.exit(f"statusBlinkerDS: GPIO {pin} is not a valid pin on this board")

    return adafruit_dotstar.DotStar(
        pins[0], pins[1], count,
        brightness=brightness, auto_write=False, pixel_order=order,
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

    pixels = open_pixels(args.data_pin, args.clock_pin, args.pixels,
                         args.brightness, args.order)

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
        # Always leave the LED dark.  "Off" is sent twice for reliability,
        # as the original script did.
        set_colour(pixels, OFF)
        time.sleep(0.01)
        set_colour(pixels, OFF)
        pixels.deinit()  # release the GPIO pins
    return 0


if __name__ == "__main__":
    sys.exit(main())
