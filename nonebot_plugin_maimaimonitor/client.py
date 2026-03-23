# ============================================================
# WARNING: DO NOT MODIFY THIS FILE
# client.py 包含核心签名算法
# 任何改动都会导致已有用户密钥失效，与服务端验证不兼容
# 如需扩展功能请只添加新方法
# 不要修改 _calculate_hmac_sha256 / _generate_sha256_hash / send_report
# ============================================================

import hmac
import hashlib
import time
import json
import httpx
from typing import Optional, Union

class MaimaiReporter:
    def __init__(self, client_id: str, private_key: str, worker_url: str):
        self.client_id = client_id
        self.private_key = private_key
        self.worker_url = worker_url.rstrip('/')

    def _calculate_hmac_sha256(self, key: str, message: str) -> str:
        key_bytes = key.encode('utf-8')
        message_bytes = message.encode('utf-8')
        hmac_obj = hmac.new(key_bytes, message_bytes, hashlib.sha256)
        return hmac_obj.hexdigest()

    def _generate_sha256_hash(self, data: str) -> str:
        return hashlib.sha256(data.encode('utf-8')).hexdigest()

    async def send_report(self, report_data: Union[dict, list], custom_display_name: str = None) -> httpx.Response:
        timestamp = str(int(time.time() * 1000))

        report_data_list = [report_data] if not isinstance(report_data, list) else report_data
        
        final_report_data_list = []
        for item in report_data_list:
            item_copy = item.copy()
            if custom_display_name:
                item_copy['bot_display_name'] = custom_display_name
            final_report_data_list.append(item_copy)
        
        raw_request_body = json.dumps(final_report_data_list, ensure_ascii=False)

        body_hash_hex = self._generate_sha256_hash(raw_request_body)
        string_to_sign = f"POST:/bot-post:{self.client_id}:{timestamp}:{body_hash_hex}"
        signature = self._calculate_hmac_sha256(self.private_key, string_to_sign)

        headers = {
            "Content-Type": "application/json",
            "X-Client-ID": self.client_id,
            "X-Timestamp": timestamp,
            "X-Signature": signature
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(f"{self.worker_url}/bot-post", headers=headers, data=raw_request_body.encode('utf-8'))
            response.raise_for_status()
            return response

    async def fetch_status(self) -> Optional[dict]:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get("https://mai.chongxi.us/api/bot")
                if response.status_code == 200:
                    return response.json()
        except Exception:
            pass
        return None
