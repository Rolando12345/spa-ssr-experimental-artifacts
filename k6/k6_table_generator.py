import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

TABLES = ROOT / "tables"
TABLES.mkdir(exist_ok=True)


class K6TableGenerator:

    def __init__(self, statistics):

        self.statistics = statistics

    def export_csv(self):

        output = TABLES / "k6_scalability_results.csv"

        with open(output, "w", newline="", encoding="utf-8") as csvfile:

            writer = csv.writer(csvfile)

            writer.writerow([

                "Architecture",

                "Page",

                "Users (VUs)",

                "Metric",

                "Complete Runs",

                "Mean",

                "Std Dev",

                "Minimum",

                "Maximum"

            ])

            rows = 0

            for architecture, pages in self.statistics.items():

                for page, scenarios in pages.items():

                    for users, metrics in scenarios.items():

                        for metric, values in metrics.items():

                            writer.writerow([

                                architecture.upper(),

                                page.capitalize(),

                                users,

                                metric.upper(),

                                values["complete_runs"],

                                values["mean"],

                                values["std"],

                                values["min"],

                                values["max"]

                            ])

                            rows += 1

        print()
        print(f"CSV exported: {output}")
        print(f"Rows exported: {rows}")

        return output


if __name__ == "__main__":

    print("K6 Table Generator")
