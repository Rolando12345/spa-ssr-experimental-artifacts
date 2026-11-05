import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

TABLES = ROOT / "tables"

TABLES.mkdir(exist_ok=True)


class TableGenerator:

    def __init__(self, statistics):

        self.statistics = statistics

    def export_csv(self):

        file = TABLES / "performance_results.csv"

        metric_order = [

            "performance",

            "fcp",

            "lcp",

            "speed_index",

            "tbt"

        ]

        with open(file, "w", newline="", encoding="utf-8") as csvfile:

            writer = csv.writer(csvfile)

            writer.writerow([

                "Architecture",

                "Page",

                "Metric",

                "Runs",

                "Mean",

                "Std Dev",

                "Minimum",

                "Maximum"

            ])

            for architecture, pages in self.statistics.items():

                for page, metrics in pages.items():

                    for metric in metric_order:

                        if metric not in metrics:
                            continue

                        values = metrics[metric]

                        writer.writerow([

                            architecture.upper(),

                            page.capitalize(),

                            metric.upper(),

                            values["runs"],

                            values["mean"],

                            values["std"],

                            values["min"],

                            values["max"]

                        ])

        print(f"\nCSV exported: {file}")

        return file