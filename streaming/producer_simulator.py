
import json
import random
import time
import uuid
from datetime import datetime, timezone

from kafka import KafkaProducer

producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    value_serializer=lambda value: json.dumps(value).encode("utf-8")
)

print("Producer connected", flush=True)

topic = "taxi-events"
zones = ["Manhattan", "Brooklyn", "Queens", "Bronx"]

try:
    while True:
        print("Generating event...", flush=True)

        event = {
            "event_id": str(uuid.uuid4()),
            "event_time": datetime.now(timezone.utc).isoformat(),
            "pickup_zone": random.choice(zones),
            "dropoff_zone": random.choice(zones),
            "distance_km": round(random.uniform(1, 25), 2),
            "fare_amount": round(random.uniform(5, 80), 2)
        }

        print("Sending event...", flush=True)
        future = producer.send(topic, value=event)
        future.get(timeout=10)

        print(f"Sent: {json.dumps(event)}", flush=True)
        time.sleep(2)
except KeyboardInterrupt:
    print("Simulator stopped.")

finally:
    producer.close()
