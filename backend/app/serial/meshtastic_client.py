from pubsub import pub
import meshtastic
import meshtastic.serial_interface

def get_meshtastic_ports():
    ports: meshtastic.serial_interface.List[str] = meshtastic.util.findPorts(True)
    return ports

def on_receive(packet, interface):
    print(f"Received packet on {interface.port}: {packet}")

def start_meshtastic_client(app):
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