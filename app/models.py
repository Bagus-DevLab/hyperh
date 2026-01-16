from pydantic import BaseModel

class ControlRequest(BaseModel):
    action: str  # Hanya menerima string "ON" atau "OFF"