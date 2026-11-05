import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results" / "k6"
FILE_PATTERN = re.compile(r".+_vu(?P<vus>\d+)_run(?P<run>\d+)$")


class K6Parser:
    def __init__(self):
        self.results = {}
        self.invalid = []

    def read_json(self, file_path):
        with file_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)

        metrics = data.get("metrics", {})
        duration = metrics.get("transaction_duration")
        requests_metric = metrics.get("http_reqs")
        failed_metric = metrics.get("transaction_failed")
        transactions_metric = metrics.get("transactions")
        checks_metric = metrics.get("checks")
        root_checks = data.get("root_group", {}).get("checks", {})
        status_check = root_checks.get("transaction resource status == 200", {})

        if not all((duration, requests_metric, failed_metric, transactions_metric, checks_metric)):
            raise ValueError("required k6 metrics are missing")

        total_requests = int(requests_metric.get("count", 0) or 0)
        transaction_count = int(transactions_metric.get("count", 0) or 0)
        status_passes = int(status_check.get("passes", 0) or 0)
        status_fails = int(status_check.get("fails", 0) or 0)
        error_fraction = float(failed_metric.get("value", 0.0) or 0.0)
        checks_fraction = float(checks_metric.get("value", 0.0) or 0.0)

        # A run with requests but zero HTTP 200 responses is not discarded: it
        # is valid evidence of saturation. Only technically incomplete reports
        # (missing metrics or zero recorded requests) are excluded.
        if total_requests == 0 or transaction_count == 0:
            raise ValueError("execution contains no recorded HTTP request")

        return {
            "mean_transaction_ms": float(duration["avg"]),
            "p95_transaction_ms": float(duration["p(95)"]),
            "throughput_total_rps": float(transactions_metric["rate"]),
            "throughput_success_rps": (
                float(transactions_metric["rate"]) * (1.0 - error_fraction)
            ),
            "error_rate_pct": error_fraction * 100.0,
            "checks_passed_pct": checks_fraction * 100.0,
            "http_requests": total_requests,
            "transactions": transaction_count,
            "http_200_passes": status_passes,
            "http_200_fails": status_fails,
            "http_200_success_pct": (
                status_passes / (status_passes + status_fails) * 100.0
                if status_passes + status_fails > 0
                else 0.0
            ),
        }

    def load_results(self):
        self.results.clear()
        self.invalid.clear()
        processed = 0

        for file_path in sorted(RESULTS.glob("*/*/vu_*/*.json")):
            architecture = file_path.parents[2].name
            page = file_path.parents[1].name
            match = FILE_PATTERN.match(file_path.stem)
            if not match:
                self.invalid.append((str(file_path), "invalid filename"))
                continue

            vus = int(match.group("vus"))
            try:
                record = self.read_json(file_path)
                self.results.setdefault(architecture, {}).setdefault(page, {}).setdefault(
                    vus, []
                ).append(record)
                processed += 1
            except Exception as exc:
                self.invalid.append((str(file_path), str(exc)))

        print(f"\nComplete k6 JSON files processed: {processed}")
        print(f"Incomplete k6 JSON files excluded: {len(self.invalid)}")
        for path, reason in self.invalid:
            print(f"  - {path}: {reason}")
        return self.results


if __name__ == "__main__":
    K6Parser().load_results()
