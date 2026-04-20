from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Network Testing Dashboard API"
    api_prefix: str = "/api"
    database_url: str

    mqtt_host: str = "localhost"
    mqtt_port: int = 1883
    mqtt_topic: str = "meshtastic/#"
    mqtt_client_id: str = "network-testing-dashboard"


settings = Settings()
