from enum import Enum
from pydantic import BaseModel
from typing import Optional

class Category(str, Enum):
    shirt = "shirt"
    pant = "pant"
    kurti = "kurti"
    lehenga = "lehenga"

class TryOnResponse(BaseModel):
    status: str
    message: str
    result_image_url: Optional[str] = None
    job_id: Optional[str] = None

class ErrorResponse(BaseModel):
    detail: str
