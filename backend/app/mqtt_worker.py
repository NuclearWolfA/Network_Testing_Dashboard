import paho.mqtt.client as mqtt

from app.core.config import settings
from app.db.session import SessionLocal
from app.services.ingestion import persist_mqtt_message


def on_connect(client: mqtt.Client, userdata, flags, rc, properties=None):
    client.subscribe(settings.mqtt_topic)


def on_message(client: mqtt.Client, userdata, message: mqtt.MQTTMessage):
    db = SessionLocal()
    try:
        persist_mqtt_message(
            db=db,
            topic=message.topic,
            qos=int(message.qos),
            retain=bool(message.retain),
            payload_raw=bytes(message.payload),
            connection_id=settings.mqtt_client_id,
            meta={"properties": str(getattr(message, "properties", None))},
        )
    except Exception as exc:
        print(f"mqtt_ingest_failed: {exc}")
        db.rollback()
    finally:
        db.close()


def run() -> None:
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=settings.mqtt_client_id)
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(settings.mqtt_host, settings.mqtt_port, 60)
    client.loop_forever()


if __name__ == "__main__":
    run()
