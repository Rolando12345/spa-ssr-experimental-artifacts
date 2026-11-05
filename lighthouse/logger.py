from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "experiment.log"


def separator():
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write("-" * 70 + "\n")


def write(message):

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{now}] {message}\n")


def start():

    separator()
    write("LIGHTHOUSE EXPERIMENT STARTED")
    separator()


def finish():

    separator()
    write("LIGHTHOUSE EXPERIMENT FINISHED")
    separator()


def success(architecture, page, run):

    write(f"SUCCESS | {architecture} | {page} | Run {run}")


def error(architecture, page, run, exception):

    write(f"ERROR | {architecture} | {page} | Run {run}")

    write(str(exception))