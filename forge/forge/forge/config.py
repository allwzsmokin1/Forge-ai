from pydantic import BaseModel

class Settings(BaseModel):
    app_name: str = "ForgeAI"
    version: str = "0.0.1"

settings = Settings()
