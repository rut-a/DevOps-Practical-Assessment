import json
import time
from datetime import datetime

METRICS_FILE = (
    "/var/lib/node_exporter/textfile_collector/etl.prom"
)


def write_metric(success, duration):
    """Write ETL metrics for Prometheus Node Exporter."""
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


def run():
    """Run ETL process and generate monitoring metrics."""
    print("ETL started")

    start_time = time.time()
    success = False

    try:
        time.sleep(2)

        data = {
            "status": "success",
            "records": 100
        }

        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

        filename = (
            f"/tmp/etl_output_{timestamp}.json"
        )

        with open(filename, "w") as file:
            json.dump(data, file)

        success = True

    except Exception as error:
        print(f"ETL failed: {error}")

    duration = time.time() - start_time

    write_metric(success, duration)

    print(
        f"ETL finished in {duration:.2f} seconds"
    )


if __name__ == "__main__":
    run()

