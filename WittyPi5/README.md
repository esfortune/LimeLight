# Witty Pi 5 schedule + logging

| File | Purpose |
|---|---|
| `~/wittypi_schedule.txt` | ON windows (`ON HH:MM-HH:MM`), low-voltage cutoff, recovery voltage |
| `~/wittypi_log.csv` | Hourly readings, plus one row at every boot and every shutdown |
| `~/wittypi_events.log` | One line each time the schedule is applied (or fails) |
| `/var/log/wp5d.log` | UUGear daemon: startup and shutdown reasons |

## Commands
    wpsched plan      # preview what the schedule file will do (no hardware changes)
    wpsched apply     # re-read the schedule file now and arm the Witty Pi
    wpsched status    # live voltages, temperature, settings, armed alarms
    wpsched log       # add a manual row to the CSV

## How it works
* The Witty Pi 5 holds one startup alarm and one shutdown alarm. `wpsched apply`
  arms the next pair. It runs at every boot (the start of each ON window),
  at 00:05 daily, and whenever you call it.
* Without network time, the battery-backed Witty Pi RTC is the clock used.
* **Low-voltage protection** happens in the Witty Pi firmware. When Vin drops below
  `LOW_VOLTAGE`, the board asks the Pi to shut down. UUGear's `wp5d` runs
  `shutdown -h now`, and the board cuts power 15 s after the Pi halts.
  The next scheduled window powers the Pi up again. If the voltage is still low,
  it shuts down cleanly again.
* systemd units: `wpsched-apply.service/.timer`, `wpsched-log.timer`, `wpsched-session.service`.

Install or update: `sudo ./install.sh`

## If the Witty Pi is removed
Nothing breaks if the board is taken off. `wp5d` keeps looking for the board but
does nothing, `wpsched apply` adds an `apply FAILED` line to
`~/wittypi_events.log` at each boot and at 00:05, and the hourly log keeps
recording the Pi's own readings with the Witty Pi columns blank. There is **no**
on/off schedule and **no** low-voltage protection without the board. If the
board is going back on, leave everything as it is: it is found again
automatically at the next boot.

**Pause (keep everything installed):**

    sudo systemctl disable --now wpsched-apply.timer wpsched-log.timer wp5d
    sudo systemctl disable wpsched-apply.service wpsched-session.service wp5d_poweroff wp5d_reboot

Resume by running `sudo ./install.sh` again.

**Remove completely:**

    sudo systemctl disable --now wpsched-apply.timer wpsched-log.timer
    sudo systemctl disable wpsched-apply.service wpsched-session.service
    sudo rm /etc/systemd/system/wpsched-* /usr/local/bin/wpsched
    sudo apt remove -y wp5        # UUGear daemon and its shutdown hooks
    sudo systemctl daemon-reload

This leaves `~/wittypi_schedule.txt`, `~/wittypi_log.csv`, `~/wittypi_events.log`,
`/var/log/wp5d.log` and this folder in place. Delete them by hand if you don't
want them. No changes to `/boot/firmware/config.txt` are needed.
