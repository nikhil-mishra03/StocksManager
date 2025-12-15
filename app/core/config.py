from pydantic_settings import BaseSettings, SettingsConfigDict

class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=False,
    )

    application_mode: str = "mock"
    postgres_host: str
    postgres_port: int
    postgres_user: str
    postgres_password: str
    database_name: str
    kite_api_key: str
    kite_api_secret: str
    kite_request_token: str
    kite_url: str
    kite_access_token: str
    alphavantage_api_key: str
    alphavantage_base_url: str

def get_config() -> Config:
    return Config()
