from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent

TABLES = ROOT / "tables"

FIGURES = ROOT / "figures"

FIGURES.mkdir(exist_ok=True)


class K6FigureGenerator:

    def __init__(self):

        self.csv = TABLES / "k6_scalability_results.csv"

        if not self.csv.exists():

            raise FileNotFoundError(

                f"CSV not found: {self.csv}"

            )

        self.data = pd.read_csv(self.csv)

    def generate_metric(self, metric, filename, ylabel):

        df = self.data[self.data["Metric"] == metric]

        if df.empty:

            print(f"No data available for {metric}")

            return

        pivot = df.pivot_table(

            index="Users (VUs)",

            columns="Architecture",

            values="Mean"

        )

        # Keep VU levels in numeric order.
        pivot = pivot.sort_index(key=lambda x: x.astype(int))

        ax = pivot.plot(

            figsize=(8, 5),

            marker="o",

            linewidth=2

        )

        ax.set_title(metric.replace("_", " "))

        ax.set_xlabel("Concurrent Users (VUs)")

        ax.set_ylabel(ylabel)

        ax.grid(

            True,

            linestyle="--",

            alpha=0.4

        )

        ax.legend(title="Architecture")

        plt.tight_layout()

        output = FIGURES / filename

        plt.savefig(

            output,

            dpi=300,

            bbox_inches="tight"

        )

        plt.close("all")

        print(f"Figure generated: {filename}")

    def generate_all(self):

        self.generate_metric(

            "MEAN_TRANSACTION_MS",

            "response_time.png",

            "Complete Transaction Time (ms)"

        )

        self.generate_metric(

            "P95_TRANSACTION_MS",

            "p95_response.png",

            "P95 Complete Transaction Time (ms)"

        )

        self.generate_metric(

            "THROUGHPUT_SUCCESS_RPS",

            "throughput.png",

            "Successful Transactions/sec"

        )

        self.generate_metric(

            "ERROR_RATE_PCT",

            "error_rate.png",

            "Error Rate (%)"

        )

        self.generate_metric(

            "CHECKS_PASSED_PCT",

            "checks.png",

            "Checks (%)"


        )


if __name__ == "__main__":

    generator = K6FigureGenerator()

    generator.generate_all()
