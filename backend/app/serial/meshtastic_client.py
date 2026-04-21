from datetime import datetime

from pubsub import pub
import meshtastic
import meshtastic.serial_interface
from app.db.session import SessionLocal
from app.models.entities import Message


def get_meshtastic_ports():
    ports: meshtastic.serial_interface.List[str] = meshtastic.util.findPorts(True)
    return ports

def on_receive(packet, interface):
    print(f"Received packet on {interface.myInfo.my_node_num}: {packet}")
    need_to_udload = True
    message = Message(
        source=f"0x{int(packet['from']):x}",
        destination=f"0x{int(packet['to']):x}",
        reporter=f"0x{int(interface.myInfo.my_node_num):x}",
        timestamp = datetime.now().astimezone(),
        sequence_number=packet["id"],
    )
    #print(f"[Debug] Timestamp: {message.timestamp}")
    if packet.get("decoded"):
        if packet["decoded"].get("payload"):
            message.payload = packet["decoded"]["payload"]
        if packet["decoded"].get("portnum"):
            message.portnum = packet["decoded"]["portnum"]
            if message.portnum == "TELEMETRY_APP":
                need_to_udload = False
    if packet.get("nextHop"):
        message.next_hop = f"0x{int(packet['nextHop']):x}"
    if need_to_udload:
        session = SessionLocal()
        try:
            session.add(message)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

def start_meshtastic_client(app):
    print("Starting meshtastic client...")
    pub.subscribe(on_receive, "meshtastic.receive")
    ports = get_meshtastic_ports()
    if len(ports) == 0:
        raise RuntimeError("No meshtastic devices found")
        return
    app.state.comport_intereface_dic = {}
    app.state.node_id_interface_dic = {}
    for port in ports:
        try:
            interface = meshtastic.serial_interface.SerialInterface(port)
            app.state.comport_intereface_dic[port] = interface
            app.state.comport_intereface_dic[port].app = app
            app.state.node_id_interface_dic[f"0x{int(interface.myInfo.my_node_num):x}"] = interface
            print(f"Connected to meshtastic device on port {port}")
            
        except Exception as e:
            print(f"Error connecting to meshtastic device on port {port}: {e}")

def send_meshtastic_message(app,interface,destination,payload):
    try:
        sent_message = interface.sendText(payload, destinationId=destination, wantAck=True)
        source_id = f"0x{int(interface.myInfo.my_node_num):x}"
        message = Message(
            source=source_id,
            destination=destination,
            reporter=source_id,
            timestamp = datetime.now().astimezone(),
            sequence_number=sent_message.id,
            payload=payload,
        )
        print(f"Sent message: {message}")
        session = SessionLocal()
        try:
            session.add(message)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
        print(f"Sent message from {source_id} to {destination} with sequence number {sent_message.id}")
        return sent_message.id
    except Exception as e:
        print(f"Error sending or updating database for meshtastic message: {e}")
    return None