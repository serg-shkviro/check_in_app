import os

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    JWT_SECRET: str = os.environ.get('JWT_SECRET', '')

CheckinSettings = Settings()