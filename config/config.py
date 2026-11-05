from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Output directories
RESULTS = ROOT / "results"

TABLES = ROOT / "tables"

FIGURES = ROOT / "figures"

LOGS = ROOT / "logs"

# Lighthouse
LIGHTHOUSE_RUNS = 5

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

LIGHTHOUSE_COMMAND = "lighthouse"

# k6
K6_RUNS = 5

# One warm-up is executed before the official repetitions of each
# architecture/page/load combination. Its output is not included in results.
K6_WARMUP_VUS = 2
K6_WARMUP_DURATION = "5s"
K6_RECOVERY_SECONDS = 15
K6_GRACEFUL_STOP = "180s"
K6_RESOURCE_TIMEOUT = "15s"

# Before warm-up and before every official repetition, the target must return
# HTTP 200. The framework waits for recovery instead of immediately skipping a
# repetition after a saturation event.
K6_HEALTH_TIMEOUT_SECONDS = 180
K6_HEALTH_POLL_SECONDS = 5

# A run is marked invalid when no HTTP request succeeds. The campaign
# continues so that the failure remains documented in the validation CSV.
K6_ABORT_ERROR_RATE = 0.20
K6_SLA_P95_MS = 2000

# Resource measurements
COST_RUNS = 5

# Resource measurements use a fixed observation window and the same fixed
# arrival rate of complete navigation transactions for both treatments.
COST_WARMUP_SECONDS = 10
COST_MEASUREMENT_SECONDS = 30
COST_SAMPLE_INTERVAL = 0.5
COST_WORKERS = 4
COST_RECOVERY_SECONDS = 15
COST_TRANSACTION_RATE = 1.0

# Network counters are system-wide in psutil. An idle baseline is measured
# before every run and subtracted from the observed transfer rate.
COST_NETWORK_BASELINE_SECONDS = 5

# Execution control
WAIT_SECONDS = 5
