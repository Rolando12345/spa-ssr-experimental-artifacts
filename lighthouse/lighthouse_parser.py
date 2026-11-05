import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

RESULTS = ROOT / "results"


class LighthouseParser:

    def __init__(self):

        self.results = {}
        self.files_processed = 0

    def read_json(self, file_path):

        try:

            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            audits = data["audits"]

            self.files_processed += 1

            return {

                "performance":
                    data["categories"]["performance"]["score"] * 100,

                "fcp":
                    audits.get("first-contentful-paint", {}).get("numericValue"),

                "lcp":
                    audits.get("largest-contentful-paint", {}).get("numericValue"),

                "speed_index":
                    audits.get("speed-index", {}).get("numericValue"),

                "tbt":
                    audits.get("total-blocking-time", {}).get("numericValue")

            }

        except Exception as ex:

            print(f"Error reading {file_path.name}: {ex}")

            return None

    def load_results(self):

        if not RESULTS.exists():
            raise FileNotFoundError(
                "Results directory not found. Run Lighthouse first."
            )

        for architecture in RESULTS.iterdir():

            if not architecture.is_dir():
                continue

            self.results[architecture.name] = {}

            for page in architecture.iterdir():

                if not page.is_dir():
                    continue

                self.results[architecture.name][page.name] = []

                for file in sorted(page.glob("*.json")):

                    metrics = self.read_json(file)

                    if metrics is not None:
                        self.results[architecture.name][page.name].append(metrics)

        print(f"\nJSON files processed: {self.files_processed}")

        return self.results


if __name__ == "__main__":

    parser = LighthouseParser()

    data = parser.load_results()

    from pprint import pprint

    pprint(data)