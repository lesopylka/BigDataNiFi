import json
import time
from pathlib import Path
import requests


BASE = "http://nifi:8080/nifi-api"
SESSION = requests.Session()


def api(method, path, payload=None):
    response = SESSION.request(method, BASE + path, json=payload, timeout=60)
    response.raise_for_status()
    return response.json() if response.content else {}


def configure(kind, entity, settings):
    # Имена свойств берем из API установленной версии NiFi.
    item = api("GET", f"/{kind}/{entity['id']}")
    descriptors = item["component"]["descriptors"]
    properties = {}
    for label, value in settings.items():
        matches = [key for key, description in descriptors.items()
                   if key == label or description.get("displayName") == label]
        if len(matches) != 1:
            raise ValueError(f"Не найдено свойство {label}: {list(descriptors)}")
        properties[matches[0]] = value
    component = {"id": entity["id"]}
    if kind == "processors":
        component["config"] = {"properties": properties}
    else:
        component["properties"] = properties
    return api("PUT", f"/{kind}/{entity['id']}", {"revision": item["revision"], "component": component})


def change_state(kind, entity, state):
    current = api("GET", f"/{kind}/{entity['id']}")
    return api("PUT", f"/{kind}/{entity['id']}/run-status", {
        "revision": current["revision"], "state": state,
    })


def main():
    for attempt in range(120):
        try:
            root = api("GET", "/flow/process-groups/root")["processGroupFlow"]["id"]
            break
        except (requests.RequestException, KeyError):
            time.sleep(5)
    else:
        raise RuntimeError("NiFi не запустился за 10 минут")
    existing = api("GET", f"/flow/process-groups/{root}")["processGroupFlow"]["flow"]["processGroups"]
    if any(group["component"]["name"] == "sales_pipeline" for group in existing):
        raise RuntimeError("sales_pipeline уже существует. Проверь поток в UI, повторно создавать его не нужно")
    group = api("POST", f"/process-groups/{root}/process-groups", {
        "revision": {"version": 0}, "component": {"name": "sales_pipeline", "position": {"x": 0, "y": 0}},
    })["id"]
    processor_types = api("GET", "/flow/processor-types")["processorTypes"]
    service_types = api("GET", "/flow/controller-service-types")["controllerServiceTypes"]

    def create(name, kind, x=0):
        types = processor_types if kind == "processors" else service_types
        descriptor = next(item for item in types if item["type"].split(".")[-1] == name)
        component = {"type": descriptor["type"], "bundle": descriptor["bundle"], "name": name}
        if kind == "processors":
            component["position"] = {"x": x, "y": 0}
        return api("POST", f"/process-groups/{group}/{kind}", {"revision": {"version": 0}, "component": component})

    reader = create("JsonTreeReader", "controller-services")
    reader = configure("controller-services", reader, {"Schema Access Strategy": "infer-schema"})
    pool = create("DBCPConnectionPool", "controller-services")
    pool = configure("controller-services", pool, {
        "Database Connection URL": "jdbc:postgresql://postgres:5432/postgres",
        "Database Driver Class Name": "org.postgresql.Driver",
        "database-driver-locations": "/opt/nifi/drivers/postgresql.jar",
        "Database User": "postgres", "Password": "postgres",
    })
    for entity in [reader, pool]:
        change_state("controller-services", entity, "ENABLED")
    consume = create("ConsumeKafka_2_6", "processors")
    consume = configure("processors", consume, {
        "Kafka Brokers": "kafka:9092", "Topic Name(s)": "sales", "Group ID": "nifi-sales",
        "Offset Reset": "earliest",
    })
    save = create("PutDatabaseRecord", "processors", 500)
    save = configure("processors", save, {
        "Record Reader": reader["id"], "Database Connection Pooling Service": pool["id"],
        "Statement Type": "UPSERT", "Database Type": "PostgreSQL", "Schema Name": "public", "Table Name": "mock_data",
        "Update Keys": "sale_key", "Unmatched Field Behavior": "Fail on Unmatched Fields",
    })

    def connect(source, destination, relationship):
        return api("POST", f"/process-groups/{group}/connections", {
            "revision": {"version": 0}, "component": {
                "source": {"id": source["id"], "groupId": group, "type": "PROCESSOR"},
                "destination": {"id": destination["id"], "groupId": group, "type": "PROCESSOR"},
                "selectedRelationships": [relationship],
                "backPressureObjectThreshold": 10000, "backPressureDataSizeThreshold": "1 GB",
            },
        })

    connect(consume, save, "success")
    # Ошибки остаются в очереди, а не удаляются через auto-terminate.
    connect(save, save, "retry")
    failure = create("LogAttribute", "processors", 1000)
    connect(save, failure, "failure")
    for entity, relationships in [(save, ["success"]), (failure, [])]:
        current = api("GET", f"/processors/{entity['id']}")
        api("PUT", f"/processors/{entity['id']}", {
            "revision": current["revision"], "component": {"id": entity["id"], "config": {"autoTerminatedRelationships": relationships}},
        })
    # LogAttribute намеренно не запускается. Очередь failure служит карантином.
    for entity in [save, consume]:
        for attempt in range(30):
            status = api("GET", f"/processors/{entity['id']}")["component"]
            if status.get("validationStatus") == "VALID":
                break
            time.sleep(1)
        if status.get("validationStatus") != "VALID":
            raise RuntimeError(f"Невалидный процессор: {json.dumps(status.get('validationErrors'), ensure_ascii=False)}")
        change_state("processors", entity, "RUNNING")
    print(f"Поток создан. Process group: {group}")


if __name__ == "__main__":
    main()
