import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results" / "costs"
FILE_PATTERN = re.compile(r".+_run(?P<run>\d+)$")


class CostParser:
    def __init__(self):
        self.results = {}
        self.invalid = []

    def read_json(self, file_path):
        with file_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)

        samples = data.get("samples", {})
        workload = data.get("workload", {})
        network = data.get("network", {})
        processes = data.get("metadata", {}).get("processes", [])

        cpu = samples.get("cpu_machine_pct", [])
        ram = samples.get("ram_tree_mb", [])
        if len(cpu) < 10 or len(ram) < 10:
            raise ValueError("fewer than 10 CPU/RAM samples")
        if int(workload.get("transactions_success", 0)) == 0:
            raise ValueError("no successful transaction")
        if not processes or any(int(item.get("pid", 0)) <= 4 for item in processes):
            raise ValueError("invalid system PID recorded instead of frontend process")
        if processes[0].get("name", "").lower() not in ("node.exe", "node"):
            raise ValueError("recorded frontend process is not Node.js")

        successful = int(workload["transactions_success"])
        failed = int(workload["transactions_failed"])
        duration = float(data["metadata"]["measurement_seconds"])

        return {
            "cpu_mean_pct": sum(cpu) / len(cpu),
            "cpu_max_pct": max(cpu),
            "ram_mean_mb": sum(ram) / len(ram),
            "ram_max_mb": max(ram),
            "network_corrected_mb": float(network["corrected_total_mb"]),
            "successful_requests": successful,
            "failed_requests": failed,
            "successful_transactions_per_second": successful / duration,
            "cpu_pct_per_successful_tps": (sum(cpu) / len(cpu)) / (successful / duration),
            "network_mb_per_successful_transaction": float(network["corrected_total_mb"]) / successful,
            "sample_count": len(cpu),
        }

    def load_results(self):
        self.results.clear()
        self.invalid.clear()
        processed = 0

        for file_path in sorted(RESULTS.glob("*/*/*.json")):
            architecture = file_path.parents[1].name
            page = file_path.parent.name
            if not FILE_PATTERN.match(file_path.stem):
                self.invalid.append((str(file_path), "invalid filename"))
                continue
            try:
                record = self.read_json(file_path)
                self.results.setdefault(architecture, {}).setdefault(page, []).append(record)
                processed += 1
            except Exception as exc:
                self.invalid.append((str(file_path), str(exc)))

        print(f"\nValid cost JSON files processed: {processed}")
        print(f"Invalid cost JSON files excluded: {len(self.invalid)}")
        return self.results


if __name__ == "__main__":
    CostParser().load_results()
