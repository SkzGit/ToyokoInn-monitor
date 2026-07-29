from pathlib import Path
from datetime import datetime
import json
import logging
import subprocess
import shutil
import os

logging.getLogger("werkzeug").setLevel(logging.ERROR)

from flask import (
    Flask,
    request,
    send_from_directory,
    send_file,
    jsonify,
)

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent

CONFIG_FILE = BASE_DIR / "config" / "settings.json"
HISTORY_FILE = BASE_DIR / "data" / "history.json"
STATE_FILE = BASE_DIR / "data" / "state.json"

monitor_process = None

def find_git():
    candidates = [
        shutil.which("git"),
        shutil.which("git.exe"),
        r"C:\Program Files\Git\cmd\git.exe",
        r"C:\Program Files (x86)\Git\cmd\git.exe",
    ]

    for git in candidates:
        if git and os.path.exists(git):
            return git

    raise FileNotFoundError("Git が見つかりません。")

def run_git(git, *args):
    return subprocess.run(
        [git, *args],
        cwd=BASE_DIR,
        capture_output=True,
        text=True,
    )

def clear_log():

    log_file = BASE_DIR / "data" / "monitor.log"

    with open(log_file, "w", encoding="utf-8"):
        pass

def clear_history():
    history_file = BASE_DIR / "data" / "history.json"
    with open(
        history_file,
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            [],
            f,
            ensure_ascii=False,
            indent=4,
        )

@app.route("/")
def index():
    return send_from_directory("web", "index.html")


@app.route("/data/<path:path>")
def data_files(path):
    return send_from_directory("data", path)

@app.route("/<path:path>")
def static_files(path):
    return send_from_directory("web", path)

@app.get("/settings")
def load_settings():

    with open(CONFIG_FILE, encoding="utf-8") as f:
        return json.load(f)

@app.post("/settings")
def save_settings():

    data = request.get_json()

    with open(
        CONFIG_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=4,
        )

    return {"result": "ok"}

@app.get("/export-settings")
def export_settings():

    return send_file(
        CONFIG_FILE,
        as_attachment=True,
        download_name=f"settings-{datetime.now():%Y%m%d-%H%M%S}.json",
    )

@app.post("/import-settings")
def import_settings():

    data = request.get_json()

    with open(
        CONFIG_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=4,
        )

    return {
        "result": "ok"
    }

@app.post("/start")
def start_monitor():

    global monitor_process

    # 既に起動中なら何もしない
    if monitor_process is not None and monitor_process.poll() is None:
        return {
            "result": "already_running"
        }

    clear_log()

    if request.get_json().get("clearHistory", False):
        clear_history()

    if request.get_json().get("clearState", False):

        with open(
            STATE_FILE,
            "w",
            encoding="utf-8",
        ) as f:

            json.dump(
                {},
                f,
                ensure_ascii=False,
                indent=4,
            )

    monitor_process = subprocess.Popen(
        ["python", "-m", "app.monitor"],
        cwd=BASE_DIR,
    )

    return {
        "result": "ok"
    }

@app.post("/stop")
def stop_monitor():

    global monitor_process

    if monitor_process is None or monitor_process.poll() is not None:
        return {
            "result": "not_running"
        }

    monitor_process.terminate()

    monitor_process.wait()

    monitor_process = None

    return {
        "result": "ok"
    }

@app.get("/status")
def monitor_status():

    global monitor_process

    running = (
        monitor_process is not None
        and monitor_process.poll() is None
    )

    return {
        "running": running
    }

@app.post("/git-push")
def git_push():
    try:
        git = find_git()

        add = run_git(git, "add", ".")

        commit = run_git(
            git,
            "commit",
            "-m",
            "Auto update",
        )

        commit_ok = (
            commit.returncode == 0
            or "nothing to commit" in commit.stdout
        )        

        pull = run_git(
            git,
            "pull",
            "--rebase",
        )

        push = run_git(git, "push")

        return jsonify({
            "add_success": add.returncode == 0,
            "commit_success": commit_ok,
            "pull_success": pull.returncode == 0,
            "push_success": push.returncode == 0,

            "commit_stdout": commit.stdout,
            "commit_stderr": commit.stderr,

            "pull_stdout": pull.stdout,
            "pull_stderr": pull.stderr,

            "push_stdout": push.stdout,
            "push_stderr": push.stderr,
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e),
        })

@app.get("/logs")
def get_logs():

    log_file = BASE_DIR / "data" / "monitor.log"

    if not log_file.exists():
        return {
            "logs": []
        }

    with open(log_file, "r", encoding="utf-8") as f:
        logs = f.readlines()

    return {
        "logs": [line.rstrip() for line in logs[-100:]]
    }

@app.get("/history")
def get_history():

    if not HISTORY_FILE.exists():
        return {"history": []}

    with open(
        HISTORY_FILE,
        encoding="utf-8",
    ) as f:

        history = json.load(f)

    return {
        "history": history
    }

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True,
    )