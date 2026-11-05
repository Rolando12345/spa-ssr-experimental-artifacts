# SPA–SSR Experimental Pipeline — Official Campaign 3.2.0

## Scope of this version

- Lighthouse, k6, and resource measurements alternate SPA and SSR using an
  AB/BA sequence.
- Lighthouse produces a real browser network trace for each page.
- k6 reconstructs a cold HTTP navigation from the document, static resources,
  and REST calls observed by Lighthouse.
- k6 does not execute client-side JavaScript or verify hydration. Angular
  browser rendering is outside the k6 latency and throughput boundary, whereas
  Next.js rendering occurs before the SSR document is returned.
- Transaction latency, error rate, and throughput refer to complete HTTP
  transactions rather than isolated requests.
- Navigation is replayed in three stages: document, concurrent static
  resources, and concurrent XHR/Fetch requests.
- k6 allows up to 180 seconds for started iterations to finish and applies a
  15-second timeout to each resource. Failed transactions remain recorded.
- The official campaign uses 1, 5, 10, 25, and 50 VUs for 30 seconds per
  repetition. Exceeding the experimental SLA is retained as degradation
  evidence and does not make a run technically incomplete.
- Each VU limits batches to 10 requests and 6 concurrent connections per host.
- Resource measurements apply one complete navigation transaction per second
  to both implementations and report CPU and RAM for the frontend-server
  process tree.

## Confirmed environment

- Python 3.14.6
- psutil 7.2.2
- Angular SPA at `http://localhost:4200`
- Next.js SSR at `http://localhost:3000`
- Spring Boot at `http://localhost:8080`

Spring Boot and MySQL must remain active throughout the campaign. Angular and
Next.js must run from production builds.

## Preparation

```powershell
venv\Scripts\activate
python -m pip install -r requirements.txt
python --version
k6 version
lighthouse --version
```

Before starting, verify Dashboard, Inventory, and Sales on ports 4200 and 3000.

## Required order for phase-by-phase execution

Lighthouse must run first because its traces generate the six transaction
manifests used by k6 and the resource phase.

```powershell
python main.py --phase lighthouse
python main.py --phase k6 --keep-results
python main.py --phase costs --keep-results
```

Do not omit `--keep-results` from the second and third commands. Without it,
the required Lighthouse traces would be removed.

The complete official command is:

```powershell
python main.py --phase all
```

Its automatic order is Lighthouse -> resources -> k6. Resource measurements
run before stress testing to reduce the influence of residual process state on
CPU and RAM observations.

## Experimental design

Each phase uses five repetitions. For each page and repetition, treatments
alternate as follows:

```text
Repetition 1: SPA -> SSR
Repetition 2: SSR -> SPA
Repetition 3: SPA -> SSR
Repetition 4: SSR -> SPA
Repetition 5: SPA -> SSR
```

k6 performs 2 implementations × 3 pages × 5 loads × 5 repetitions = 150
runs. The official loads are 1, 5, 10, 25, and 50 VUs for 30 seconds.

On the 4 GB laptop, 50 VUs is the calibrated stress level. Unrelated
applications should remain closed, the computer should stay connected to AC
power, and users should not interact with it during the official campaign.
Runs must not be cancelled solely because they exceed the SLA. Aggregation
requires all 150 k6 runs to be technically complete.

## Transaction model

After Lighthouse, six manifests are created under:

```text
config/transactions/spa/dashboard.json
config/transactions/ssr/dashboard.json
...
```

Each manifest retains HTTP 200 requests observed during a valid browser
navigation: the document, CSS, JavaScript, fonts, XHR/Fetch calls, and other
resources. The HTTP model replays the document, concurrent static resources,
and concurrent data requests. If either frontend is rebuilt and hashed resource
names change, Lighthouse must be rerun before k6 or resource measurements.

## Resource measurements

Both implementations receive an offered rate of one complete navigation per
second for 30 seconds. CPU and RAM cover the frontend server process tree on
port 4200 or 3000.

Network counters are system-wide in psutil and are retained only as diagnostic
outputs. They are excluded from the article's decision metrics because traffic
cannot be attributed to one process with the same precision as CPU and RSS.

## Integrity

- Do not mix outputs produced by different campaign versions.
- Preserve original JSON files, validation records, logs, tables, and figures.
- A technically complete k6 run that exceeds the SLA remains saturation
  evidence.
- The illustrative classification thresholds are p95 ≤ 2000 ms and transaction
  error rate ≤ 20%.
- Do not publish partial phase results without documenting missing runs.

The `results` directory contains 360 JSON files: 210 official runs (30
Lighthouse, 150 k6, and 30 resource measurements) and 150 validation records,
one for each k6 run. Validation records are integrity controls, not additional
experimental runs.
