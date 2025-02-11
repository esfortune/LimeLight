from flask import Flask, render_template, request, jsonify
import subprocess

app = Flask(__name__)

SCRIPTS = {
    "script1": "/home/arducam/bin/eINKstatus.py",
    "script2": "/home/arducam/bin/wifiV1down.sh",
    "script3": "/home/arducam/bin/allLEDsOFF.sh",
    "script4": "/home/arducam/bin/takeStudioPhoto.sh",
    "script5": "/home/arducam/bin/msgDate.sh",
    "script6": "/home/arducam/bin/checkMode.py"
}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/run-script", methods=["POST"])
def run_script():
    data = request.json
    script_name = data.get("script")

    if script_name not in SCRIPTS:
        return jsonify({"status": "error", "message": "Invalid script"}), 400

    try:
        if (script_name == "script1" or script_name == "script6"):
            result = subprocess.run(SCRIPTS[script_name], capture_output=True, text=True, check=True)
        else:
            result = subprocess.run(["/bin/bash", SCRIPTS[script_name]], capture_output=True, text=True, check=True)
        return jsonify({"status": "success", "output": result.stdout.strip()})

    except subprocess.CalledProcessError as e:
        return jsonify({"status": "failure", "output": e.stderr.strip()})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=2727)

