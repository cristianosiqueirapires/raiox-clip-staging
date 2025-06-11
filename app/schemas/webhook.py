from pydantic import BaseModel
from typing import Optional

class WebhookRequest(BaseModel):
    image_url: str
    client_id: str
    metadata: Optional[dict] = None
