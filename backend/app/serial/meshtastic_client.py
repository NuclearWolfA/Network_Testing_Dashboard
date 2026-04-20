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
    message = Message(
        source=f"0x{int(packet['from']):x}",
        destination=f"0x{int(packet['to']):x}",
        reporter=f"0x{int(interface.myInfo.my_node_num):x}",
        timestamp = datetime.now(),
        sequence_number=packet["id"],
    )
    if packet.get("decoded"):
        if packet["decoded"].get("payload"):
            message.payload = packet["decoded"]["payload"]
        if packet["decoded"].get("portnum"):
            message.portnum = packet["decoded"]["portnum"]
    if packet.get("nextHop"):
        message.next_hop = f"0x{int(packet['nextHop']):x}"
    session = SessionLocal()
    session.add(message)
    session.commit()
    session.close()

def start_meshtastic_client(app):
    print("Starting meshtastic client...")
    pub.subscribe(on_receive, "meshtastic.receive")
    ports = get_meshtastic_ports()
    if len(ports) == 0:
        raise RuntimeError("No meshtastic devices found")
        return
    app.state.comport_intereface_dic = {}
    for port in ports:
        try:
            app.state.comport_intereface_dic[port] = meshtastic.serial_interface.SerialInterface(port)
            app.state.comport_intereface_dic[port].app = app
            print(f"Connected to meshtastic device on port {port}")
            
        except Exception as e:
            print(f"Error connecting to meshtastic device on port {port}: {e}")