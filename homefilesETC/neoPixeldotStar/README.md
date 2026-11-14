# statusBlinker — status LED for MothPad

MothPad devices show their status by blinking an Adafruit LED. There are two
hardware variants, each with its own script:

| Script               | LED type                     | Wires          | How it is driven                     |
|----------------------|------------------------------|----------------|--------------------------------------|
| `statusBlinkerNP.py` | NeoPixel (WS2812)            | data           | Raspberry Pi 5 PIO hardware          |
| `statusBlinkerDS.py` | DotStar 5050 (APA102)        | data + clock   | two plain GPIO pins (software)       |

Neither script uses SPI. The SPI0 bus (GPIO 8–11) is left to the Waveshare
High-Precision AD HAT: a NeoPixel or DotStar on SPI would pick up the ADC's
traffic and flicker, and its own updates could corrupt ADC commands.

Both scripts take the same options and read their pins from `config.py`, which
must sit in the same directory as the script.

## Wiring

| LED pin     | Raspberry Pi                         | `config.py` setting                     |
|-------------|--------------------------------------|-----------------------------------------|
| NeoPixel DIN | GPIO 26 (physical pin 37)           | `statusNeoPixel_gpio = 26`              |
| DotStar DI   | GPIO 26 (physical pin 37)           | `statusDotStarData_gpio = 26`           |
| DotStar CI   | GPIO 5 (physical pin 29)            | `statusDotStarClock_gpio = 5`           |
| 5V / VIN     | 5V (physical pin 2 or 4)            |                                         |
| GND          | GND (physical pin 39, next to pin 37) |                                       |

Pins 29, 37 and 39 are all at the same end of the header, in the row
nearest the board's edge. The other pins in use are listed in `config.py`
(see "Which GPIO pins will we use?").

## One-time setup

### 1. Give your user access to the GPIO and PIO hardware

```bash
sudo usermod -aG gpio "$USER"     # /dev/gpiochip* and /dev/pio0 belong to group gpio
sudo reboot                        # or log out and back in
```

SPI does **not** need to be enabled for the status LED. (The AD HAT still
needs `dtparam=spi=on` in `/boot/firmware/config.txt`.)

### 2. Create the Python virtual environment at `~/PyEnvs/neopixel`

The one environment serves both scripts.

```bash
mkdir -p ~/PyEnvs
python3 -m venv ~/PyEnvs/neopixel
~/PyEnvs/neopixel/bin/pip install --upgrade pip
~/PyEnvs/neopixel/bin/pip install \
    adafruit-blinka \
    "gpiod>=2.2.2,<3" \
    adafruit-circuitpython-neopixel \
    Adafruit-Blinka-Raspberry-Pi5-Neopixel \
    adafruit-circuitpython-dotstar
```

- `adafruit-blinka` and `gpiod` give CircuitPython-style `board` pin access
  on the Pi. Without `gpiod`, `import board` fails with "The platform library
  'gpiod' was not found".
- `Adafruit-Blinka-Raspberry-Pi5-Neopixel` lets the NeoPixel library use the
  Pi 5's PIO hardware. NeoPixels need very precise timing, so this package
  is required on a Pi 5.
- `adafruit-circuitpython-dotstar` drives the DotStar from any two GPIO pins.

Tested on a Raspberry Pi 5 running Raspberry Pi OS (Debian 13 "trixie"),
Python 3.13, Adafruit-Blinka 10.2, adafruit-circuitpython-neopixel 6.4.2,
Adafruit-Blinka-Raspberry-Pi5-Neopixel 1.0.0rc2, adafruit-circuitpython-dotstar 2.2.21.

### 3. Install the scripts

```bash
chmod +x statusBlinkerNP.py statusBlinkerDS.py
cp statusBlinkerNP.py config.py ~/bin/    # NeoPixel devices
# or
cp statusBlinkerDS.py config.py ~/bin/    # DotStar devices
```

`config.py` sets `statusLED = '/home/canopylife/bin/statusBlinker.py'`. Either
change that to the new name, or install the right script under the old name
(e.g. `cp statusBlinkerDS.py ~/bin/statusBlinker.py`).

The scripts' first line points at `~/PyEnvs/neopixel/bin/python3`, so they
can be run directly without activating the venv.

## Usage

```bash
./statusBlinkerNP.py --list        # show every pattern
./statusBlinkerNP.py working       # blink until stopped
./statusBlinkerNP.py 2             # legacy numeric codes still work
./statusBlinkerNP.py off           # turn the LED off
./statusBlinkerNP.py test          # red, green, blue once each: check wiring
./statusBlinkerDS.py ok -b 0.3     # 30% brightness
```

### Patterns

The numeric codes are kept exactly as in each original script, so existing
callers do not need to change. **The numbers mean different things on the two
device types**, so names are safer in new code.

| Name         | NeoPixel code: behaviour                 | DotStar code: behaviour                       |
|--------------|------------------------------------------|-----------------------------------------------|
| `error-fast` | 1: fast red (10 Hz), forever             | 3: red (~3 Hz) for 60 s, then off             |
| `working`    | 2: fast green (10 Hz), forever           | 2: green (~3 Hz), forever                     |
| `error`      | 3: red double-blink, forever             | 7 *(new)*: red double-blink, forever          |
| `ok`         | 4: four long **green** blinks (~8 s)     | 4: four long **blue** blinks (~8 s)           |
| `reset`      | 5: four long red blinks (~8 s)           | 5: four long red blinks (~8 s)                |
| `off`        | 6: LED off                               | 6: LED off                                    |
| `attention`  | 7 *(new)*: brief purple flash every 1 s  | 1: purple flash every 1.2 s, forever          |
| `test`       | –: red, green, blue, 1 s each            | –: red, green, blue, 1 s each                 |

### Options

| Option                  | NP | DS | Meaning                                         |
|-------------------------|----|----|-------------------------------------------------|
| `-p / --pin N`          | ✓  |    | NeoPixel data GPIO (default from `config.py`)   |
| `-d / --data-pin N`     |    | ✓  | DotStar data GPIO (default from `config.py`)    |
| `-c / --clock-pin N`    |    | ✓  | DotStar clock GPIO (default from `config.py`)   |
| `-n / --pixels N`       | ✓  | ✓  | number of LEDs (NP default 10, DS default 1)    |
| `-b / --brightness X`   | ✓  | ✓  | 0.0–1.0 (default 1.0)                           |
| `-o / --order XYZ`      |    | ✓  | colour byte order the LED expects (default RBG) |
| `-l / --list`           | ✓  | ✓  | list patterns                                   |

"Forever" patterns run until the process is stopped with Ctrl-C or `kill`
(SIGTERM/SIGINT/SIGHUP). The LED is always switched off before the script
exits, so it is never left stuck on.

### Calling from another program

```python
import subprocess
import config as c

blinker = subprocess.Popen([c.statusLED, "working"])
# ... do work ...
blinker.terminate()   # LED turns off cleanly
blinker.wait()
```

## Adding a pattern

Add an entry to the `PATTERNS` dictionary in the script: a list of
`(colour, seconds)` steps plus a repeat count (`None` = forever). Optionally
give it a number in `NUMERIC_CODES`.
