from statistics import mean, stdev


class CostStatistics:
    def __init__(self, data):
        self.data = data

    def calculate(self):
        report = {}
        metrics = (
            "cpu_mean_pct",
            "cpu_max_pct",
            "ram_mean_mb",
            "ram_max_mb",
            "network_corrected_mb",
            "successful_requests",
            "failed_requests",
            "successful_transactions_per_second",
            "cpu_pct_per_successful_tps",
            "network_mb_per_successful_transaction",
            "sample_count",
        )

        for architecture, pages in self.data.items():
            report[architecture] = {}
            for page, runs in pages.items():
                report[architecture][page] = {}
                for metric in metrics:
                    values = [run[metric] for run in runs]
                    report[architecture][page][metric] = {
                        "valid_runs": len(values),
                        "mean": round(mean(values), 4),
                        "std": round(stdev(values), 4) if len(values) > 1 else 0,
                        "min": round(min(values), 4),
                        "max": round(max(values), 4),
                    }
        return report
