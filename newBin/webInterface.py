#!/home/arducam/PyEnvs/webby/bin/python3
####!/Users/eric/NotCloudy/PyEnvs/webby/bin/python3
# Eric Fortune, Canopy Life, February 2025
# Code written for Limelight Rainforest test device.
# This provides a web interface for users to check and manipulate
# the device before deployment.

# Track the PID so that we can kill the process when needed.
import os
import sys
import re
import traceback

PID_FILE = "/home/arducam/wifiUP.txt"  # Path to store the PID

cron_BASIC_FILE = os.path.expanduser("/home/arducam/cron/basic.txt")
cron_PRESET1 = os.path.expanduser("/home/arducam/cron/preset1.txt")
cron_PRESET2 = os.path.expanduser("/home/arducam/cron/preset2.txt")
CRON_COMMANDS = {'studio': '/home/arducam/bin/takeStudioPhoto.sh', 'audio': '/home/arducam/bin/takeAudio.sh'}

# Save the current process PID
with open(PID_FILE, "w") as f:
    f.write(str(os.getpid()))

from flask import Flask, render_template, request, jsonify, redirect, url_for
import subprocess

app = Flask(__name__)

SCRIPTS = {
    "script-devinfo": "/home/arducam/bin/wDeviceInfo.py",
    "script2": "/home/arducam/bin/wifiV1down4ever.sh",
    "script3": "/home/arducam/bin/allLEDsOFF.sh",
    "script4": "/home/arducam/bin/takeStudioPhoto.sh",
    "script5": "/home/arducam/bin/msgDate.sh",
    "script6": "/home/arducam/bin/checkMode.py"
}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/crontab")
def crontab():
    return render_template("crontab.html")

@app.route('/set-crontab', methods=['POST'])
def set_crontab():
    try:
        data = request.get_json()
        cron_lines = []

        # Load baseline lines from cronbasics.txt
        if os.path.exists(cron_BASIC_FILE):
            with open(cron_BASIC_FILE, 'r') as f:
                cron_lines.extend(line.strip() for line in f if line.strip())

        for task in ['studio', 'audio']:
            if not data.get(f'{task}_enabled'):
                continue

            cmd = CRON_COMMANDS[task]
            mode = data.get(f'{task}_mode')

            if mode == 'everyday':
                s = data[f'{task}_everyday']
                interval = int(s['interval'])
                start = int(s['start'])
                end = s['end']

                if str(end).startswith('next-'):
                    # Split into two crontab lines
                    actual_end = int(end.replace('next-', ''))
                    cron_lines.append(f"*/{interval} {start}-23 * * * {cmd}")
                    cron_lines.append(f"*/{interval} 0-{actual_end} * * * {cmd}")
                else:
                    cron_lines.append(f"*/{interval} {start}-{int(end)} * * * {cmd}")

            elif mode == 'custom':
                for day, vals in data[f'{task}_custom'].items():
                    interval = int(vals['interval'])
                    start = int(vals['start'])
                    end = vals['end']

                    if str(end).startswith('next-'):
                        actual_end = int(end.replace('next-', ''))
                        cron_lines.append(f"*/{interval} {start}-23 * * {day} {cmd}")
                        cron_lines.append(f"*/{interval} 0-{actual_end} * * {str((int(day)+1)%7)} {cmd}")
                    else:
                        cron_lines.append(f"*/{interval} {start}-{int(end)} * * {day} {cmd}")

        # Write to temp file and install crontab
        cron_text = "\n".join(cron_lines) + "\n"
        with open("/tmp/new_cron", "w") as f:
            f.write(cron_text)

        subprocess.run(["crontab", "/tmp/new_cron"], check=True)
        return "Crontab updated successfully."

    except Exception as e:
        print("Exception occurred:", e)
        traceback.print_exc()
        return "Failed to update crontab", 500

@app.route('/load_preset1', methods=['POST'])
def load_preset1():

    try:
        if os.path.exists(cron_PRESET1):
            if os.path.exists(cron_BASIC_FILE):
                 with open('/tmp/presetcron', 'w') as out, \
                     open(cron_BASIC_FILE, 'r') as f1, \
                     open(cron_PRESET1, 'r') as f2:
                     out.write(f1.read())
                     out.write(f2.read())

        # Write updated crontab
        subprocess.run(["crontab", "/tmp/presetcron"], check=True)
        return "Crontab updated successfully."

    except Exception as e:
        return f"Failed to load preset: {str(e)}", 500

