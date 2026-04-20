from fastapi import FastAPI

from app.api.routes import router
from app.core.config import settings


app = FastAPI(title=settings.app_name)


app.include_router(router, prefix=settings.api_prefix)

@app.on_event("startup")
def startup_event():
    from app.serial.meshtastic_client import start_meshtastic_client
    start_meshtastic_client(app)