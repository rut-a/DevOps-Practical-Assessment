# Module 3 — ETL CI/CD Pipeline & Monitoring

This module covers two things: automating the deployment of an ETL script through a CI/CD pipeline, and setting up real-time monitoring to see os level resources and etl script status.


## What I Built

- A GitHub Actions pipeline that lints and deploys my ETL script to a Linux server over SSH
- A Python ETL script that simulates data processing and writes Prometheus-compatible metrics
- A Prometheus Node Exporter collecting those metrics via the textfile collector
- A Grafana dashboard visualizing disk I/O, memory usage, CPU usage and ETL execution status

## Project Structure

```
Module3/
├── etl/
│   └── etl.py               # The ETL script
└── .github/
    └── workflows/
        └── deploy.yml       # GitHub Actions CI/CD pipeline 
```

## Part 1 — The ETL Script (`etl.py`)

### Section 1 — Imports & Constants

```python
import json
import time
from datetime import datetime

METRICS_FILE = (
    "/var/lib/node_exporter/textfile_collector/etl.prom"
)
```

I import `json` for writing the output file, `time` for tracking how long the ETL takes, and `datetime` for timestamping the output. The `METRICS_FILE` constant points to the Node Exporter's textfile collector directory.

### Section 2 — `write_metric()`: Exposing Metrics to Prometheus

```python
def write_metric(success, duration):
    timestamp = int(time.time())

    metrics = f"""
# HELP etl_success ETL execution success status
# TYPE etl_success gauge
etl_success {1 if success else 0}

# HELP etl_duration_seconds ETL execution duration
# TYPE etl_duration_seconds gauge
etl_duration_seconds {duration:.2f}

# HELP etl_last_run_timestamp Last ETL run timestamp
# TYPE etl_last_run_timestamp gauge
etl_last_run_timestamp {timestamp}
"""
    with open(METRICS_FILE, "w") as file:
        file.write(metrics)
```

This function writes three metrics in the Prometheus exposition format to the `.prom` file:

| Metric | Type | Description |
|---|---|---|
| `etl_success` | Gauge | `1` if the ETL succeeded, `0` if it failed |
| `etl_duration_seconds` | Gauge | How long the ETL took to run in seconds |
| `etl_last_run_timestamp` | Gauge | Unix timestamp of the last run |

### Section 3 — `run()`: The ETL Logic

```python
def run():
    print("ETL started")
    start_time = time.time()
    success = False

    try:
        time.sleep(2)

        data = {
            "status": "success",
            "records": 101
        }

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"/tmp/etl_output_{timestamp}.json"

        with open(filename, "w") as file:
            json.dump(data, file)

        success = True

    except Exception as error:
        print(f"ETL failed: {error}")

    duration = time.time() - start_time
    write_metric(success, duration)
    print(f"ETL finished in {duration:.2f} seconds")
```


1. **Start the timer** — I capture `start_time` before anything runs so I get an accurate duration measurement including the simulated workload.
2. **Simulate processing** — `time.sleep(2)` stands in for a real data pipeline. In a real ETL this would be database queries, API calls, data transformations, etc.
3. **Write the output** — I dump a JSON file to `/tmp/` with a timestamped filename so each run produces a unique output file and nothing gets overwritten.
4. **Handle failures** — the whole ETL body is wrapped in a `try/except`. If anything throws, `success` stays `False` and the error gets printed.`write_metric()` is always called even on failure, so Prometheus doesn't go stale.
5. **Compute duration & write metrics** — after the try/except block, I calculate the total duration and call `write_metric()`.


## Part 2 — CI/CD Pipeline (`deploy.yml`)

I set up GitHub Actions to trigger on any push to `main` that touches files inside `Module3/`. The pipeline has two jobs:

### Job 1 — Lint

```yaml
- name: run linter
  run: flake8 Module3/etl/etl.py
```

Before anything gets deployed, I run `flake8` on the ETL script to catch syntax errors and style violations.
### Job 2 — Deploy (runs only if lint passes)

```yaml
needs: lint
```

The deploy job only runs if lint succeeds. It SSHs into my Linux server using credentials stored as GitHub Secrets and either clones the repo fresh or pulls the latest changes, then runs the ETL script:

```bash
python3 Module3/etl/etl.py
```

The `set -e` at the top of the script makes the SSH session exit immediately on any error.
**Secrets used:**

| Secret | Purpose |
|---|---|
| `LINUX_HOST` | IP of the target server |
| `LINUX_USER` | SSH username |
| `LINUX_SSH_KEY` | Private key for passwordless SSH auth |


## Part 3 — Monitoring Setup

### Prometheus Node Exporter

I installed Node Exporter on the Linux server and enabled the textfile collector by pointing it at the directory where `etl.py` writes its `.prom` file:

```bash
--collector.textfile.directory=/var/lib/node_exporter/textfile_collector/
```

Prometheus scrapes the Node Exporter on its configured interval and picks up both the standard system metrics (CPU, memory, disk I/O) and the custom ETL metrics automatically.

### Grafana Dashboard

I connected Grafana to my Prometheus instance and built a dashboard with panels for:

- **Disk I/O** — using the standard Node Exporter `node_disk_*` metrics to track read/write throughput
- **ETL Success Status** — `etl_success` shown as a stat panel; green for `1`, red for `0`
- **ETL Duration** — `etl_duration_seconds` as a time series so I can spot if runs are getting slower over time
- **Last Run Timestamp** — `etl_last_run_timestamp` converted to a human-readable time to confirm the script is actually being triggered

### Dashboard Screenshot

![screenshot](./grafana_dashboard.png)


- Keeping CI/CD paths relative to the **repo root** is crucial when your workflow file lives at the root but your code is in a subdirectory
- The Prometheus textfile collector is the simplest way to expose custom metrics from a script without running a full metrics server
- Separating lint and deploy into two jobs makes the pipeline easier to debug — you know exactly which stage failed


# Issues faced

- I tested the CI/CD pipline with a test github repo separately so .github/workflows/deploy.yml was under Module3. When I tested the pipeline from the root project folder the path to the etl script in deploy.yml got broken. I checked the github actions error to fix it.

- I faced a permission issue when trying to write to `/var/lib/node_exporter/textfile_collector/`. I fixed this by changing ownership of the textfile collector directory:

```bash
sudo chown -R ubuntu:ubuntu /var/lib/node_exporter/textfile_collector
```

