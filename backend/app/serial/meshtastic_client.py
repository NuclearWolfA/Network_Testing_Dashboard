from datetime import datetime

from pubsub import pub
import meshtastic
import meshtastic.serial_interface
from app.db.session import SessionLocal
from app.models.entities import Message

from app.generated import sdn_pb2, aodv_pb2, portnums_pb2

def get_meshtastic_ports():
    ports: meshtastic.serial_interface.List[str] = meshtastic.util.findPorts(True)
    return ports

def on_receive(packet, interface):
    print(f"Received packet on {interface.myInfo.my_node_num}: {packet}")
    need_to_upload = True
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
        if packet["decoded"].get("requestId"):
            message.request_id = packet["decoded"]["requestId"]
        if packet["decoded"].get('routing'):
            ack_info = packet["decoded"]['routing']
            if ack_info.get('errorReason'):
                if ack_info['errorReason'] == 'NONE':
                    message.message_type = "ACK"
                else:
                    message.message_type = "NACK"
        if packet["decoded"].get("portnum"):
            message.portnum = packet["decoded"]["portnum"]
            #print(f"Received message on port {message.portnum}")
            #print(f"Type of the portnum: {type(message.portnum)}")
            if message.portnum == "TELEMETRY_APP" or message.portnum == "SIMULATOR_APP":
                need_to_upload = False
            elif message.portnum == 78: # SDN messages
                payload = packet["decoded"].get('payload', None)
                try:
                    sdn_message = sdn_pb2.SDN()
                    sdn_message.ParseFromString(payload)
                    if sdn_message.HasField("announcement"):
                        message.message_type = "ANNOUNCEMENT"
                    elif sdn_message.HasField("route_update"):
                        message.message_type = "ROUTE_UPDATE"
                    elif sdn_message.HasField("route_command"):
                        message.message_type = "ROUTE_COMMAND"
                    elif sdn_message.HasField("route_install"):
                        message.message_type = "ROUTE_INSTALL"
                    elif sdn_message.HasField("route_set"):
                        message.message_type = "ROUTE_SET"
                    elif sdn_message.HasField("route_set_confirm"):
                        message.message_type = "ROUTE_SET_CONFIRM"
                    elif sdn_message.HasField("link_quality"):
                        message.message_type = "LINK_QUALITY"
                    else:
                        message.message_type = "UNKNOWN_SDN_MESSAGE"
                except Exception as e:
                    print(f"Error parsing SDN message: {e}")
            
            elif message.portnum == 75:
                payload = packet["decoded"].get('payload', None)
                try:
                    aodv_message = aodv_pb2.AODV()
                    aodv_message.ParseFromString(payload)
                    if aodv_message.HasField("rreq"):
                        message.message_type = "RREQ"
                    elif aodv_message.HasField("rrep"):
                        message.message_type = "RREP"
                    elif aodv_message.HasField("rerr"):
                        message.message_type = "RERR"
                    elif aodv_message.HasField("rrep_ack"):
                        message.message_type = "RREP_ACK"
                    else:
                        message.message_type = "UNKNOWN_AODV_MESSAGE"
                except Exception as e:
                    print(f"Error parsing AODV message: {e}")


    if packet.get("nextHop"):
        message.next_hop = f"0x{int(packet['nextHop']):x}"
    if packet.get("relayNode"):
        message.relay_node = f"0x{int(packet['relayNode']):x}"
    if need_to_upload:
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