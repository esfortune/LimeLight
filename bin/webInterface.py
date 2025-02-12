#!/home/arducam/webby/bin/python3
# Eric Fortune, Canopy Life, February 2024
# Code written for Limelight Rainforest test device.
# This provides a web interface for users to check and manipulate
# the device before deployment.

# Track the PID so that we can kill the process when needed.
import os
import sys

PID_FILE = "/home/arducam/wifiUP.txt"  # Path to store the PID

# Save the current process PID
with open(PID_FILE, "w") as f:
    f.write(str(os.getpid()))

# We are running the web interface via FLASK
from flask import Flask, render_template, request, jsonify
import subprocess

app = Flask(__name__)

# Each of the scripts must be listed here. Python scripts are handled differently below.
SCRIPTS = {
    "script1": "/home/arducam/bin/eINKstatus.py",
    "script2": "/home/arducam/bin/wifiV1down.sh",
    "script3": "/home/arducam/bin/allLEDsOFF.sh",
    "script4": "/home/arducam/bin/takeStudioPhoto.sh",
    "script5": "/home/arducam/bin/msgDate.sh",
    "script6": "/home/arducam/bin/checkMode.py"
}

# THIS IS OUR WEBPAGE, found in the "templates" directory
@app.route("/")
def index():
    return render_template("index.html")


# Running SCRIPTS
@app.route("/run-script", methods=["POST"])
def run_script():
    data = request.json
    script_name = data.get("script")

    if script_name not in SCRIPTS:
        return jsonify({"status": "error", "message": "Invalid script"}), 400

    try:
        # PYTHON SCRIPTS
        if (script_name == "script1" or script_name == "script6"):
            result = subprocess.run(SCRIPTS[script_name], capture_output=True, text=True)
        # SHELL SCRIPTS (BASH)
        else:
            result = subprocess.run(["/bin/bash", SCRIPTS[script_name]], capture_output=True, text=True, check=True)
        return jsonify({"status": "success", "output": result.stdout.strip()})

    except subprocess.CalledProcessError as e:
        return jsonify({"status": "failure", "output": e.stderr.strip()})


# Setting System Time
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

# We are currently running this on port 5001
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)

