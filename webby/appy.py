from flask import Flask, render_template, request, jsonify
import subprocess

app = Flask(__name__)

SCRIPTS = {
    "script1": "/home/arducam/bin/script1.py",
    "script2": "/home/arducam/bin/script2.py",
    "script3": "/home/arducam/bin/script3.py"
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
        subprocess.run(["/home/arducam/eINK/bin/python3", SCRIPTS[script_name]], check=True)
        return jsonify({"status": "success"})
    except subprocess.CalledProcessError:
        return jsonify({"status": "failure"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=2727)

