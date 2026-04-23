# encoding: utf-8
import os

API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
