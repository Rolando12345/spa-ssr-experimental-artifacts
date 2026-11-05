import json
import subprocess
import time
from pathlib import Path

import requests

from config.config import (
    K6_ABORT_ERROR_RATE,
    K6_HEALTH_POLL_SECONDS,
    K6_HEALTH_TIMEOUT_SECONDS,
    K6_GRACEFUL_STOP,
    K6_RECOVERY_SECONDS,
    K6_RESOURCE_TIMEOUT,
    K6_RUNS,
    K6_SLA_P95_MS,
    K6_WARMUP_DURATION,
    K6_WARMUP_VUS,
)
from config.urls import URLS
from k6.scenarios import SCENARIOS
from utils.transactions import ensure_transaction_manifests

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results" / "k6"
VALIDATION = RESULTS / "validation"
ARCHITECTURES = ("SPA", "SSR")


def wait_until_healthy(url: str, label: str) -> float:
    """Wait until a target returns HTTP 200 or the recovery limit expires."""
    started = time.monotonic()
    last_error = "no response"

    while time.monotonic() - started <= K6_HEALTH_TIMEOUT_SECONDS:
        try:
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                elapsed = round(time.monotonic() - started, 2)
                if elapsed > 1:
                    print(f"   {label} recovered after {elapsed} seconds")
                return elapsed
            last_error = f"HTTP {response.status_code}"
        except requests.RequestException as exc:
            last_error = str(exc)

        print(f"   Waiting for {label}: {last_error}")
        time.sleep(K6_HEALTH_POLL_SECONDS)

    raise RuntimeError(
        f"{label} did not recover within {K6_HEALTH_TIMEOUT_SECONDS} seconds: "
        f"{last_error}"
    )


def k6_command(url: str, transaction_file: Path, vus: int, duration: str, output: Path | None = None):
    command = [
        "k6", "run",
        "-e", f"URL={url}",
        "-e", f"VUS={vus}",
        "-e", f"DURATION={duration}",
        "-e", f"TRANSACTION_FILE={transaction_file}",
        "-e", f"GRACEFUL_STOP={K6_GRACEFUL_STOP}",
        "-e", f"RESOURCE_TIMEOUT={K6_RESOURCE_TIMEOUT}",
    ]
    if output is not None:
        command.extend(["--summary-export", str(output)])
    command.append(str(ROOT / "k6" / "scripts" / "load_test.js"))
    return command


def read_validation(summary_file: Path) -> dict:
    """Separate technical completeness from SLA compliance."""
    if not summary_file.exists():
        return {
            "execution_complete": False,
            "valid": False,
            "sla_met": False,
            "reason": "summary file was not generated",
        }

    with summary_file.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    metrics = data.get("metrics", {})
    requests_metric = metrics.get("http_reqs") or {}
    failed_metric = metrics.get("transaction_failed") or {}
    duration_metric = metrics.get("transaction_duration") or {}
    transaction_metric = metrics.get("transactions") or {}
    checks_metric = metrics.get("checks") or {}
    root_checks = data.get("root_group", {}).get("checks", {})
    status_check = root_checks.get("transaction resource status == 200", {})

    total = int(requests_metric.get("count", 0) or 0)
    total_transactions = int(transaction_metric.get("count", 0) or 0)
    status_passes = int(status_check.get("passes", 0) or 0)
    status_fails = int(status_check.get("fails", 0) or 0)
    error_rate = failed_metric.get("value")
    p95 = duration_metric.get("p(95)")
    checks_rate = checks_metric.get("value")

    missing = []
    if total == 0:
        missing.append("no HTTP requests were recorded")
    if total_transactions == 0:
        missing.append("no complete transaction was recorded")
    if error_rate is None:
        missing.append("error rate is missing")
    if p95 is None:
        missing.append("P95 response time is missing")
    if checks_rate is None:
        missing.append("checks rate is missing")

    execution_complete = not missing
    sla_reasons = []
    if execution_complete:
        error_rate = float(error_rate)
        p95 = float(p95)
        if error_rate > K6_ABORT_ERROR_RATE:
            sla_reasons.append(
                f"error rate {error_rate:.4f} exceeded {K6_ABORT_ERROR_RATE:.2f}"
            )
        if p95 > K6_SLA_P95_MS:
            sla_reasons.append(
                f"P95 {p95:.2f} ms exceeded {K6_SLA_P95_MS} ms"
            )
        if status_passes == 0:
            sla_reasons.append("no HTTP 200 response was recorded")

    sla_met = execution_complete and not sla_reasons
    if missing:
        reason = "; ".join(missing)
    elif sla_reasons:
        reason = "execution complete; SLA not met: " + "; ".join(sla_reasons)
    else:
        reason = "execution complete; SLA met"

    return {
        "execution_complete": execution_complete,
        # Backward-compatible field: valid now means technically complete,
        # not that performance thresholds were satisfied.
        "valid": execution_complete,
        "sla_met": sla_met,
        "reason": reason,
        "http_requests": total,
        "transactions": total_transactions,
        "http_200_passes": status_passes,
        "http_200_fails": status_fails,
        "error_rate": error_rate,
        "p95_ms": p95,
        "checks_rate": checks_rate,
    }


