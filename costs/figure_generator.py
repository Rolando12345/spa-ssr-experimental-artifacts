from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent

TABLES = ROOT / "tables"

FIGURES = ROOT / "figures"

FIGURES.mkdir(exist_ok=True)


class CostFigureGenerator:

    def __init__(self):

        self.csv = TABLES / "cost_results.csv"

        self.data = pd.read_csv(self.csv)

    def generate_metric(self, metric, filename, ylabel):

        df = self.data[self.data["Metric"] == metric]

        if df.empty:

            print(f"No data available for {metric}")

            return

        pivot = df.pivot_table(

            index="Page",

            columns="Architecture",

            values="Mean"

        )

        desired_order = [

            "Dashboard",

            "Inventory",

            "Sales"

        ]

        pivot = pivot.reindex(desired_order)

        fig, ax = plt.subplots(figsize=(8, 5))

        pivot.plot(

            kind="bar",

            ax=ax,

            width=0.75

        )

        ax.set_title(metric.replace("_", " "))

        ax.set_xlabel("Module")

        ax.set_ylabel(ylabel)

        ax.grid(

            axis="y",

            linestyle="--",

            alpha=0.4

        )

        plt.tight_layout()

        output = FIGURES / filename

        fig.savefig(

            output,

            dpi=300,

            bbox_inches="tight"

        )

        plt.close(fig)

        print(f"Figure generated: {filename}")

    def generate_all(self):

        self.generate_metric(

            "CPU_MEAN_PCT",

            "cpu_usage.png",

            "CPU Usage (%)"

        )

        self.generate_metric(

            "RAM_MEAN_MB",

            "ram_usage.png",

            "Memory Usage (MB)"

        )

        self.generate_metric(

            "NETWORK_MB_PER_SUCCESSFUL_TRANSACTION",

            "network_usage.png",

            "Transferred Data per Successful Transaction (MB)"

        )

        self.generate_metric(

            "CPU_PCT_PER_SUCCESSFUL_TPS",

            "cpu_normalized.png",

            "CPU (%) per Successful Transaction/s"

        )


if __name__ == "__main__":

    generator = CostFigureGenerator()

    generator.generate_all()
