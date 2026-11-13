import argparse
import json
import subprocess
import time
import urllib.request


def get(path):
    with urllib.request.urlopen("http://localhost:8082/nifi-api" + path, timeout=15) as response:
        return json.load(response)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-input", type=int, default=10000)
    args = parser.parse_args()
    root = get("/flow/process-groups/root")["processGroupFlow"]
    group = next(item["id"] for item in root["flow"]["processGroups"]
                 if item["component"]["name"] == "sales_pipeline")
    for attempt in range(120):
        result = subprocess.run([
            "docker", "compose", "exec", "-T", "-e", "KAFKA_HEAP_OPTS=-Xms64m -Xmx256m", "kafka", "kafka-consumer-groups",
            "--bootstrap-server", "kafka:9092", "--describe", "--group", "nifi-sales",
        ], capture_output=True, text=True, timeout=30)
        if result.returncode:
            raise RuntimeError(f"Kafka CLI failed ({result.returncode}): {result.stdout} {result.stderr}")
        rows = [line.split() for line in result.stdout.splitlines() if line.split() and line.split()[0] == "nifi-sales"]
        status = get(f"/flow/process-groups/{group}/status")["processGroupStatus"]["aggregateSnapshot"]
        delivered = bool(rows) and all(row[3].isdigit() and row[4].isdigit() and row[3] == row[4] for row in rows)
        end_offset = sum(int(row[4]) for row in rows if row[4].isdigit())
        print(f"Kafka offsets: {[(row[3], row[4], row[5]) for row in rows]}; queued: {status['queuedCount']}", flush=True)
        if not rows:
            print(result.stdout + result.stderr, flush=True)
        if delivered and end_offset == args.expected_input and int(str(status["queuedCount"]).replace(",", "")) == 0:
            print(f"Kafka offset {end_offset}, NiFi queues are empty")
            return
        time.sleep(5)
    raise RuntimeError("Kafka or NiFi queues did not drain within 10 minutes")


if __name__ == "__main__":
    main()
