import argparse
import platform
import time
import traceback

import psutil

from config.urls import URLS
from costs.cost_parser import CostParser
from costs.figure_generator import CostFigureGenerator
from costs.run_costs import run_costs
from costs.statistics import CostStatistics
from costs.table_generator import CostTableGenerator
from k6.k6_figure_generator import K6FigureGenerator
from k6.k6_parser import K6Parser
from k6.k6_statistics import K6Statistics
from k6.k6_table_generator import K6TableGenerator
from k6.run_k6 import run_k6
from lighthouse.figure_generator import FigureGenerator
from lighthouse.lighthouse_parser import LighthouseParser
from lighthouse.run_lighthouse import run_experiment
from lighthouse.server_checker import server_online
from lighthouse.statistics import StatisticsGenerator
from lighthouse.table_generator import TableGenerator
from utils.cleanup import clean_previous_k6_results, clean_previous_results


def phase_time(start, name):
    print(f"\n{name} completed in {round(time.time() - start, 2)} seconds")


def require_servers():
    for architecture in ("SPA", "SSR"):
        url = URLS[architecture]["Dashboard"]
        if not server_online(url):
            raise RuntimeError(f"{architecture} server is OFFLINE: {url}")


def wait_for_servers():
    while True:
        if all(server_online(URLS[a]["Dashboard"]) for a in ("SPA", "SSR")):
            print("SPA and SSR servers are ONLINE.")
            return
        print("Waiting 5 seconds for server recovery...")
        time.sleep(5)


def process_lighthouse_results():
    data = LighthouseParser().load_results()
    report = StatisticsGenerator(data).calculate()
    TableGenerator(report).export_csv()
    FigureGenerator().generate_all()


def process_k6_results():
    parser = K6Parser()
    data = parser.load_results()
    if not data:
        raise RuntimeError("No valid k6 result is available for processing.")
    report = K6Statistics(data).calculate()
    K6TableGenerator(report).export_csv()
    K6FigureGenerator().generate_all()


def process_cost_results():
    parser = CostParser()
    data = parser.load_results()
    if not data:
        raise RuntimeError("No valid cost result is available for processing.")
    report = CostStatistics(data).calculate()
    CostTableGenerator(report).export_csv()
    CostFigureGenerator().generate_all()


def parse_args():
    parser = argparse.ArgumentParser(description="SPA vs SSR experiment")
    parser.add_argument(
        "--phase",
        choices=("all", "lighthouse", "k6", "costs", "process"),
        default="all",
        help="experimental phase to execute",
    )
    parser.add_argument(
        "--keep-results",
        action="store_true",
        help="do not delete existing outputs before execution",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    started = time.time()

    print("=" * 60)
    print("SPA vs SSR Experimental Framework - corrected version")
    print(f"Python: {platform.python_version()}")
    print(f"psutil: {psutil.__version__}")
    print("=" * 60)

    if args.phase == "k6" and args.keep_results:
        clean_previous_k6_results()
    elif not args.keep_results and args.phase != "process":
        clean_previous_results()

    try:
        if args.phase != "process":
            require_servers()
            print("Waiting 10 seconds for servers to stabilize...")
            time.sleep(10)

        if args.phase in ("all", "lighthouse"):
            phase = time.time()
            run_experiment()
            process_lighthouse_results()
            phase_time(phase, "LIGHTHOUSE")

        # In a complete campaign, resource costs are measured before the
        # high-load k6 phase so that stress-induced process state does not
        # contaminate CPU and RAM observations.
        if args.phase == "all":
            phase = time.time()
            run_costs()
            process_cost_results()
            phase_time(phase, "COST ANALYSIS")

        if args.phase in ("all", "k6"):
            phase = time.time()
            run_k6()
            process_k6_results()
            phase_time(phase, "K6")

        if args.phase == "costs":
            phase = time.time()
            run_costs()
            process_cost_results()
            phase_time(phase, "COST ANALYSIS")

        if args.phase == "process":
            process_lighthouse_results()
            process_k6_results()
            process_cost_results()

        print(f"\nCompleted in {round((time.time() - started) / 60, 2)} minutes")
    except Exception:
        print("\nEXPERIMENT FAILED")
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
