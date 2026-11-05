from statistics import mean, stdev


class StatisticsGenerator:

    def __init__(self, data):
        self.data = data

    def calculate(self):

        report = {}

        metrics = [
            "performance",
            "fcp",
            "lcp",
            "speed_index",
            "tbt"
        ]

        for architecture, pages in self.data.items():

            report[architecture] = {}

            for page, runs in pages.items():

                report[architecture][page] = {}

                for metric in metrics:

                    values = [

                        r[metric]

                        for r in runs

                        if r.get(metric) is not None

                    ]

                    if len(values) == 0:
                        continue

                    report[architecture][page][metric] = {

                        "runs": len(values),

                        "mean": round(mean(values), 2),

                        "std": round(stdev(values), 2) if len(values) > 1 else 0,

                        "min": round(min(values), 2),

                        "max": round(max(values), 2)

                    }

        return report