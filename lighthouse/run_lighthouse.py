import json
import os
import shutil
import subprocess
import time
from pathlib import Path

from config.config import LIGHTHOUSE_COMMAND, LIGHTHOUSE_RUNS, WAIT_SECONDS
from config.urls import URLS
from lighthouse.logger import error, finish, start, success, write
from lighthouse.server_checker import server_online

ROOT = Path(__file__).resolve().parent.parent
ARCHITECTURES = ("SPA", "SSR")


def lighthouse_command(url, output):
    """Resolve npm's Windows .cmd shim and native executables reliably."""
    candidates = [LIGHTHOUSE_COMMAND]
    if os.name == "nt" and not LIGHTHOUSE_COMMAND.lower().endswith(".cmd"):
        candidates.insert(0, f"{LIGHTHOUSE_COMMAND}.cmd")
    executable = next((shutil.which(name) for name in candidates if shutil.which(name)), None)
    if executable is None:
        raise RuntimeError(
            "Lighthouse was not found in PATH. Verify with: where lighthouse"
        )

    arguments = [
        executable, url, "--preset=desktop", "--output=json",
        f"--output-path={output}",
        "--chrome-flags=--headless=new --disable-gpu --no-sandbox",
        "--quiet",
    ]
    # npm installs Lighthouse as a .cmd shim on Windows. Batch files must be
    # launched through cmd.exe; native executables use direct execution.
    if os.name == "nt" and executable.lower().endswith((".cmd", ".bat")):
        return [os.environ.get("COMSPEC", "cmd.exe"), "/d", "/s", "/c", *arguments]
    return arguments


def architecture_order(run):
    return ARCHITECTURES if run % 2 else tuple(reversed(ARCHITECTURES))


def valid_report(path):
    if not path.exists():
        return False
    try:
        with path.open("r", encoding="utf-8") as handle:
            report = json.load(handle)
        return not report.get("runtimeError") and report.get("audits", {}).get(
            "largest-contentful-paint", {}).get("numericValue") is not None
    except (OSError, json.JSONDecodeError):
        return False


def run_experiment():
    for architecture in ARCHITECTURES:
        url = URLS[architecture]["Dashboard"]
        write(f"Checking {architecture} server...")
        if not server_online(url):
            raise RuntimeError(f"{architecture} server is OFFLINE")
        write(f"{architecture} server ONLINE")

    start()
    successful = failed = current = 0
    total = 2 * 3 * LIGHTHOUSE_RUNS
    for page in ("Dashboard", "Inventory", "Sales"):
        for run in range(1, LIGHTHOUSE_RUNS + 1):
            for architecture in architecture_order(run):
                url = URLS[architecture][page]
                folder = ROOT / "results" / architecture.lower() / page.lower()
                folder.mkdir(parents=True, exist_ok=True)
                output = folder / f"{page.lower()}_{run}.json"
                current += 1
                print(f"\nLighthouse {current}/{total} | {architecture} | {page} | Run {run}")
                try:
                    command = lighthouse_command(url, output)
                    completed = subprocess.run(command, check=False, capture_output=True, text=True)
                    if valid_report(output):
                        success(architecture, page, run)
                        successful += 1
                        if completed.returncode != 0:
                            write(f"NOTICE | valid JSON retained despite Chrome temporary cleanup return code | {architecture} | {page} | Run {run}")
                    else:
                        raise RuntimeError(completed.stderr or "invalid Lighthouse JSON")
                except Exception as exc:
                    failed += 1
                    error(architecture, page, run, exc)
                    print(f"   FAILED: {exc}")
                time.sleep(WAIT_SECONDS)
    finish()
    print(f"\nLighthouse valid: {successful}/{total}; failed: {failed}")
    if successful != total:
        raise RuntimeError("Lighthouse campaign is incomplete; do not publish partial results")


if __name__ == "__main__":
    run_experiment()
