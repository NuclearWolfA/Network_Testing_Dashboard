import paho.mqtt.client as mqtt
from functools import partial
import json

from app.core.config import settings
from app.serial.meshtastic_client import send_meshtastic_message


def on_connect(client: mqtt.Client, userdata, flags, rc, properties=None, *, app):
    interfaces_dic = getattr(app.state, "node_id_interface_dic", {})
    for node_id, interface in interfaces_dic.items():
        topic = f"{settings.mqtt_topic}/{node_id}"
        client.subscribe(topic)
        print(f"Subscribed to MQTT topic: {topic}")


def on_message(client: mqtt.Client, userdata, message: mqtt.MQTTMessage, *, app):
    print(f"Received MQTT message on topic {message.topic} with QoS {message.qos} : {message.payload}")

    source = message.topic.split("/")[-1]
    interfaces_dic = getattr(app.state, "node_id_interface_dic", {})
    interface = interfaces_dic.get(source)
    if interface is None:
        print(f"No interface found for source {source}; cannot send message.")
        return

    try:
        payload_text = message.payload.decode("utf-8")
        message_data = json.loads(payload_text)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        print(f"Invalid MQTT payload format for topic {message.topic}: {exc}")
        return

    if not isinstance(message_data, dict):
        print(f"Invalid MQTT payload type for topic {message.topic}; expected JSON object.")
        return

    destination = message_data.get("destination")
    if not destination:
        print("No destination found in MQTT message; cannot send message.")
        return

    payload = message_data.get("payload")
    if payload is None:
        print("No payload found in MQTT message; cannot send message.")
        return

    try:
        send_meshtastic_message(app, interface, destination, str(payload))
    except Exception as exc:
        print(f"Failed to forward MQTT message to Meshtastic: {exc}")


def publish_mqtt_message(source: str, destination: str, payload: str) -> bool:
    if not source:
        raise ValueError("source is required")
    if not destination:
        raise ValueError("destination is required")
    if payload is None:
        raise ValueError("payload is required")

    topic = f"{settings.mqtt_topic}/{source}"
    message_body = json.dumps(
        {
            "source": source,
            "destination": destination,
            "payload": payload,
        }
    )

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=settings.mqtt_client_id)
    try:
        client.connect(settings.mqtt_host, settings.mqtt_port, 60)
        client.loop_start()
        publish_result = client.publish(topic, message_body, qos=0, retain=False)
        publish_result.wait_for_publish()
        if publish_result.rc != mqtt.MQTT_ERR_SUCCESS:
            raise RuntimeError(f"MQTT publish failed with code {publish_result.rc}")
        print(f"Published MQTT message to topic {topic}: {message_body}")
        return True
    except OSError as exc:
        print(f"MQTT publish failed: {exc}")
        return False
    finally:
        try:
            client.loop_stop()
        except Exception:
            pass
        try:
            client.disconnect()
        except Exception:
            pass

def mqtt_startup(app) -> None:

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=settings.mqtt_client_id)
    client.on_connect = partial(on_connect, app=app)
    client.on_message = partial(on_message, app=app)

    try:
        client.connect(settings.mqtt_host, settings.mqtt_port, 60)
    except OSError as exc:
        print(
            f"MQTT broker unavailable at {settings.mqtt_host}:{settings.mqtt_port}; "
            "skipping MQTT startup."
        )
        print(f"MQTT startup error: {exc}")
        return
    print(f"Connected to MQTT broker at {settings.mqtt_host}:{settings.mqtt_port}")
    client.loop_forever()
