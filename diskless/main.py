#!/usr/bin/env python3

from flask import Flask, request, jsonify
import subprocess

app = Flask(__name__)

@app.route('/ansible-playbook', methods=['GET'])
def ansible_playbook():
    node = request.args.get("node")

    cmd_call = subprocess.Popen(
            "ansible-playbook ",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True
            )
        stdout, stderr = cmd_call.communicate()
        stdout = stdout.decode("utf-8")
        stderr = stderr.decode("utf-8")
        exit_code = cmd_call.returncode
        return str(stdout), str(stderr), exit_code

    print(node)
    return jsonify({"status": "OK"}), 200

if __name__ == "__main__":

    print("BlueBanquise diskless automate now running as server on port 7777")
    print("URLs map:")
    print(app.url_map)
    app.run(host="0.0.0.0", port=7777, debug=True)
    quit()