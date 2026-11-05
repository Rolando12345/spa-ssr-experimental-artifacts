from statistics import mean, stdev


class K6Statistics:
    def __init__(self, data):
        self.data = data

    def calculate(self):
        report = {}
        metrics = (
            "mean_transaction_ms",
            "p95_transaction_ms",
            "throughput_total_rps",
            "throughput_success_rps",
            "error_rate_pct",
            "checks_passed_pct",
            "http_requests",
            "transactions",
            "http_200_passes",
            "http_200_fails",
            "http_200_success_pct",
        )

        for architecture, pages in self.data.items():
            report[architecture] = {}
            for page, scenarios in pages.items():
                report[architecture][page] = {}
                for vus, runs in scenarios.items():
                    report[architecture][page][vus] = {}
                    for metric in metrics:
                        dataset = [execution[metric] for execution in runs]
                        report[architecture][page][vus][metric] = {
                            "complete_runs": len(dataset),
                            "mean": round(mean(dataset), 4),
                            "std": round(stdev(dataset), 4) if len(dataset) > 1 else 0,
                            "min": round(min(dataset), 4),
                            "max": round(max(dataset), 4),
                        }
        return report
