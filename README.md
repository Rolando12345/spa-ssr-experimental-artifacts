# SPA–SSR Experimental Artifacts

This repository contains the scripts, navigation manifests, run-level results,
validation records, consolidated tables, figures, and logs supporting the
article **“An Evidence-Based Decision Framework for Selecting Angular SPA and
Next.js SSR.”**

## Experimental scope

The study compares two complete frontend implementation stacks under the
documented local test conditions:

- Angular 20.2.0, compiled for production and delivered with `serve 14.2.6`.
- Next.js 15.5.3 with server-side rendering, compiled for production and run
  with `next start`.
- Shared Spring Boot 3.4.2 backend and MySQL 8.4 database snapshot.
- Dashboard, Inventory, and Sales features.
- Five repetitions per condition.

The comparison does not isolate rendering strategy from framework, bundling,
runtime, hydration, or serving-tool differences.

## Measurement boundary

- Lighthouse executes each application in Chrome and characterizes initial
  loading through FCP, LCP, Speed Index, and TBT.
- k6 replays the HTTP navigation flow derived from Lighthouse traces. It
  requests the document, static resources, and XHR/Fetch endpoints, but it does
  **not** execute client-side JavaScript or verify browser hydration. Therefore,
  Angular browser rendering is outside the k6 latency and throughput boundary,
  whereas Next.js server rendering occurs before the SSR HTML response is
  returned.
- Resource measurements cover the Node.js frontend-server process tree only:
  static delivery through `serve` for Angular and server rendering through
  `next start` for Next.js. They exclude the Java backend, browser, database,
  and load-generator resource use and do not represent total-system resource
  consumption.
- The applications, backend, database, browser, and k6 generator ran on the
  same computer. Generator-side resource use was not measured separately, so
  the artifacts do not establish that the generator was free from resource
  constraints at the highest loads.

## Artifact inventory

The `results` directory contains 360 JSON files:

| Artifact | Count | Definition |
|---|---:|---|
| Lighthouse results | 30 | 2 stacks × 3 features × 5 repetitions |
| k6 run results | 150 | 2 stacks × 3 features × 5 VU levels × 5 repetitions |
| Resource results | 30 | 2 stacks × 3 features × 5 repetitions |
| k6 validation records | 150 | One integrity record for each k6 run |

Thus, 210 JSON files correspond to the official experimental runs reported in
the article. The remaining 150 JSON files are validation records, not
additional runs.

Other repository contents are:

- `config/transactions/`: six HTTP navigation manifests generated from valid
  Lighthouse traces.
- `lighthouse/`, `k6/`, `costs/`, and `utils/`: experiment and processing code.
- `tables/`: three consolidated CSV files used for the reported tables.
- `figures/`: figures regenerated from the consolidated results.
- `logs/`: phase and process-identification records.
- `README-EJECUCION.md`: original Spanish execution instructions.
- `SERVING-CONDITIONS.md`: observed caching, compression, and response-header
  conditions.

Raw logs and resource JSON files preserve local Windows paths as provenance;
they contain no credentials or authentication tokens.

## Official matrix

The campaign comprises 210 official runs:

- Lighthouse: 30 runs.
- k6: 150 runs at 1, 5, 10, 25, and 50 virtual users for 30 seconds.
- Frontend-server resources: 30 runs with a 10-second warm-up, a 30-second
  measurement window, 0.5-second sampling, and an offered rate of one complete
  navigation transaction per second.

The experimental thresholds of p95 ≤ 2 seconds and transaction error rate ≤
20% are illustrative internal classification criteria, not general service
targets. Runs that exceeded either threshold were retained.

## Environment

- Windows 10, build 10.0.17763.9020, x64
- Intel Core i3-5005U, 2.00 GHz, 4 GB RAM
- Node.js 24.14.0
- Python 3.14.6 and psutil 7.2.2
- Lighthouse CLI 13.4.0 and Google Chrome 150.0.7871.129 (headless)
- k6 v2.0.0-rc1
- Spring Boot 3.4.2 and MySQL Server 8.4

## Reproduction prerequisites

The scripts expect the evaluated applications to be available at:

- Angular SPA: `http://localhost:4200`
- Next.js SSR: `http://localhost:3000`
- Shared backend: `http://localhost:8080`

The frontend, backend, and database application source code is not included in
this artifact package. The run-level evidence and all processing scripts needed
to inspect and regenerate the consolidated tables and figures are included.

Install the Python dependencies in an isolated environment:

```powershell
python -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt
```

The original execution order and commands are documented in
`README-EJECUCION.md`. Running a new campaign overwrites generated outputs;
preserve the published `results`, `tables`, `figures`, and `logs` before doing
so.

## Interpretation

The five repetitions and descriptive statistics support characterization of
the observed campaign but do not establish statistical significance or general
superiority. High-load results reflect the evaluated shared host and cannot
locate the bottleneck among the frontend, backend, database, and generator.