def save_validation(architecture, page, vus, run, validation):
    VALIDATION.mkdir(parents=True, exist_ok=True)
    output = VALIDATION / (
        f"{architecture.lower()}_{page.lower()}_vu{vus}_run{run}.json"
    )
    payload = {
        "architecture": architecture,
        "page": page,
        "vus": vus,
        "run": run,
        **validation,
    }
    with output.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=4)


def run_warmup(architecture: str, page: str, url: str, transaction_file: Path, vus: int):
    label = f"{architecture} {page} {vus} VUs"
    wait_until_healthy(url, label)
    print(f"\nWarm-up | {label}")
    completed = subprocess.run(
        k6_command(url, transaction_file, K6_WARMUP_VUS, K6_WARMUP_DURATION),
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"warm-up failed for {label}")
    time.sleep(K6_RECOVERY_SECONDS)
    wait_until_healthy(url, label)


def architecture_order(run: int):
    """AB/BA counterbalancing reduces fixed-order and thermal bias."""
    return ARCHITECTURES if run % 2 == 1 else tuple(reversed(ARCHITECTURES))


def run_k6():
    print("=" * 60)
    print("k6 Scalability Experiments - alternating SPA/SSR protocol")
    print("=" * 60)

    manifests = ensure_transaction_manifests()

    for architecture in ARCHITECTURES:
        wait_until_healthy(
            URLS[architecture]["Dashboard"], f"{architecture} Dashboard"
        )

    subprocess.run(["k6", "version"], capture_output=True, check=True)

    pages = tuple(URLS["SPA"].keys())
    total = len(ARCHITECTURES) * len(pages) * len(SCENARIOS) * K6_RUNS
    completed_runs = sla_passes = incomplete_runs = current = 0

    # Page and load remain constant while the treatment alternates. Odd runs
    # use SPA->SSR and even runs SSR->SPA (AB/BA counterbalancing).
    for page in pages:
        for scenario in SCENARIOS:
            vus = int(scenario["vus"])
            duration = str(scenario["duration"])

            try:
                for architecture in ARCHITECTURES:
                    transaction_file = manifests[(architecture, page)][0]
                    run_warmup(
                        architecture,
                        page,
                        URLS[architecture][page],
                        transaction_file,
                        vus,
                    )
            except Exception as exc:
                raise RuntimeError(
                    f"K6 PRECONDITION FAILED before {page} at {vus} VUs. "
                    "A frontend server is unavailable; restart it and repeat "
                    f"the campaign from a clean folder. Cause: {exc}"
                ) from exc

            for run in range(1, K6_RUNS + 1):
                for architecture in architecture_order(run):
                    current += 1
                    url = URLS[architecture][page]
                    transaction_file = manifests[(architecture, page)][0]
                    label = f"{architecture} {page} {vus} VUs Run {run}"
                    folder = RESULTS / architecture.lower() / page.lower() / f"vu_{vus}"
                    folder.mkdir(parents=True, exist_ok=True)
                    output = folder / f"{page.lower()}_vu{vus}_run{run}.json"

                    print(
                        f"\nExecution {current}/{total} | {architecture} | "
                        f"{page} | {vus} VUs | Run {run}/{K6_RUNS}"
                    )

                    begin = time.time()
                    recovery_seconds = None
                    try:
                        recovery_seconds = wait_until_healthy(url, label)
                        result = subprocess.run(
                            k6_command(url, transaction_file, vus, duration, output),
                            check=False,
                        )
                        validation = read_validation(output)
                        validation["k6_exit_code"] = result.returncode
                        validation["elapsed_seconds"] = round(time.time() - begin, 2)
                        validation["recovery_seconds"] = recovery_seconds
                        validation["execution_order"] = current
                        save_validation(architecture, page, vus, run, validation)

                        if validation["execution_complete"]:
                            completed_runs += 1
                            if validation["sla_met"]:
                                sla_passes += 1
                                print("   COMPLETE | SLA MET")
                            else:
                                print(f"   COMPLETE | SLA NOT MET: {validation['reason']}")
                        else:
                            incomplete_runs += 1
                            print(f"   INCOMPLETE: {validation['reason']}")
                    except Exception as exc:
                        incomplete_runs += 1
                        save_validation(
                            architecture,
                            page,
                            vus,
                            run,
                            {
                                "execution_complete": False,
                                "valid": False,
                                "sla_met": False,
                                "reason": str(exc),
                                "recovery_seconds": recovery_seconds,
                                "execution_order": current,
                            },
                        )
                        print(f"   INCOMPLETE: {exc}")

                    time.sleep(K6_RECOVERY_SECONDS)

    print("\n" + "=" * 60)
    print(f"Total planned       : {total}")
    print(f"Completed runs      : {completed_runs}")
    print(f"Runs meeting SLA    : {sla_passes}")
    print(f"Runs not meeting SLA: {completed_runs - sla_passes}")
    print(f"Incomplete runs     : {incomplete_runs}")
    print("=" * 60)

    if completed_runs != total or incomplete_runs:
        raise RuntimeError(
            f"k6 campaign incomplete: {completed_runs}/{total} completed; "
            f"{incomplete_runs} incomplete. Preserve the evidence, correct "
            "the incident and do not publish partial aggregate results."
        )

    if completed_runs != total or incomplete_runs:
        raise RuntimeError(
            f"Official k6 campaign incomplete: {completed_runs}/{total}. "
            "Do not publish partial results."
        )


if __name__ == "__main__":
    run_k6()
