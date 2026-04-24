from datetime import datetime

from pubsub import pub
import meshtastic
import meshtastic.serial_interface
from app.db.session import SessionLocal
from app.models.entities import Message, Node
from app.core.config import settings

from app.generated import sdn_pb2, aodv_pb2, portnums_pb2

def get_meshtastic_ports():
    ports: meshtastic.serial_interface.List[str] = meshtastic.util.findPorts(True)
    return ports

def get_portnum_value(portnum):
    if isinstance(portnum, int):
        return portnum
    if isinstance(portnum, str):
        try:
            return int(portnum)
        except ValueError:
            return getattr(portnums_pb2.PortNum, portnum, None)
    return None

def on_receive(packet, interface):
    timestamp = datetime.now().astimezone()
    print(f"Received packet on {interface.myInfo.my_node_num}: {packet}")
    need_to_upload = True
    message = Message(
        source=f"0x{int(packet['from']):x}",
        destination=f"0x{int(packet['to']):x}",
        reporter=f"0x{int(interface.myInfo.my_node_num):x}",
        timestamp = timestamp,
        sequence_number=packet["id"],
    )
    #print(f"[Debug] Timestamp: {message.timestamp}")
    if packet.get("encrypted"):
        message.message_type = "FORWARDED MESSAGE"
    if packet.get("hopStart") and packet.get("hopLimit"):
        message.hops_away = packet["hopStart"] - packet["hopLimit"]
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
            portnum_value = get_portnum_value(message.portnum)
            #print(f"Received message on port {message.portnum}")
            #print(f"Type of the portnum: {type(message.portnum)}")
            if portnum_value in (portnums_pb2.PortNum.TELEMETRY_APP, portnums_pb2.PortNum.SIMULATOR_APP):
                need_to_upload = False
            elif portnum_value == portnums_pb2.PortNum.SDN_APP:
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
            
            elif portnum_value == portnums_pb2.PortNum.AODV_ROUTING_APP:
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
                    elif "rrep_ack" in aodv_message.DESCRIPTOR.fields_by_name and aodv_message.HasField("rrep_ack"):
                        message.message_type = "RREP_ACK"
                    elif aodv_message.HasField("rt_request"):
                        message.message_type = "ROUTE_TABLE_REQUEST"
                    elif aodv_message.HasField("rt_response"):
                        message.message_type = "ROUTE_TABLE_RESPONSE"
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
        print("No meshtastic devices found; skipping Meshtastic startup.")
        return
    app.state.comport_intereface_dic = {}
    app.state.node_id_interface_dic = {}
    for port in ports:
        try:
            interface = meshtastic.serial_interface.SerialInterface(port)
            app.state.comport_intereface_dic[port] = interface
            app.state.comport_intereface_dic[port].app = app
            app.state.node_id_interface_dic[f"0x{int(interface.myInfo.my_node_num):x}"] = interface
            upsert_node(f"0x{int(interface.myInfo.my_node_num):x}")
            print(f"Connected to meshtastic device on port {port}")
            
        except Exception as e:
            print(f"Error connecting to meshtastic device on port {port}: {e}")

def send_meshtastic_message(app,interface,destination,payload):
    try:
        destination_int = int(destination[2:], 16)
        timestamp = datetime.now().astimezone()
        sent_message = interface.sendText(payload, destinationId=destination_int, wantAck=True)
        source_id = f"0x{int(interface.myInfo.my_node_num):x}"
        message = Message(
            source=source_id,
            destination=destination,
            reporter=source_id,
            timestamp = timestamp,
            sequence_number=sent_message.id,
            payload=payload,
            portnum = "TEXT_MESSAGE_APP"
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

def upsert_node(node_id: str):
    session = SessionLocal()
    backend_id = settings.backend_id
    last_byte = node_id[-2:]
    if last_byte == "00":
        last_byte = "ff"
    try:
        node = session.query(Node).filter(Node.node_id == node_id).one_or_none()
        if node is None:
            node = Node(node_id=node_id, backend_id=backend_id, last_byte=last_byte)
            session.add(node)
        else:
            node.backend_id = backend_id
            node.last_byte = last_byte
        session.commit()
        session.refresh(node)
        return node
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
