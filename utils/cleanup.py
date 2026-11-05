from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent.parent

DIRECTORIES = {

    "Results": ROOT / "results",

    "Tables": ROOT / "tables",

    "Figures": ROOT / "figures",

    "Logs": ROOT / "logs"

}

K6_OUTPUTS = (
    ROOT / "results" / "k6",
    ROOT / "tables" / "k6_scalability_results.csv",
    ROOT / "figures" / "response_time.png",
    ROOT / "figures" / "p95_response.png",
    ROOT / "figures" / "throughput.png",
    ROOT / "figures" / "error_rate.png",
)


def count_files(directory: Path):
    """Count files recursively."""

    if not directory.exists():
        return 0

    return sum(1 for file in directory.rglob("*") if file.is_file())


def clean_previous_results():

    print()
    print("=" * 60)
    print("PREVIOUS EXPERIMENT VALIDATION")
    print("=" * 60)

    total_previous = 0

    for name, directory in DIRECTORIES.items():

        files = count_files(directory)

        total_previous += files

        print(f"{name:<10}: {files} files")

    print("-" * 60)
    print(f"Total previous files : {total_previous}")

    print()
    print("Cleaning previous experiment...")

    for directory in DIRECTORIES.values():

        if directory.exists():

            shutil.rmtree(directory)

        directory.mkdir(parents=True, exist_ok=True)

    print("Cleaning completed successfully.")

    print()
    print("=" * 60)
    print("CURRENT WORKSPACE VALIDATION")
    print("=" * 60)

    total_current = 0

    for name, directory in DIRECTORIES.items():

        files = count_files(directory)

        total_current += files

        print(f"{name:<10}: {files} files")

    print("-" * 60)
    print(f"Total current files : {total_current}")

    if total_current == 0:

        print()
        print("Workspace successfully cleaned.")
        print("Ready to start a new experiment.")

    else:

        print()
        print("WARNING: Some files remain in the workspace.")

    print("=" * 60)
    print()


def clean_previous_k6_results():
    """Remove only k6-derived outputs and preserve Lighthouse and costs."""
    print()
    print("=" * 60)
    print("K6 OFFICIAL CAMPAIGN CLEANUP")
    print("=" * 60)

    removed = 0
    for output in K6_OUTPUTS:
        if output.is_dir():
            removed += count_files(output)
            shutil.rmtree(output)
        elif output.is_file():
            output.unlink()
            removed += 1

    (ROOT / "results" / "k6").mkdir(parents=True, exist_ok=True)
    print(f"Previous k6 files removed: {removed}")
    print("Lighthouse and cost outputs were preserved.")
    print("=" * 60)
    print()


if __name__ == "__main__":

    clean_previous_results()
