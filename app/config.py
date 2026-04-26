from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    hf_token: str = ""
    host: str = "0.0.0.0"
    port: int = 8000
    vton_space_id: str = "yisol/IDM-VTON"
    api_timeout: int = 120

    class Config:
        env_file = ".env"

settings = Settings()

# Token configured -> Force reload!
