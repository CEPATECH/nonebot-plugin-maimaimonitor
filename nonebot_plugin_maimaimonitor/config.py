from pydantic import BaseModel
from typing import Optional

class Config(BaseModel):
    maimai_bot_client_id: Optional[str] = None
    maimai_bot_private_key: Optional[str] = None
    maimai_bot_display_name: str = "qwq"
    maimai_worker_url: str = "https://maiapi.chongxi.us"
    maimai_broadcast_group_ids: list[int] = []
    maimai_broadcast_interval: int = 300
