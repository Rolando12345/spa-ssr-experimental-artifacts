from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent

LOGS = ROOT / "logs"
LOGS.mkdir(exist_ok=True)

LOG_FILE = LOGS / "costs.log"


def write(message):

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(LOG_FILE, "a", encoding="utf-8") as file:

        file.write(f"[{timestamp}] {message}\n")


def start():

    write("=" * 60)
    write("COST EXPERIMENT STARTED")


def finish():

    write("COST EXPERIMENT FINISHED")
    write("=" * 60)


def success(architecture, page, run):

    write(
        f"SUCCESS | {architecture} | {page} | Run {run}"
    )


def error(architecture, page, run, exception):

    write(
        f"ERROR | {architecture} | {page} | Run {run} | {exception}"
    )