from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent

TABLES = ROOT / "tables"

FIGURES = ROOT / "figures"

FIGURES.mkdir(exist_ok=True)


class FigureGenerator:

    def __init__(self):

        self.csv = TABLES / "performance_results.csv"

        self.data = pd.read_csv(self.csv)

    def generate_metric(self, metric):

        df = self.data[self.data["Metric"] == metric]

        if df.empty:

            print(f"No data available for {metric}. Figure skipped.")

            return

        pivot = df.pivot(

            index="Page",

            columns="Architecture",

            values="Mean"

        )

        if pivot.empty:

            print(f"No numeric values found for {metric}. Figure skipped.")

            return

        plt.figure(figsize=(7, 5))

        ax = pivot.plot(

            kind="bar",

            color=["#1976D2", "#D32F2F"]

        )

        ax.set_title(metric)

        ax.set_xlabel("Module")

        ax.set_ylabel(metric)

        ax.grid(

            axis="y",

            linestyle="--",

            alpha=0.5

        )

        plt.tight_layout()

        output = FIGURES / f"{metric.lower()}.png"

        plt.savefig(

            output,

            dpi=300,

            bbox_inches="tight"

        )

        plt.close("all")

        print(f"Figure generated: {output.name}")

    def generate_all(self):

        metrics = [

            "PERFORMANCE",

            "FCP",

            "LCP",

            "SPEED_INDEX",

            "TBT"

        ]

        for metric in metrics:

            self.generate_metric(metric)