from fastapi import APIRouter, Request

from app.serial.meshtastic_client import send_meshtastic_message


router = APIRouter()


@router.get("/dummy")
def dummy_api() -> dict[str, str]:
    return {"message": "dummy backend api"}

@router.post("/send")
async def send_text(request: Request, source: str, destination: str, payload: str):
    print(f"Received send request: source={source}, destination={destination}, payload={payload}")
    # Here you can add code to send the message using the meshtastic client
    interface = request.app.state.node_id_interface_dic.get(source)
    if not interface:
        return {"error": "Source node not found"}
    seq_no = send_meshtastic_message(request.app, interface, destination, payload)

    return {"message": "Message sent successfully", "sequence_number": seq_no}