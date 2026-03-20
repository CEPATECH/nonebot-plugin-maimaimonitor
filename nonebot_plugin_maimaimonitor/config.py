from pydantic import BaseModel, Field
from typing import Dict, Optional

class Config(BaseModel):
    maimai_bot_client_id: Optional[str] = Field(default=None)
    maimai_bot_private_key: Optional[str] = None
    maimai_bot_display_name: Optional[str] = None

    maimai_worker_url: str = "https://maiapi.chongxi.us"
    maimai_command_aliases: Dict[str, str] = {}
