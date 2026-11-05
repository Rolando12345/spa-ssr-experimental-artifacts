import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

TABLES = ROOT / "tables"

TABLES.mkdir(exist_ok=True)


class CostTableGenerator:

    def __init__(self, statistics):

        self.statistics = statistics

    def export_csv(self):

        output = TABLES / "cost_results.csv"

        rows = 0

        with open(
            output,
            "w",
            newline="",
            encoding="utf-8"
        ) as csvfile:

            writer = csv.writer(csvfile)

            writer.writerow([

                "Architecture",

                "Page",

                "Metric",

                "Valid Runs",

                "Mean",

                "Std Dev",

                "Minimum",

                "Maximum"

            ])

            for architecture in sorted(self.statistics.keys()):

                pages = self.statistics[architecture]

                for page in sorted(pages.keys()):

                    metrics = pages[page]

                    for metric in sorted(metrics.keys()):

                        values = metrics[metric]

                        writer.writerow([

                            architecture.upper(),

                            page.capitalize(),

                            metric.upper(),

                            values["valid_runs"],

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

    print("Cost Table Generator")
