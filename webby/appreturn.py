from flask import Flask, render_template, request, jsonify
import subprocess

app = Flask(__name__)

SCRIPTS = {
    "script1": "/home/arducam/bin/eINKstatus.py",
    "script2": "/home/arducam/bin/wifiV1down.sh",
    "script3": "/home/arducam/bin/echoecho.sh"
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
        if script_name == "script1":
            result = subprocess.run("/home/arducam/bin/eINKstatus.py", capture_output=True, text=True, check=True)
        if script_name == "script2":
            result = subprocess.run(["/bin/bash", SCRIPTS[script_name]], capture_output=True, text=True, check=True)
        if script_name == "script3":
            result = subprocess.run(["/bin/bash", SCRIPTS[script_name]], capture_output=True, text=True, check=True)
        return jsonify({"status": "success", "output": result.stdout.strip()})
    except subprocess.CalledProcessError as e:
        return jsonify({"status": "failure", "output": e.stderr.strip()})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=2727)

