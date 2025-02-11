from flask import Flask, render_template, request, jsonify
import subprocess

app = Flask(__name__)

SCRIPTS = {
    "script1": "/home/arducam/bin/eINKstatus.py",
    "script2": "/home/arducam/bin/script2.sh",
    "script3": "/home/arducam/bin/script3.sh"
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
            subprocess.run("/home/arducam/bin/eINKstatus.py", check=True)
        if script_name == "script2":
            subprocess.run(["/bin/bash", SCRIPTS[script_name]], check=True)
        return jsonify({"status": "success"})
    except subprocess.CalledProcessError:
        return jsonify({"status": "failure"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=2727)