@app.route('/get-crontab', methods=['GET'])
def get_crontab():
    try:
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True, check=True)
        return jsonify({"status": "success", "crontab": result.stdout})
    except subprocess.CalledProcessError as e:
        return jsonify({"status": "failure", "crontab": e.stderr.strip()}), 500


@app.route("/run-script", methods=["POST"])
def run_script():
    data = request.json
    script_name = data.get("script")

    if script_name not in SCRIPTS:
        return jsonify({"status": "error", "message": "Invalid script"}), 400

    try:
        if script_name in ["script-devinfo", "script6"]:
            result = subprocess.run(SCRIPTS[script_name], capture_output=True, text=True, check=True)
        else:
            result = subprocess.run(["/bin/bash", SCRIPTS[script_name]], capture_output=True, text=True, check=True)
        return jsonify({"status": "success", "output": result.stdout.strip()})

    except subprocess.CalledProcessError as e:
        return jsonify({"status": "failure", "output": e.stderr.strip()})

@app.route("/set-time", methods=["POST"])
def set_time():
    data = request.json
    new_time = data.get("time")

    if not new_time:
        return jsonify({"status": "error", "message": "No time provided"}), 400

    try:
        subprocess.run(["sudo", "date", "-s", new_time], check=True)
        return jsonify({"status": "success", "message": f"Time set to {new_time}"})
    except subprocess.CalledProcessError as e:
        return jsonify({"status": "failure", "message": e.stderr.strip()}), 500

@app.route('/set-location', methods=['POST'])
def set_location():
    data = request.get_json()
    location = data.get('location', '')

    if not re.match(r'^[\w\-]+$', location):
        return 'Invalid input: only letters, numbers, dashes, and underscores allowed.', 400

    location_file = os.path.expanduser('~/location.txt')
    try:
        with open(location_file, 'w') as f:
            f.write(location)
        return f'Location "{location}" saved.'
    except Exception as e:
        return f'Failed to save location: {e}', 500

@app.route('/set-gps', methods=['POST'])
def set_gps():
    data = request.get_json()
    gps = data.get('gps', '')

    if not re.match(r'^[a-zA-Z0-9,\s.]+$', gps):
        return 'Invalid input: only letters, numbers, dashes, underscores, commas, and periods allowed.', 400

    gps_file = os.path.expanduser('~/gps.txt')
    try:
        with open(gps_file, 'w') as f:
            f.write(gps)
        return f'GPS coordinates "{gps}" saved.'
    except Exception as e:
        return f'Failed to save gps: {e}', 500


def scan_wifi_networks(interface='wlan1'):
    try:
        output = subprocess.check_output(['nmcli', '-t', '-f', 'SSID', 'dev', 'wifi', 'list', 'ifname', interface]).decode()
        ssids = sorted(set(filter(None, output.strip().split('\n'))))  # Remove empty and duplicates
        return ssids
    except subprocess.CalledProcessError:
        return []

def get_connection_status(interface='wlan1'):
    try:
        output = subprocess.check_output(['nmcli', '-t', '-f', 'DEVICE,STATE,CONNECTION', 'dev']).decode()
        for line in output.strip().splitlines():
            parts = line.strip().split(':')
            if parts[0] == interface:
                state = parts[1]
                con = parts[2] if len(parts) > 2 else "N/A"
                return f"{interface} is {state} ({con})"
        return f"{interface} not found"
    except:
        return "Unknown"


@app.route("/wifi")
def wifi():
    ssids = scan_wifi_networks()
    status = get_connection_status()
    return render_template('wifi.html', ssids=ssids, status=status)

@app.route('/connect', methods=['POST'])
def connect():
    ssid = request.form.get('ssid')
    password = request.form.get('password')

    try:

        # Add the new connection
        subprocess.run([
            'sudo', 'nmcli', 'con', 'add',
            'type', 'wifi',
            'ifname', 'wlan1',
            'con-name', ssid,
            'ssid', ssid
        ], check=True)

        # Add password settings
        subprocess.run([
            'sudo', 'nmcli', 'con', 'modify', ssid,
            'wifi-sec.key-mgmt', 'wpa-psk',
            'wifi-sec.psk', password, 'ifname', 'wlan1'
        ], check=True)

        # Try to bring up the connection
        subprocess.run(['nmcli', 'con', 'up', ssid], check=True)

        return jsonify({"status": "success", "message": f"Connected to {ssid}."})

    except subprocess.CalledProcessError as e:
        return jsonify({
            "status": "failure",
            "message": f"Connection error: {e.stderr.strip() if e.stderr else str(e)}"
        }), 500
    except Exception as e:
        return jsonify({
            "status": "failure",
            "message": f"Unexpected error: {str(e)}"
        }), 500


if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=5001)

