from fastapi import FastAPI

from app.api.analyze_api import router as analyze_router
from app.api.routes import router
from app.core.config import settings
from app.db.session import SessionLocal
from app.services.backend_registry import upsert_backend_instance


app = FastAPI(title=settings.app_name)


app.include_router(router, prefix=settings.api_prefix)
app.include_router(analyze_router, prefix=settings.api_prefix)

@app.on_event("startup")
def startup_event():
    session = SessionLocal()
    try:
        upsert_backend_instance(session)
    finally:
        session.close()

    from app.serial.meshtastic_client import start_meshtastic_client
    try:
        start_meshtastic_client(app)
    except Exception as e:
        print(f"Error starting meshtastic client: {e}")