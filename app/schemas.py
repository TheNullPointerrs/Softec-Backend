# app/schemas.py
from pydantic import BaseModel

class TextInput(BaseModel):
    text: str
