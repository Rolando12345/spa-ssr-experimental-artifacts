import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import psutil
import requests

from config.config import (
    COST_MEASUREMENT_SECONDS, COST_NETWORK_BASELINE_SECONDS,
    COST_RECOVERY_SECONDS, COST_RUNS, COST_SAMPLE_INTERVAL,
    COST_TRANSACTION_RATE, COST_WARMUP_SECONDS, COST_WORKERS,
)
from config.urls import URLS
from costs.logger import error, finish, start, success, write
from costs.monitor import CostMonitor
from costs.process_finder import find_process
from utils.transactions import ensure_transaction_manifests

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results" / "costs"
ARCHITECTURES = ("SPA", "SSR")


def get_port(architecture):
    return 4200 if architecture.upper() == "SPA" else 3000


def network_bytes():
    counters = psutil.net_io_counters()
    return counters.bytes_sent + counters.bytes_recv


def measure_idle_network_rate(seconds):
    before = network_bytes()
    started = time.monotonic()
    time.sleep(seconds)
    return max(network_bytes() - before, 0) / (time.monotonic() - started)


def fetch_resource(request):
    try:
        response = requests.get(request["url"], timeout=15)
        return response.status_code == 200
    except requests.RequestException:
        return False


def fetch_stage(resources):
    if not resources:
        return True, 0
    workers = min(len(resources), 8)
    with ThreadPoolExecutor(max_workers=workers) as executor:
        outcomes = list(executor.map(fetch_resource, resources))
    return all(outcomes), len(outcomes)


def execute_transaction(requests_list):
    """Replay document, static and data stages using browser-like concurrency."""
    document = next(
        (item for item in requests_list if item["resource_type"] == "Document"),
        None,
    )
    static = [
        item for item in requests_list
        if item["resource_type"] not in ("Document", "XHR", "Fetch")
    ]
    dynamic = [
        item for item in requests_list
        if item["resource_type"] in ("XHR", "Fetch")
    ]
    if document is None:
        return False, 0

    resources = 1
    if not fetch_resource(document):
        return False, resources
    static_ok, static_count = fetch_stage(static)
    resources += static_count
    if not static_ok:
        return False, resources
    dynamic_ok, dynamic_count = fetch_stage(dynamic)
    resources += dynamic_count
    return dynamic_ok, resources


def fixed_rate_workload(requests_list, duration, rate, workers, result_box):
    futures = []
    started = time.monotonic()
    next_release = started
    with ThreadPoolExecutor(max_workers=workers) as executor:
        while next_release - started < duration:
            wait = next_release - time.monotonic()
            if wait > 0:
                time.sleep(wait)
            futures.append(executor.submit(execute_transaction, requests_list))
            next_release += 1.0 / rate
        results = [future.result() for future in futures]
    result_box.update({
        "transactions_total": len(results),
        "transactions_success": sum(ok for ok, _ in results),
        "transactions_failed": sum(not ok for ok, _ in results),
        "resource_requests": sum(count for _, count in results),
    })


def warm_up(requests_list):
    deadline = time.monotonic() + COST_WARMUP_SECONDS
    successes = 0
    while time.monotonic() < deadline:
        ok, _ = execute_transaction(requests_list)
        successes += int(ok)
    if successes == 0:
        raise RuntimeError("warm-up produced no complete successful transaction")


def execute_measurement(architecture, page, url, run, manifest):
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    root_process = find_process(get_port(architecture), architecture)

    requests_list = manifest["requests"]
    warm_up(requests_list)
    baseline_rate = measure_idle_network_rate(COST_NETWORK_BASELINE_SECONDS)
    monitor = CostMonitor(root_process, COST_SAMPLE_INTERVAL)
    counters = {}
    worker = threading.Thread(
        target=fixed_rate_workload,
        args=(requests_list, COST_MEASUREMENT_SECONDS, COST_TRANSACTION_RATE,
              COST_WORKERS, counters),
        daemon=False,
    )
    network_before = network_bytes()
    started = time.monotonic()
    worker.start()
    samples = monitor.sample_for(COST_MEASUREMENT_SECONDS)
    worker.join()
    elapsed = time.monotonic() - started
    network_total = max(network_bytes() - network_before, 0)
    corrected = max(network_total - baseline_rate * elapsed, 0)

    if counters.get("transactions_success", 0) == 0:
        raise RuntimeError("measurement produced no successful transaction")
    if len(samples["cpu_machine_pct"]) < 10:
        raise RuntimeError("insufficient resource samples")

    process_metadata = monitor.process_metadata()
    if not process_metadata or process_metadata[0]["pid"] <= 4:
        raise RuntimeError("invalid frontend process metadata; cost run rejected")
    if process_metadata[0]["name"].lower() not in ("node.exe", "node"):
        raise RuntimeError("frontend process is not Node.js; cost run rejected")

    return {
        "metadata": {
            "architecture": architecture, "page": page, "run": run,
            "url": url, "port": get_port(architecture),
            "python_version": "3.14.6", "psutil_version": psutil.__version__,
            "sample_interval_seconds": COST_SAMPLE_INTERVAL,
            "measurement_seconds": round(elapsed, 4),
            "offered_transactions_per_second": COST_TRANSACTION_RATE,
            "workers": COST_WORKERS,
            "transaction_model": manifest["model"],
            "transaction_replay": "document -> parallel static -> parallel XHR/Fetch",
            "transaction_resources": len(requests_list),
            "process_scope": "frontend server process tree",
            "processes": process_metadata,
        },
        "workload": counters,
        "samples": samples,
        "network": {
            "scope": "system-wide counters with idle-baseline correction",
            "baseline_bytes_per_second": round(baseline_rate, 4),
            "observed_total_mb": round(network_total / 1024 / 1024, 6),
            "baseline_estimate_mb": round(baseline_rate * elapsed / 1024 / 1024, 6),
            "corrected_total_mb": round(corrected / 1024 / 1024, 6),
        },
    }


def architecture_order(run):
    return ARCHITECTURES if run % 2 else tuple(reversed(ARCHITECTURES))


def run_costs():
    manifests = ensure_transaction_manifests()
    RESULTS.mkdir(parents=True, exist_ok=True)
    start()
    total = 2 * 3 * COST_RUNS
    current = successful = failed = 0
    for page in ("Dashboard", "Inventory", "Sales"):
        for run in range(1, COST_RUNS + 1):
            for architecture in architecture_order(run):
                current += 1
                url = URLS[architecture][page]
                manifest = manifests[(architecture, page)][1]
                folder = RESULTS / architecture.lower() / page.lower()
                folder.mkdir(parents=True, exist_ok=True)
                output = folder / f"{page.lower()}_run{run}.json"
                print(f"\nCost {current}/{total} | {architecture} | {page} | Run {run}")
                try:
                    result = execute_measurement(architecture, page, url, run, manifest)
                    with output.open("w", encoding="utf-8") as handle:
                        json.dump(result, handle, indent=4)
                    success(architecture, page, run)
                    write(f"PROCESS | {architecture} | {page} | Run {run} | {result['metadata']['processes']}")
                    successful += 1
                except Exception as exc:
                    failed += 1
                    error(architecture, page, run, exc)
                    print(f"   FAILED: {exc}")
                time.sleep(COST_RECOVERY_SECONDS)
    finish()
    print(f"\nValid cost runs: {successful}/{total}; failed: {failed}")
    if successful != total:
        raise RuntimeError(
            f"Official cost campaign incomplete: {successful}/{total}. "
            "Do not publish partial results."
        )


if __name__ == "__main__":
    run_costs()
