import csv
import json
import os
import time
from pathlib import Path
from kafka import KafkaProducer


def main():
    producer = KafkaProducer(
        bootstrap_servers=os.getenv("KAFKA_SERVERS", "kafka:9092"),
        acks="all",
        value_serializer=lambda value: json.dumps(value, ensure_ascii=False).encode("utf-8"),
        key_serializer=lambda value: value.encode("utf-8"),
    )
    count = 0
    for path in sorted(Path("data").glob("*.csv")):
        with path.open(encoding="utf-8", newline="") as source:
            for row in csv.DictReader(source):
                # ID в разных файлах совпадают, поэтому добавляем имя файла.
                row["source_file"] = path.name
                row["sale_key"] = f"{path.name}:{row['id']}"
                producer.send("sales", key=row["sale_key"], value=row).get(timeout=30)
                count += 1
                time.sleep(float(os.getenv("SEND_DELAY", "0.01")))
    producer.flush()
    producer.close()
    print(f"Отправлено сообщений: {count}")


if __name__ == "__main__":
    main()
